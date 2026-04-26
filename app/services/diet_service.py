"""Diet Service — AI-powered personalized diet plan generation and editing."""

from __future__ import annotations

import copy
import json
import logging
import re
from datetime import date as date_type
from typing import Any, cast

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..config import settings
from ..constants import DietConstants
from ..core.custom_exceptions import DietNotFoundError, DietParsingError
from ..db.models import UserDiet, UserRoutine
from ..templates.diet import DIET_JSON_SCHEMA, DIET_SYSTEM_PROMPT
from .base_ai_generation_service import BaseAIGenerationService

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _build_diet_generation_prompt(
    intake: dict[str, Any],
    free_text: str,
    user_bio: dict[str, Any],
    routine_data: dict[str, Any] | None,
) -> str:
    """Build the complete nutritionist prompt for AI diet plan generation."""

    # User bio section
    bio_lines = []
    if user_bio.get("age"):
        bio_lines.append(f"- Edad: {user_bio['age']} años")
    if user_bio.get("gender"):
        gender_label = "Masculino" if user_bio["gender"] == "male" else "Femenino"
        bio_lines.append(f"- Sexo: {gender_label}")
    if user_bio.get("weight_kg"):
        bio_lines.append(f"- Peso: {user_bio['weight_kg']} kg")
    if user_bio.get("height_cm"):
        bio_lines.append(f"- Altura: {user_bio['height_cm']} cm")
    if user_bio.get("activity_level"):
        bio_lines.append(f"- Nivel de actividad (factor TDEE): {user_bio['activity_level']}")
    bio_section = "\n".join(bio_lines) if bio_lines else "- (No disponible)"

    # Nutrition targets section
    targets_lines = []
    if user_bio.get("target_calories"):
        targets_lines.append(f"- Calorías objetivo diarias: {round(user_bio['target_calories'])} kcal")
    if user_bio.get("protein_target_g"):
        targets_lines.append(f"- Proteína objetivo: {round(user_bio['protein_target_g'])} g/día")
    if user_bio.get("carbs_target_g"):
        targets_lines.append(f"- Carbohidratos objetivo: {round(user_bio['carbs_target_g'])} g/día")
    if user_bio.get("fat_target_g"):
        targets_lines.append(f"- Grasas objetivo: {round(user_bio['fat_target_g'])} g/día")
    if user_bio.get("objective"):
        obj_labels = {
            "fat_loss": "Pérdida de grasa",
            "muscle_gain": "Ganancia muscular",
            "body_recomp": "Recomposición corporal",
            "maintenance": "Mantenimiento",
            "performance": "Rendimiento deportivo",
        }
        targets_lines.append(f"- Objetivo fitness: {obj_labels.get(user_bio['objective'], user_bio['objective'])}")
    targets_section = "\n".join(targets_lines) if targets_lines else "- (Perfil nutricional no configurado — usar valores estándar saludables)"

    # Routine data section
    routine_section = "(Sin rutina activa — estimar calorías quemadas basado en el nivel de actividad)"
    if routine_data:
        sessions = routine_data.get("sessions", [])
        if sessions:
            avg_kcal = sum(s.get("estimated_calories_per_session", 0) for s in sessions) / len(sessions)
            session_titles = [s.get("title", "") for s in sessions[:3]]
            routine_section = (
                f"Rutina activa con {len(sessions)} sesiones de entrenamiento.\n"
                f"Calorías promedio por sesión: {round(avg_kcal)} kcal.\n"
                f"Tipos de sesión (muestra): {', '.join(session_titles)}.\n"
                f"Usar {round(avg_kcal)} kcal extras en los días de entrenamiento."
            )

    # Intake fields
    meals_count = intake.get("meals_count", 5)
    dietary_restrictions = intake.get("dietary_restrictions", "ninguna") or "ninguna"
    food_allergies = intake.get("food_allergies", "ninguna") or "ninguna"
    health_conditions = intake.get("health_conditions", "ninguna") or "ninguna"
    disliked_foods = intake.get("disliked_foods", "") or "Ninguno declarado"
    budget_level = intake.get("budget_level", "moderado")
    cooking_time = intake.get("cooking_time", "moderado")
    training_days: list[str] = intake.get("training_days") or []

    if training_days:
        training_days_section = f"DÍAS DE ENTRENAMIENTO: {', '.join(training_days)}"
    else:
        training_days_section = "DÍAS DE ENTRENAMIENTO: No especificados — training_day y rest_day deben ser idénticos en estructura"

    free_text_section = (
        f"\nINFORMACIÓN ADICIONAL DEL USUARIO:\n{free_text.strip()}"
        if free_text and free_text.strip()
        else ""
    )

    return f"""{DIET_SYSTEM_PROMPT}

---

DATOS DEL USUARIO:

DATOS BIOMÉTRICOS:
{bio_section}

OBJETIVOS NUTRICIONALES (del perfil):
{targets_section}

DATOS DE LA RUTINA DE ENTRENAMIENTO:
{routine_section}

RESTRICCIONES DIETÉTICAS: {dietary_restrictions}
ALERGIAS ALIMENTARIAS: {food_allergies}
CONDICIONES DE SALUD RELEVANTES: {health_conditions}
ALIMENTOS QUE NO LE GUSTAN: {disliked_foods}
CANTIDAD DE COMIDAS POR DÍA: {meals_count}
PRESUPUESTO: {budget_level}
TIEMPO DE COCCIÓN: {cooking_time}
{training_days_section}
{free_text_section}

---

TU TAREA:
1. Analizar PRIMERO todas las restricciones, alergias y condiciones de salud — ningún alimento prohibido puede aparecer
2. Calcular calorías para día de descanso (= target_calories del perfil) y día de entrenamiento (= target + kcal rutina)
3. Distribuir los macros objetivo exactamente en {meals_count} comidas por día
4. Diseñar comidas concretas con alimentos reales, porciones específicas y valores nutricionales precisos
5. Asegurar que los totales diarios coincidan con los objetivos (tolerancia ±5%)
6. Calcular el consumo de agua diario

{DIET_JSON_SCHEMA}"""


def _build_diet_edit_prompt(current_diet_data: dict[str, Any], edit_instruction: str) -> str:
    """Build the prompt for editing an existing diet plan."""
    return f"""{DIET_SYSTEM_PROMPT}

---

PLAN DE ALIMENTACIÓN ACTUAL (JSON):
{json.dumps(current_diet_data, ensure_ascii=False, indent=2)}

---

INSTRUCCIÓN DE MODIFICACIÓN DEL USUARIO:
"{edit_instruction}"

---

TU TAREA:
1. Analizar la instrucción de modificación
2. Aplicar los cambios respetando las restricciones alimentarias ya registradas en el plan actual
3. Mantener la estructura general del plan, modificando solo lo que se indica
4. Re-calcular totales calóricos y de macros si se agregan/eliminan alimentos
5. Asegurar que los totales diarios sigan coincidiendo con los objetivos

{DIET_JSON_SCHEMA}"""


def _render_meals(day: dict[str, Any]) -> str:
    """Render the meal cards for a given day (training or rest)."""
    meals_html = ""
    for meal in day.get("meals", []):
        foods_html = "".join(
            f"""<tr>
                    <td>{f['name']}</td>
                    <td>{f['portion']}</td>
                    <td style="text-align:right">{round(f['calories'])} kcal</td>
                    <td style="text-align:right">{round(f['protein_g'])}g</td>
                    <td style="text-align:right">{round(f['carbs_g'])}g</td>
                    <td style="text-align:right">{round(f['fat_g'])}g</td>
                </tr>"""
            for f in meal.get("foods", [])
        )
        meal_note = f"<p style='margin:4px 0 0 0;font-size:0.82em;opacity:0.75;font-style:italic'>{meal.get('notes','')}</p>" if meal.get("notes") else ""
        meals_html += f"""<div class="meal-card">
  <div class="meal-header">
    <span class="meal-name">{meal['name']}</span>
    <span class="meal-kcal">{round(meal['total_calories'])} kcal</span>
  </div>
  <table class="food-table">
    <thead><tr>
      <th>Alimento</th><th>Porción</th>
      <th style="text-align:right">Kcal</th>
      <th style="text-align:right">Prot</th>
      <th style="text-align:right">HC</th>
      <th style="text-align:right">Gras</th>
    </tr></thead>
    <tbody>{foods_html}</tbody>
  </table>
  {meal_note}
</div>"""
    return meals_html


def _render_day_section(day: dict[str, Any], emoji: str, title: str) -> str:
    """Render the full HTML section for a training or rest day."""
    meals_html = _render_meals(day)
    return f"""<div class="day-section">
  <p class="day-title">{emoji} {title}</p>
  <div class="day-totals">
    <div class="macro-pill">Calorías: <span>{round(day.get('total_calories', 0))} kcal</span></div>
    <div class="macro-pill">Proteína: <span>{round(day.get('total_protein_g', 0))}g</span></div>
    <div class="macro-pill">HC: <span>{round(day.get('total_carbs_g', 0))}g</span></div>
    <div class="macro-pill">Grasas: <span>{round(day.get('total_fat_g', 0))}g</span></div>
    <div class="water-pill">💧 {day.get('water_ml', 0)} ml agua</div>
  </div>
  {meals_html}
</div>"""


def _build_diet_notes_section(
    health_notes: list[str],
    supplement_suggestions: str,
    water_notes: str,
    nutritional_summary: str,
) -> str:
    """Render the recommendations/notes section at the bottom of the diet page."""
    health_notes_html = "".join(f"<li>{note}</li>" for note in health_notes)
    supplement_html = f"<p class='supplement'><strong>Suplementación:</strong> {supplement_suggestions}</p>" if supplement_suggestions else ""
    water_note_html = f"<p class='water-note'>{water_notes}</p>" if water_notes else ""
    return f"""<div class="notes-section">
  <p class="notes-title">📋 Recomendaciones</p>
  <ul>{health_notes_html}</ul>
  {supplement_html}
  {water_note_html}
  <p class="summary">{nutritional_summary}</p>
</div>"""


def _build_diet_stylesheet() -> str:
    """Return the <style> block for the diet HTML document."""
    return """<style>
  :root {
    --bg: #0d0d1a;
    --card: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.12);
    --accent: #00f2c3;
    --text: rgba(255,255,255,0.9);
    --muted: rgba(255,255,255,0.55);
  }
  [data-theme="original"] {
    --bg: #1a0a2e;
    --card: rgba(139,92,246,0.1);
    --border: rgba(139,92,246,0.25);
    --accent: #00f2c3;
    --text: #f0ede8;
    --muted: rgba(240,237,232,0.55);
  }
  html[data-theme="original"] { background: linear-gradient(135deg, #1a0a2e 0%, #2d1060 50%, #1a0a2e 100%); }
  [data-theme="light"] {
    --bg: #e8f8fa;
    --card: rgba(255,255,255,0.75);
    --border: rgba(0,0,0,0.12);
    --accent: #00c8d8;
    --text: #0a1a1e;
    --muted: rgba(10,26,30,0.6);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 1rem; max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.5rem; color: var(--accent); margin-bottom: 0.25rem; }
  .objective { font-size: 0.85rem; color: var(--muted); margin-bottom: 0.75rem; }
  .description { font-size: 0.9rem; line-height: 1.6; margin-bottom: 1.5rem; color: var(--muted); }
  .theme-btns { display:flex; gap:0.5rem; margin-bottom:1.5rem; flex-wrap:wrap; }
  .theme-btn { padding:0.4rem 0.9rem; border-radius:20px; border:1px solid var(--border); background:var(--card); color:var(--text); cursor:pointer; font-size:0.82rem; }
  .theme-btn.active { background:var(--accent); color:#0a1a1e; border-color:var(--accent); }
  .day-section { margin-bottom: 2rem; }
  .day-title { font-size: 1.1rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; padding-bottom: 0.3rem; border-bottom: 1px solid var(--border); }
  .day-totals { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
  .macro-pill { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 0.3rem 0.8rem; font-size: 0.8rem; }
  .macro-pill span { color: var(--accent); font-weight: 700; }
  .water-pill { background: rgba(0,180,255,0.15); border: 1px solid rgba(0,180,255,0.3); border-radius: 20px; padding: 0.3rem 0.8rem; font-size: 0.8rem; }
  .meal-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; }
  .meal-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; flex-wrap: wrap; }
  .meal-name { font-weight: 700; font-size: 0.95rem; flex: 1; }
  .meal-kcal { font-size: 0.85rem; color: var(--accent); font-weight: 600; margin-left: auto; }
  .food-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  .food-table th { text-align: left; color: var(--muted); font-weight: 600; padding: 0.2rem 0.3rem; border-bottom: 1px solid var(--border); }
  .food-table td { padding: 0.3rem 0.3rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .notes-section { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin-top: 1.5rem; }
  .notes-title { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; }
  .notes-section ul { padding-left: 1.2rem; }
  .notes-section li { font-size: 0.85rem; color: var(--muted); margin-bottom: 0.35rem; line-height: 1.5; }
  .supplement { margin-top: 0.75rem; font-size: 0.85rem; color: var(--muted); }
  .water-note { margin-top: 0.5rem; font-size: 0.8rem; color: var(--muted); font-style: italic; }
  .summary { margin-top: 1rem; font-size: 0.88rem; color: var(--muted); line-height: 1.6; border-top: 1px solid var(--border); padding-top: 0.75rem; }
  @media (max-width: 600px) {
    .food-table th:nth-child(4), .food-table td:nth-child(4),
    .food-table th:nth-child(5), .food-table td:nth-child(5),
    .food-table th:nth-child(6), .food-table td:nth-child(6) { display: none; }
  }
</style>"""


def _build_diet_scripts() -> str:
    """Return the <script> block for the diet HTML document."""
    return """<script>
function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}
document.documentElement.setAttribute('data-theme', 'original');
</script>"""


def _generate_diet_html(diet_data: dict[str, Any]) -> str:
    """Generate a self-contained HTML document for the diet plan."""
    title = diet_data.get("title", "Plan de Alimentación")
    description = diet_data.get("description", "")
    objective_label = diet_data.get("objective_label", "")
    training_day = diet_data.get("training_day", {})
    rest_day = diet_data.get("rest_day", {})

    stylesheet = _build_diet_stylesheet()
    training_section = _render_day_section(training_day, "🏋️", "Día de Entrenamiento")
    rest_section = _render_day_section(rest_day, "😴", "Día de Descanso")
    notes_section = _build_diet_notes_section(
        health_notes=diet_data.get("health_notes", []),
        supplement_suggestions=diet_data.get("supplement_suggestions", ""),
        water_notes=diet_data.get("water_notes", ""),
        nutritional_summary=diet_data.get("nutritional_summary", ""),
    )
    scripts = _build_diet_scripts()

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{stylesheet}
</head>
<body>
<div class="theme-btns">
  <button class="theme-btn active" onclick="setTheme('original')">Original</button>
  <button class="theme-btn" onclick="setTheme('dark')">Dark</button>
  <button class="theme-btn" onclick="setTheme('light')">Light</button>
</div>
<h1>{title}</h1>
<p class="objective">{objective_label}</p>
<p class="description">{description}</p>

{training_section}

{rest_section}

{notes_section}

{scripts}
</body>
</html>"""


# ── JSON extraction helpers ───────────────────────────────────────────────────

def _escape_string_literals(text: str) -> str:
    """
    Walk the JSON character by character and escape control characters
    (newlines, tabs, carriage returns) that appear *inside* string values.

    Gemini sometimes emits raw newlines inside string values, which is
    illegal JSON and causes "Unterminated string" parse errors.
    """
    result: list[str] = []
    in_string = False
    escaped = False

    for ch in text:
        if escaped:
            result.append(ch)
            escaped = False
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue

        if in_string:
            if ch == "\n":
                result.append("\\n")
            elif ch == "\r":
                result.append("\\r")
            elif ch == "\t":
                result.append("\\t")
            else:
                result.append(ch)
        else:
            result.append(ch)

    return "".join(result)


def _extract_json(raw: str) -> str:
    """
    Best-effort extraction of valid JSON from a Gemini response.

    Handles the most common Gemini output impurities:
    1. Markdown code fences (```json ... ```)
    2. Text before/after the JSON object
    3. Raw newlines / tabs inside string values (→ Unterminated string error)
    4. JavaScript single-line comments  // ...
    5. JavaScript multi-line comments  /* ... */
    6. Trailing commas before } or ]
    7. JavaScript `undefined` / NaN / Infinity → replaced with null
    """
    text = raw.strip()

    # 1. Strip code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # 2. Find the first '{' and last matching '}' to isolate the JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    # 3. Remove /* ... */ multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # 4. Remove // single-line comments at end of lines (not inside strings)
    text = re.sub(r"(?m)//[^\n\"]*$", "", text)

    # 5. Replace JavaScript-only literals
    text = re.sub(r"\bundefined\b", "null", text)
    text = re.sub(r"\bNaN\b", "null", text)
    text = re.sub(r"\bInfinity\b", "null", text)

    # 6. Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 7. Escape raw control characters inside string literals
    text = _escape_string_literals(text)

    return text.strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

_WEEKDAY_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _get_spanish_weekday(d: date_type) -> str:
    """Return the Spanish name of the weekday for a given date."""
    return _WEEKDAY_ES[d.weekday()]


def _recalculate_meal_totals(meal: dict[str, Any]) -> None:
    """Recalculate meal macro totals from its food list."""
    foods = meal.get("foods", [])
    meal["total_calories"] = round(sum(f.get("calories", 0) for f in foods), 1)
    meal["total_protein_g"] = round(sum(f.get("protein_g", 0) for f in foods), 1)
    meal["total_carbs_g"] = round(sum(f.get("carbs_g", 0) for f in foods), 1)
    meal["total_fat_g"] = round(sum(f.get("fat_g", 0) for f in foods), 1)


def _extract_grams_from_portion(portion: str) -> float | None:
    """Extract a gram (or ml treated as g) weight from a portion string.

    Prefers explicit parenthetical amounts like "(120g)" over bare quantities.
    Examples:
      "1 unidad mediana (120g)" → 120.0
      "80g"                     → 80.0
      "250ml"                   → 250.0
      "1 cucharada (15 ml)"     → 15.0
    """
    # Prefer parenthetical: (Xg) or (X ml)
    match = re.search(r'\((\d+(?:[.,]\d+)?)\s*(?:g|gr|ml)\b\)', portion, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", "."))
    # Fallback: bare Xg or Xml
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:g|gr|ml)\b', portion, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def _enrich_diet_with_fatsecret(diet_data: dict[str, Any]) -> None:
    """Populate food macros using FatSecret (primary) → USDA (fallback) for each food item.

    Gemini provides food names and portions only — no calorie/macro values.
    This function resolves per-100g macros from verified nutrition databases,
    scales them to the actual portion gram weight, and writes the values into
    each food dict. Unique food names are resolved in parallel via a thread pool.
    After enrichment, meal and day totals are recalculated from the food values.
    Foods where both sources fail are left with zero macros (logged as warnings).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from dataclasses import dataclass

    from .fatsecret_service import FatSecretServiceError, search_food_by_name as fatsecret_search
    from .usda_service import USDAServiceError, search_food_by_name as usda_search

    @dataclass
    class NutritionResult:
        calories_per_100g: float
        protein_per_100g: float
        carbs_per_100g: float
        fat_per_100g: float
        source: str

    # Collect (food_dict, name_lower, grams) for every food with a parsable portion
    food_items: list[tuple[dict[str, Any], str, float]] = []
    for day_key in ("training_day", "rest_day"):
        day = diet_data.get(day_key)
        if not isinstance(day, dict):
            continue
        for meal in day.get("meals") or []:
            if not isinstance(meal, dict):
                continue
            for food in meal.get("foods") or []:
                if not isinstance(food, dict):
                    continue
                grams = _extract_grams_from_portion(food.get("portion", ""))
                if grams and grams > 0 and food.get("name"):
                    food_items.append((food, food["name"].lower(), grams))

    if not food_items:
        return

    # Resolve unique names in parallel — FatSecret first, USDA fallback
    unique_names: set[str] = {name for _, name, _ in food_items}
    results: dict[str, NutritionResult] = {}

    def _lookup(name: str) -> tuple[str, NutritionResult | None]:
        try:
            r = fatsecret_search(name)
            return (name, NutritionResult(
                calories_per_100g=r.calories_per_100g,
                protein_per_100g=r.protein_per_100g,
                carbs_per_100g=r.carbs_per_100g,
                fat_per_100g=r.fat_per_100g,
                source="fatsecret",
            ))
        except (FatSecretServiceError, Exception):
            pass

        try:
            r = usda_search(name)
            return (name, NutritionResult(
                calories_per_100g=r.calories_per_100g,
                protein_per_100g=r.protein_per_100g,
                carbs_per_100g=r.carbs_per_100g,
                fat_per_100g=r.fat_per_100g,
                source="usda",
            ))
        except (USDAServiceError, Exception):
            pass

        logger.warning("diet_enrich food=%s: not found in FatSecret or USDA", name)
        return (name, None)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_lookup, name): name for name in unique_names}
        for future in as_completed(futures):
            name, result = future.result()
            if result is not None:
                results[name] = result
                logger.info("diet_enrich food=%s source=%s", name, result.source)

    # Apply resolved macros to each food item
    for food, name, grams in food_items:
        result = results.get(name)
        if result is None:
            food["calories"] = 0.0
            food["protein_g"] = 0.0
            food["carbs_g"] = 0.0
            food["fat_g"] = 0.0
            continue
        factor = grams / 100.0
        food["calories"] = round(result.calories_per_100g * factor, 1)
        food["protein_g"] = round(result.protein_per_100g * factor, 1)
        food["carbs_g"] = round(result.carbs_per_100g * factor, 1)
        food["fat_g"] = round(result.fat_per_100g * factor, 1)

    # Recalculate meal and day totals from updated food values
    for day_key in ("training_day", "rest_day"):
        day = diet_data.get(day_key)
        if not isinstance(day, dict):
            continue
        day_calories = day_protein = day_carbs = day_fat = 0.0
        for meal in day.get("meals") or []:
            if not isinstance(meal, dict):
                continue
            _recalculate_meal_totals(meal)
            day_calories += meal.get("total_calories", 0)
            day_protein += meal.get("total_protein_g", 0)
            day_carbs += meal.get("total_carbs_g", 0)
            day_fat += meal.get("total_fat_g", 0)
        day["total_calories"] = round(day_calories, 1)
        day["total_protein_g"] = round(day_protein, 1)
        day["total_carbs_g"] = round(day_carbs, 1)
        day["total_fat_g"] = round(day_fat, 1)


# ── Service ───────────────────────────────────────────────────────────────────

class DietService(BaseAIGenerationService):
    """Business logic for AI diet plan generation, editing, and retrieval."""

    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_ERROR = "error"

    # ── BaseAIGenerationService abstract method implementations ───────────────

    @classmethod
    def _upsert_record(
        cls, db: Session, *, user_id: int, intake: dict[str, Any]
    ) -> UserDiet:
        return cls._upsert_diet(db, user_id=user_id, status=cls.STATUS_PROCESSING, intake_data=intake)

    @classmethod
    def _get_active_record(cls, db: Session, *, user_id: int) -> UserDiet:
        return cls.get_active_diet(db, user_id=user_id)

    @classmethod
    def _get_record_data(cls, record: Any) -> dict[str, Any] | None:
        return cast(Any, record).diet_data

    @classmethod
    def _set_record_ready(cls, record: Any, *, raw_data: dict[str, Any], html: str) -> None:
        d = cast(Any, record)
        # Persist training_days from intake_data into diet_data for the meal tracker.
        # intake_data is stored on the record by _upsert_diet during generate_from_text.
        if "training_days" not in raw_data:
            intake_data: dict[str, Any] = d.intake_data or {}
            raw_data["training_days"] = intake_data.get("training_days") or []
        d.status = cls.STATUS_READY
        d.html_content = html
        d.diet_data = raw_data
        d.error_message = None
        # Reset meal tracker so it starts fresh with the new diet
        d.current_meal_index = 0
        d.current_meal_date = None

    @classmethod
    def _set_record_error(cls, record: Any, *, error_message: str) -> None:
        d = cast(Any, record)
        d.status = cls.STATUS_ERROR
        d.error_message = error_message

    @classmethod
    def _set_record_processing(cls, record: Any) -> None:
        cast(Any, record).status = cls.STATUS_PROCESSING

    @classmethod
    def _build_generation_prompt(
        cls,
        intake: dict[str, Any],
        free_text: str,
        user_bio: dict[str, Any],
        **kwargs: Any,
    ) -> str:
        routine_data: dict[str, Any] | None = kwargs.get("routine_data")
        return _build_diet_generation_prompt(intake, free_text, user_bio, routine_data)

    @classmethod
    def _build_edit_prompt(cls, current_data: dict[str, Any], edit_instruction: str) -> str:
        return _build_diet_edit_prompt(current_data, edit_instruction)

    @classmethod
    def _call_gemini_and_parse(cls, prompt: str) -> dict[str, Any]:
        return cls._call_gemini(prompt)

    @classmethod
    def _generate_html(cls, raw_data: dict[str, Any]) -> str:
        return _generate_diet_html(raw_data)

    @classmethod
    def _post_process(cls, raw_data: dict[str, Any], **kwargs: Any) -> None:
        # Replace AI-estimated macros with verified FatSecret data
        _enrich_diet_with_fatsecret(raw_data)

    @classmethod
    def _get_no_data_exception(cls) -> Exception:
        return DietParsingError("No diet data available to edit.")

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def generate_from_text(
        cls,
        db: Session,
        *,
        user_id: int,
        intake: dict[str, Any],
        free_text: str,
        user_bio: dict[str, Any],
        routine_data: dict[str, Any] | None = None,
    ) -> UserDiet:
        """Generate a personalized diet plan from intake form + free text via Gemini."""
        return super().generate_from_text(
            db,
            user_id=user_id,
            intake=intake,
            free_text=free_text,
            user_bio=user_bio,
            routine_data=routine_data,
        )  # type: ignore[return-value]

    @classmethod
    def edit_diet(
        cls,
        db: Session,
        *,
        user_id: int,
        edit_instruction: str,
    ) -> UserDiet:
        """Apply an edit instruction to the user's current diet via Gemini."""
        return cls.edit_record(db, user_id=user_id, edit_instruction=edit_instruction)  # type: ignore[return-value]

    @classmethod
    def get_active_diet(cls, db: Session, *, user_id: int) -> UserDiet:
        """Return the user's active diet plan or raise DietNotFoundError."""
        diet = db.query(UserDiet).filter(UserDiet.user_id == user_id).first()
        if diet is None:
            raise DietNotFoundError("No active diet plan found.")
        return diet

    @classmethod
    def get_current_meal(cls, db: Session, *, user_id: int) -> dict[str, Any]:
        """Return the current planned meal based on today's day type and tracker index."""
        diet = cls.get_active_diet(db, user_id=user_id)
        d = cast(Any, diet)

        if d.status != "ready":
            raise DietNotFoundError("No active diet plan found.")

        diet_data: dict[str, Any] = d.diet_data or {}
        today = date_type.today()
        today_str = today.isoformat()

        # Auto-reset index if date has changed
        if d.current_meal_date != today:
            d.current_meal_index = 0
            d.current_meal_date = today
            db.commit()

        training_days: list[str] = [t.lower() for t in (diet_data.get("training_days") or [])]
        is_training = _get_spanish_weekday(today) in training_days
        day_key = "training_day" if is_training else "rest_day"
        day_data = diet_data.get(day_key) or diet_data.get("rest_day") or {}
        meals: list[dict[str, Any]] = day_data.get("meals") or []
        total_meals = len(meals)

        meal_index = min(int(d.current_meal_index or 0), max(total_meals - 1, 0))
        planned_meal = meals[meal_index] if meals else None

        # Check for a daily override (set via apply_meal_alternative with scope='today')
        daily_overrides: dict[str, Any] = d.daily_overrides or {}
        today_overrides: dict[str, Any] = daily_overrides.get(today_str) or {}
        override = today_overrides.get(str(meal_index))
        is_overridden = override is not None
        current_meal = override if is_overridden else planned_meal

        return {
            "day_type": day_key,
            "meal": current_meal,
            "meal_index": meal_index,
            "total_meals": total_meals,
            "is_last_meal": meal_index >= total_meals - 1,
            "is_overridden": is_overridden,
        }

    @classmethod
    def log_meal(cls, db: Session, *, user_id: int, action: str) -> dict[str, Any]:
        """Mark the current meal as complete or skipped, advancing the tracker index.

        When action is 'complete', the meal's macros are added to today's daily_consumed tally.
        """
        diet = cls.get_active_diet(db, user_id=user_id)
        d = cast(Any, diet)

        today = date_type.today()
        today_str = today.isoformat()

        if d.current_meal_date != today:
            d.current_meal_index = 0
            d.current_meal_date = today

        diet_data: dict[str, Any] = d.diet_data or {}
        training_days: list[str] = [t.lower() for t in (diet_data.get("training_days") or [])]
        is_training = _get_spanish_weekday(today) in training_days
        day_key = "training_day" if is_training else "rest_day"
        day_data = diet_data.get(day_key) or diet_data.get("rest_day") or {}
        meals: list[dict[str, Any]] = day_data.get("meals") or []
        total_meals = len(meals)

        current_index = int(d.current_meal_index or 0)

        # Accumulate consumed macros only when the user marks the meal as complete
        if action == "complete" and current_index < total_meals:
            # Resolve the meal (may be a daily override)
            daily_overrides: dict[str, Any] = d.daily_overrides or {}
            today_overrides: dict[str, Any] = daily_overrides.get(today_str) or {}
            meal = today_overrides.get(str(current_index)) or (meals[current_index] if meals else None)

            if meal:
                meal_calories  = float(meal.get("total_calories",  0))
                meal_protein_g = float(meal.get("total_protein_g", 0))
                meal_carbs_g   = float(meal.get("total_carbs_g",   0))
                meal_fat_g     = float(meal.get("total_fat_g",     0))

                # ── Update diet-level daily_consumed tracker ──────────────
                consumed: dict[str, Any] = copy.deepcopy(d.daily_consumed or {})
                day_entry: dict[str, float] = consumed.get(today_str) or {
                    "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0
                }
                day_entry["calories"]  = round(day_entry["calories"]  + meal_calories,  1)
                day_entry["protein_g"] = round(day_entry["protein_g"] + meal_protein_g, 1)
                day_entry["carbs_g"]   = round(day_entry["carbs_g"]   + meal_carbs_g,   1)
                day_entry["fat_g"]     = round(day_entry["fat_g"]      + meal_fat_g,    1)
                consumed[today_str] = day_entry
                d.daily_consumed = consumed
                flag_modified(d, "daily_consumed")

                # ── Also write into DailyNutrition so the dashboard reflects it ──
                # Local import avoids circular dependency (nutrition_service → diet_service)
                from .nutrition_service import NutritionService  # noqa: PLC0415
                daily = NutritionService.get_or_create_daily_nutrition(db, user_id=user_id)
                daily.total_calories   += meal_calories
                daily.protein_consumed += meal_protein_g
                daily.carbs_consumed   += meal_carbs_g
                daily.fat_consumed     += meal_fat_g

        next_index = min(current_index + 1, total_meals)  # clamp — don't wrap daily
        d.current_meal_index = next_index
        d.current_meal_date = today
        db.commit()

        return {
            "current_meal_index": next_index,
            "current_meal_date": today_str,
            "advanced": next_index > current_index,
        }

    @classmethod
    def get_meal_alternative(cls, db: Session, *, user_id: int) -> dict[str, Any]:
        """Generate an AI alternative for the current planned meal via Gemini.

        Returns a meal with the same calorie target (±20 kcal) and macros (±5 g each),
        respecting the user's food preferences stored in intake_data.
        """
        diet = cls.get_active_diet(db, user_id=user_id)
        d = cast(Any, diet)
        if d.status != "ready":
            raise DietNotFoundError("No active diet plan found.")

        # Get current meal info (reuses existing day-type + index resolution)
        current = cls.get_current_meal(db, user_id=user_id)
        meal: dict[str, Any] | None = current.get("meal")
        if not meal:
            raise DietNotFoundError("No hay comida planificada en este momento.")

        meal_index: int = current["meal_index"]
        day_type: str = current["day_type"]

        intake: dict[str, Any] = d.intake_data or {}
        restrictions = intake.get("dietary_restrictions") or "ninguna"
        allergies = intake.get("food_allergies") or "ninguna"
        disliked = intake.get("disliked_foods") or "ninguno"
        budget = intake.get("budget_level") or "moderado"
        cooking = intake.get("cooking_time") or "moderado"
        free_text = intake.get("free_text") or ""

        cal   = float(meal.get("total_calories",  0))
        prot  = float(meal.get("total_protein_g", 0))
        carbs = float(meal.get("total_carbs_g",   0))
        fat   = float(meal.get("total_fat_g",     0))

        foods_summary = ", ".join(
            f"{f.get('portion', '')} {f.get('name', '')}".strip()
            for f in (meal.get("foods") or [])
        )

        free_text_section = f"\nINFORMACIÓN ADICIONAL: {free_text.strip()}" if free_text.strip() else ""

        prompt = f"""Genera una comida alternativa para reemplazar "{meal.get('name', 'esta comida')}" de un plan de dieta personalizado.

COMIDA ACTUAL: {meal.get('name')}
ALIMENTOS ACTUALES: {foods_summary}
CALORÍAS OBJETIVO: {cal:.0f} kcal (rango aceptable: {cal - 20:.0f}–{cal + 20:.0f} kcal)
PROTEÍNAS: {prot:.0f}g (rango: {prot - 5:.0f}–{prot + 5:.0f}g)
CARBOHIDRATOS: {carbs:.0f}g (rango: {carbs - 5:.0f}–{carbs + 5:.0f}g)
GRASAS: {fat:.0f}g (rango: {fat - 5:.0f}–{fat + 5:.0f}g)

PREFERENCIAS DEL USUARIO:
- Restricciones dietéticas: {restrictions}
- Alergias: {allergies}
- Alimentos que NO le gustan: {disliked}
- Presupuesto: {budget}
- Tiempo de cocción: {cooking}{free_text_section}

INSTRUCCIONES:
- La alternativa debe ser DIFERENTE a la comida actual (distintos alimentos)
- Respetar estrictamente las restricciones, alergias y alimentos que no le gustan
- Priorizar alimentos que el usuario mencionó que le gustan
- Los totales deben estar dentro de los rangos indicados

Devuelve SOLO JSON válido — sin markdown, sin código, sin explicaciones:
{{
  "id": "meal_alt",
  "name": "Nombre de la comida en español",
  "foods": [
    {{
      "name": "nombre del alimento",
      "portion": "cantidad y unidad (ej: 150g, 1 unidad)",
      "calories": 0.0,
      "protein_g": 0.0,
      "carbs_g": 0.0,
      "fat_g": 0.0,
      "notes": ""
    }}
  ],
  "total_calories": 0.0,
  "total_protein_g": 0.0,
  "total_carbs_g": 0.0,
  "total_fat_g": 0.0,
  "notes": ""
}}"""

        alternative_data = cls._call_gemini_light(prompt)

        return {
            "meal": alternative_data,
            "day_type": day_type,
            "meal_index": meal_index,
        }

    @classmethod
    def apply_meal_alternative(
        cls,
        db: Session,
        *,
        user_id: int,
        meal_index: int,
        day_type: str,
        scope: str,
        meal: dict[str, Any],
    ) -> None:
        """Apply an alternative meal either permanently or as a 24 h daily override.

        scope='diet'  → replaces the meal in diet_data permanently.
        scope='today' → stores in daily_overrides[today][meal_index]; expires at midnight.
        """
        diet = cls.get_active_diet(db, user_id=user_id)
        d = cast(Any, diet)
        if d.status != "ready":
            raise DietNotFoundError("No active diet plan found.")

        today_str = date_type.today().isoformat()

        if scope == "today":
            overrides: dict[str, Any] = copy.deepcopy(d.daily_overrides or {})
            day_overrides = overrides.get(today_str) or {}
            day_overrides[str(meal_index)] = meal
            overrides[today_str] = day_overrides
            d.daily_overrides = overrides
            flag_modified(d, "daily_overrides")

        else:  # scope == "diet" — permanent replacement
            diet_data: dict[str, Any] = copy.deepcopy(d.diet_data or {})
            day_data: dict[str, Any] = diet_data.get(day_type) or {}
            meals: list[dict[str, Any]] = day_data.get("meals") or []
            if 0 <= meal_index < len(meals):
                meals[meal_index] = meal
                day_data["meals"] = meals
                diet_data[day_type] = day_data
                d.diet_data = diet_data
                flag_modified(d, "diet_data")
            else:
                raise DietParsingError(f"meal_index {meal_index} out of range.")

        db.commit()

    @classmethod
    def modify_meal(
        cls,
        db: Session,
        *,
        user_id: int,
        day_type: str,
        meal_id: str,
        action: str,
        food: dict[str, Any] | None = None,
        food_index: int | None = None,
    ) -> UserDiet:
        """Add or remove a food item from a specific meal."""
        diet = cls.get_active_diet(db, user_id=user_id)
        d = cast(Any, diet)

        if not d.diet_data:
            raise DietParsingError("No diet data to modify.")

        diet_data: dict[str, Any] = copy.deepcopy(d.diet_data)
        day = diet_data.get(day_type)
        if not day:
            raise DietParsingError(f"Day type '{day_type}' not found in diet.")

        meals: list[dict[str, Any]] = day.get("meals") or []
        meal = next((m for m in meals if m.get("id") == meal_id), None)
        if meal is None:
            raise DietParsingError(f"Meal '{meal_id}' not found in {day_type}.")

        if action == "add_food" and food is not None:
            meal.setdefault("foods", []).append(food)
            _recalculate_meal_totals(meal)
        elif action == "remove_food" and food_index is not None:
            foods = meal.get("foods", [])
            if 0 <= food_index < len(foods):
                foods.pop(food_index)
                _recalculate_meal_totals(meal)

        # Reassign to trigger SQLAlchemy dirty tracking on JSON column
        d.diet_data = diet_data
        db.commit()
        db.refresh(diet)
        return diet

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _upsert_diet(
        cls,
        db: Session,
        *,
        user_id: int,
        status: str,
        intake_data: dict[str, Any] | None = None,
    ) -> UserDiet:
        """Create or replace the user's diet record."""
        diet = db.query(UserDiet).filter(UserDiet.user_id == user_id).first()
        if diet is None:
            diet = UserDiet(user_id=user_id)
            db.add(diet)

        d = cast(Any, diet)
        d.status = status
        d.source_type = "ai_text"
        d.html_content = None
        d.diet_data = None
        d.error_message = None
        if intake_data is not None:
            d.intake_data = intake_data

        return diet

    @classmethod
    def _call_gemini_light(cls, prompt: str) -> dict[str, Any]:
        """Lightweight Gemini call for single-meal generation (lower token limit, higher temperature)."""
        if not settings.GEMINI_API_KEY:
            raise DietParsingError("Gemini API key not configured.")

        model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        url = f"{GEMINI_API_BASE_URL}/{model}:generateContent?key={settings.GEMINI_API_KEY}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": DietConstants.GEMINI_ALTERNATIVE_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        with httpx.Client(timeout=DietConstants.GEMINI_ALTERNATIVE_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

        candidates = response.json().get("candidates", [])
        if not candidates:
            raise DietParsingError("Gemini returned no candidates.")

        raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
        cleaned = _extract_json(raw_text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise DietParsingError(f"Failed to parse Gemini alternative response: {exc}") from exc

    @classmethod
    def _call_gemini(cls, prompt: str) -> dict[str, Any]:
        """Send a text-only request to Gemini and parse the JSON response."""
        if not settings.GEMINI_API_KEY:
            raise DietParsingError("Gemini API key not configured.")

        model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        url = f"{GEMINI_API_BASE_URL}/{model}:generateContent?key={settings.GEMINI_API_KEY}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": DietConstants.GEMINI_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        with httpx.Client(timeout=DietConstants.GEMINI_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

        candidates = response.json().get("candidates", [])
        if not candidates:
            raise DietParsingError("Gemini returned no candidates.")

        raw_text = candidates[0]["content"]["parts"][0]["text"].strip()

        cleaned = _extract_json(raw_text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # Log enough context to diagnose the failure
            error_char = exc.pos if exc.pos is not None else 0
            context_start = max(0, error_char - 100)
            context_end = min(len(cleaned), error_char + 100)
            logger.error(
                "Gemini diet JSON parse error at char %d: %s\n"
                "Context around error: ...%s...\n"
                "Raw text (first 1000): %s",
                error_char,
                exc,
                cleaned[context_start:context_end],
                raw_text[:1000],
            )
            raise DietParsingError(f"Failed to parse Gemini diet response: {exc}") from exc

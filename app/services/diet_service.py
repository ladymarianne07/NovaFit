"""Diet Service — AI-powered personalized diet plan generation and editing."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, cast

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..core.custom_exceptions import DietNotFoundError, DietParsingError
from ..db.models import UserDiet, UserRoutine

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# ── JSON schema instructions ──────────────────────────────────────────────────

_DIET_JSON_SCHEMA = """
Return ONLY valid JSON — no markdown, no code fences, no explanations.
The JSON must follow this exact structure:

{
  "title": "Plan de alimentación personalizado",
  "description": "2-3 sentences describing the diet approach, objective, and why these calories/macros were chosen",
  "objective_label": "Pérdida de grasa / Recomposición corporal / etc.",
  "target_calories_rest": 1800,
  "target_calories_training": 2200,
  "target_protein_g": 150,
  "target_carbs_g": 200,
  "target_fat_g": 60,
  "water_ml_rest": 2500,
  "water_ml_training": 3200,
  "water_notes": "Brief explanation of how water intake was calculated",
  "training_day": {
    "day_type": "training",
    "label": "Día de entrenamiento",
    "total_calories": 2200,
    "total_protein_g": 160,
    "total_carbs_g": 240,
    "total_fat_g": 62,
    "water_ml": 3200,
    "notes": "Optional general notes for training days",
    "meals": [
      {
        "id": "breakfast",
        "name": "Desayuno",
        "time": "07:00 - 08:00",
        "total_calories": 480,
        "total_protein_g": 28,
        "total_carbs_g": 60,
        "total_fat_g": 12,
        "notes": "Optional notes about this meal (timing, pre/post workout context, etc.)",
        "foods": [
          {
            "name": "Avena con leche descremada",
            "portion": "80g avena + 250ml leche",
            "calories": 350,
            "protein_g": 18,
            "carbs_g": 52,
            "fat_g": 6,
            "notes": ""
          },
          {
            "name": "Banana",
            "portion": "1 unidad mediana (120g)",
            "calories": 110,
            "protein_g": 1,
            "carbs_g": 28,
            "fat_g": 0,
            "notes": ""
          }
        ]
      }
    ]
  },
  "rest_day": {
    "day_type": "rest",
    "label": "Día de descanso",
    "total_calories": 1800,
    "total_protein_g": 150,
    "total_carbs_g": 180,
    "total_fat_g": 55,
    "water_ml": 2500,
    "notes": "Optional general notes for rest days",
    "meals": []
  },
  "health_notes": [
    "Tip or health note related to the user's conditions",
    "Another relevant tip"
  ],
  "supplement_suggestions": "Optional brief supplement suggestion based on objective (or empty string)",
  "nutritional_summary": "1-2 sentence summary of the overall plan and expected results"
}

Rules:
- title: concise and motivating
- description: explain the calorie split between training and rest days, and why macros were set as they were
- training_day.total_calories must equal sum of all meal calories (within ±5 kcal rounding)
- rest_day.total_calories must equal sum of all rest day meal calories (within ±5 kcal rounding)
- Each food's calories must approximately equal: protein_g×4 + carbs_g×4 + fat_g×9
- meal ids: short lowercase alphanumeric with underscores (e.g. breakfast, lunch, dinner, snack_1, post_workout)
- Meal times should be realistic based on typical Argentine schedule and user preferences
- Water: base = weight_kg × 35 ml/kg, add 500-700 ml on training days; minimum 2000 ml rest / 2500 ml training
- Foods: use specific Argentine/regional names when applicable (palta, batata, yerba mate, etc.)
- Portions: always include amount (grams, ml, units) in parentheses
- Keep all text in Spanish (rioplatense tone)
- health_notes: 2-4 practical tips relevant to the user's conditions, restrictions, or objective
- supplement_suggestions: only if clearly beneficial for objective; empty string if none warranted
- DO NOT include foods that violate dietary_restrictions or food_allergies
- DO NOT include disliked_foods listed by the user
- training_day and rest_day should share the same meal structure but differ in calorie totals and portion sizes
- The extra calories on training days should come primarily from carbohydrates (pre/post workout meals)
"""

_DIET_SYSTEM_PROMPT = """Sos un nutricionista deportivo especializado en nutrición basada en evidencia científica, trabajando para NovaFitness.

PRINCIPIO FUNDAMENTAL — PRECISIÓN NUTRICIONAL:
Cada plan de alimentación debe alcanzar EXACTAMENTE los objetivos calóricos y de macronutrientes del usuario.
Los totales de cada día deben coincidir con las metas (tolerancia ±5% por redondeo).

CÁLCULO DE CALORÍAS POR TIPO DE DÍA:
- Día de descanso: usar exactamente las calorías objetivo del perfil del usuario (target_calories)
- Día de entrenamiento: target_calories + calorías quemadas en la sesión de entrenamiento
  * Si hay rutina activa, usar las kcal estimadas por sesión de la rutina
  * Si no hay rutina, estimar según tipo de entrenamiento y duración declarada
  * Las calorías extra en días de entrenamiento deben provenir principalmente de carbohidratos

DISTRIBUCIÓN DE MACRONUTRIENTES:
- Respetar exactamente los porcentajes/gramos del perfil del usuario
- En días de entreno: aumentar carbohidratos principalmente (combustible para el ejercicio)
- Proteína: distribuir uniformemente en todas las comidas (mínimo 20-30g por comida principal)
- Grasas: evitar en la comida pre-entrenamiento, distribuir en las demás

ESTRUCTURA DE COMIDAS:
- Pre-entrenamiento (1-2h antes): rico en carbohidratos complejos, moderado en proteína, bajo en grasa
- Post-entrenamiento (dentro de 1h): proteína + carbohidratos simples (recuperación y síntesis proteica)
- Resto del día: distribución equilibrada

AGUA:
- Base: peso_corporal (kg) × 35 ml
- Agregar 500-700 ml en días de entrenamiento
- Ajustar si hay condiciones que lo requieran (riñones, diabetes, etc.)
- Explicar brevemente el cálculo

RESTRICCIONES Y ALERGIAS — OBLIGATORIO:
- Verificar CADA alimento contra restricciones dietéticas y alergias declaradas
- Si hay restricción vegetariana: eliminar TODAS las carnes, aves y mariscos
- Si hay restricción vegana: eliminar además lácteos, huevos y miel
- Si hay intolerancia al gluten: eliminar trigo, avena convencional, cebada, centeno
- Si hay intolerancia a la lactosa: reemplazar lácteos por alternativas vegetales
- Si hay alergia a frutos secos: excluir completamente todos los frutos secos y derivados

CONDICIONES DE SALUD RELEVANTES:
- Diabetes tipo 2: priorizar carbohidratos de bajo índice glucémico, evitar azúcares simples
- Hipertensión: reducir sodio, aumentar potasio y magnesio
- Hipotiroidismo: evitar exceso de alimentos bociógenos crudos
- Síndrome de intestino irritable: evitar alimentos FODMAPs altos
- Hiperuricemia/gota: limitar purinas (vísceras, mariscos, fructosa)
- Anemia: priorizar hierro hem + vitamina C en la misma comida

PRESUPUESTO Y TIEMPO DE COCCIÓN:
- Económico: proteínas de huevo, legumbres, pollo muslo, arroz, avena, banana
- Moderado: incluir salmón, queso, palta, frutas variadas
- Sin límite: incluir proteínas premium, superalimentos, suplementos de calidad
- Mínimo tiempo: priorizar preparaciones simples (yogur + frutas, huevos revueltos, ensaladas)
"""


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
    meal_timing = intake.get("meal_timing_preference", "") or "Sin preferencia horaria específica"

    free_text_section = (
        f"\nINFORMACIÓN ADICIONAL DEL USUARIO:\n{free_text.strip()}"
        if free_text and free_text.strip()
        else ""
    )

    return f"""{_DIET_SYSTEM_PROMPT}

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
PREFERENCIA DE HORARIOS: {meal_timing}
{free_text_section}

---

TU TAREA:
1. Analizar PRIMERO todas las restricciones, alergias y condiciones de salud — ningún alimento prohibido puede aparecer
2. Calcular calorías para día de descanso (= target_calories del perfil) y día de entrenamiento (= target + kcal rutina)
3. Distribuir los macros objetivo exactamente en {meals_count} comidas por día
4. Diseñar comidas concretas con alimentos reales, porciones específicas y valores nutricionales precisos
5. Asegurar que los totales diarios coincidan con los objetivos (tolerancia ±5%)
6. Calcular el consumo de agua diario

{_DIET_JSON_SCHEMA}"""


def _build_diet_edit_prompt(current_diet_data: dict[str, Any], edit_instruction: str) -> str:
    """Build the prompt for editing an existing diet plan."""
    return f"""{_DIET_SYSTEM_PROMPT}

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

{_DIET_JSON_SCHEMA}"""


def _generate_diet_html(diet_data: dict[str, Any]) -> str:
    """Generate a self-contained HTML document for the diet plan."""
    title = diet_data.get("title", "Plan de Alimentación")
    description = diet_data.get("description", "")
    objective_label = diet_data.get("objective_label", "")
    training_day = diet_data.get("training_day", {})
    rest_day = diet_data.get("rest_day", {})
    health_notes = diet_data.get("health_notes", [])
    supplement_suggestions = diet_data.get("supplement_suggestions", "")
    nutritional_summary = diet_data.get("nutritional_summary", "")
    water_notes = diet_data.get("water_notes", "")

    def render_meals(day: dict[str, Any]) -> str:
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
    <span class="meal-time">{meal.get('time','')}</span>
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

    health_notes_html = "".join(f"<li>{note}</li>" for note in health_notes)
    supplement_html = f"<p class='supplement'><strong>Suplementación:</strong> {supplement_suggestions}</p>" if supplement_suggestions else ""
    water_note_html = f"<p class='water-note'>{water_notes}</p>" if water_notes else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: #0d0d1a;
    --card: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.12);
    --accent: #00f2c3;
    --text: rgba(255,255,255,0.9);
    --muted: rgba(255,255,255,0.55);
  }}
  [data-theme="light"] {{
    --bg: #e8f8fa;
    --card: rgba(255,255,255,0.75);
    --border: rgba(0,0,0,0.12);
    --accent: #00c8d8;
    --text: #0a1a1e;
    --muted: rgba(10,26,30,0.6);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 1rem; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; color: var(--accent); margin-bottom: 0.25rem; }}
  .objective {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 0.75rem; }}
  .description {{ font-size: 0.9rem; line-height: 1.6; margin-bottom: 1.5rem; color: var(--muted); }}
  .theme-btns {{ display:flex; gap:0.5rem; margin-bottom:1.5rem; flex-wrap:wrap; }}
  .theme-btn {{ padding:0.4rem 0.9rem; border-radius:20px; border:1px solid var(--border); background:var(--card); color:var(--text); cursor:pointer; font-size:0.82rem; }}
  .theme-btn.active {{ background:var(--accent); color:#0a1a1e; border-color:var(--accent); }}
  .day-section {{ margin-bottom: 2rem; }}
  .day-title {{ font-size: 1.1rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; padding-bottom: 0.3rem; border-bottom: 1px solid var(--border); }}
  .day-totals {{ display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }}
  .macro-pill {{ background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 0.3rem 0.8rem; font-size: 0.8rem; }}
  .macro-pill span {{ color: var(--accent); font-weight: 700; }}
  .water-pill {{ background: rgba(0,180,255,0.15); border: 1px solid rgba(0,180,255,0.3); border-radius: 20px; padding: 0.3rem 0.8rem; font-size: 0.8rem; }}
  .meal-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; }}
  .meal-header {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; flex-wrap: wrap; }}
  .meal-name {{ font-weight: 700; font-size: 0.95rem; flex: 1; }}
  .meal-time {{ font-size: 0.78rem; color: var(--muted); }}
  .meal-kcal {{ font-size: 0.85rem; color: var(--accent); font-weight: 600; margin-left: auto; }}
  .food-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  .food-table th {{ text-align: left; color: var(--muted); font-weight: 600; padding: 0.2rem 0.3rem; border-bottom: 1px solid var(--border); }}
  .food-table td {{ padding: 0.3rem 0.3rem; border-bottom: 1px solid rgba(255,255,255,0.05); }}
  .notes-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin-top: 1.5rem; }}
  .notes-title {{ font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; }}
  .notes-section ul {{ padding-left: 1.2rem; }}
  .notes-section li {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 0.35rem; line-height: 1.5; }}
  .supplement {{ margin-top: 0.75rem; font-size: 0.85rem; color: var(--muted); }}
  .water-note {{ margin-top: 0.5rem; font-size: 0.8rem; color: var(--muted); font-style: italic; }}
  .summary {{ margin-top: 1rem; font-size: 0.88rem; color: var(--muted); line-height: 1.6; border-top: 1px solid var(--border); padding-top: 0.75rem; }}
  @media (max-width: 600px) {{
    .food-table th:nth-child(4), .food-table td:nth-child(4),
    .food-table th:nth-child(5), .food-table td:nth-child(5),
    .food-table th:nth-child(6), .food-table td:nth-child(6) {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="theme-btns">
  <button class="theme-btn" onclick="setTheme('')">Original</button>
  <button class="theme-btn active" onclick="setTheme('dark')">Dark</button>
  <button class="theme-btn" onclick="setTheme('light')">Light</button>
</div>
<h1>{title}</h1>
<p class="objective">{objective_label}</p>
<p class="description">{description}</p>

<div class="day-section">
  <p class="day-title">🏋️ Día de Entrenamiento</p>
  <div class="day-totals">
    <div class="macro-pill">Calorías: <span>{round(training_day.get('total_calories', 0))} kcal</span></div>
    <div class="macro-pill">Proteína: <span>{round(training_day.get('total_protein_g', 0))}g</span></div>
    <div class="macro-pill">HC: <span>{round(training_day.get('total_carbs_g', 0))}g</span></div>
    <div class="macro-pill">Grasas: <span>{round(training_day.get('total_fat_g', 0))}g</span></div>
    <div class="water-pill">💧 {training_day.get('water_ml', 0)} ml agua</div>
  </div>
  {render_meals(training_day)}
</div>

<div class="day-section">
  <p class="day-title">😴 Día de Descanso</p>
  <div class="day-totals">
    <div class="macro-pill">Calorías: <span>{round(rest_day.get('total_calories', 0))} kcal</span></div>
    <div class="macro-pill">Proteína: <span>{round(rest_day.get('total_protein_g', 0))}g</span></div>
    <div class="macro-pill">HC: <span>{round(rest_day.get('total_carbs_g', 0))}g</span></div>
    <div class="macro-pill">Grasas: <span>{round(rest_day.get('total_fat_g', 0))}g</span></div>
    <div class="water-pill">💧 {rest_day.get('water_ml', 0)} ml agua</div>
  </div>
  {render_meals(rest_day)}
</div>

<div class="notes-section">
  <p class="notes-title">📋 Recomendaciones</p>
  <ul>{health_notes_html}</ul>
  {supplement_html}
  {water_note_html}
  <p class="summary">{nutritional_summary}</p>
</div>

<script>
function setTheme(t) {{
  document.documentElement.setAttribute('data-theme', t);
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}}
document.documentElement.setAttribute('data-theme', 'dark');
</script>
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


# ── Service ───────────────────────────────────────────────────────────────────

class DietService:
    """Business logic for AI diet plan generation, editing, and retrieval."""

    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_ERROR = "error"

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
        diet = cls._upsert_diet(
            db,
            user_id=user_id,
            status=cls.STATUS_PROCESSING,
            intake_data=intake,
        )
        db.commit()

        try:
            prompt = _build_diet_generation_prompt(intake, free_text, user_bio, routine_data)
            raw_data = cls._call_gemini(prompt)
            html = _generate_diet_html(raw_data)

            d = cast(Any, diet)
            d.status = cls.STATUS_READY
            d.html_content = html
            d.diet_data = raw_data
            d.error_message = None
        except Exception as exc:
            logger.exception("Failed to generate diet for user_id=%s", user_id)
            d = cast(Any, diet)
            d.status = cls.STATUS_ERROR
            d.error_message = str(exc)

        db.commit()
        db.refresh(diet)
        return diet

    @classmethod
    def edit_diet(
        cls,
        db: Session,
        *,
        user_id: int,
        edit_instruction: str,
    ) -> UserDiet:
        """Apply an edit instruction to the user's current diet via Gemini."""
        diet = cls.get_active_diet(db, user_id=user_id)

        current_data = cast(Any, diet).diet_data
        if not current_data:
            raise DietParsingError("No diet data available to edit.")

        d = cast(Any, diet)
        d.status = cls.STATUS_PROCESSING
        db.commit()

        try:
            prompt = _build_diet_edit_prompt(current_data, edit_instruction)
            raw_data = cls._call_gemini(prompt)
            html = _generate_diet_html(raw_data)

            d.status = cls.STATUS_READY
            d.html_content = html
            d.diet_data = raw_data
            d.error_message = None
        except Exception as exc:
            logger.exception("Failed to edit diet for user_id=%s", user_id)
            d.status = cls.STATUS_ERROR
            d.error_message = str(exc)

        db.commit()
        db.refresh(diet)
        return diet

    @classmethod
    def get_active_diet(cls, db: Session, *, user_id: int) -> UserDiet:
        """Return the user's active diet plan or raise DietNotFoundError."""
        diet = db.query(UserDiet).filter(UserDiet.user_id == user_id).first()
        if diet is None:
            raise DietNotFoundError("No active diet plan found.")
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
                "maxOutputTokens": 8192,
            },
        }

        with httpx.Client(timeout=120.0) as client:
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

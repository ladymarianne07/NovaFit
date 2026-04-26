"""Routine Service — file upload, AI generation, editing, HTML generation, and session logging."""

from __future__ import annotations

import base64
import json
import logging
import re
from datetime import date
from typing import Any, cast

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..constants import RoutineConstants, WorkoutConstants
from ..core.custom_exceptions import (
    RoutineFileTooLargeError,
    RoutineInvalidFileTypeError,
    RoutineNotFoundError,
    RoutineParsingError,
)
from ..db.models import UserRoutine, WorkoutSession
from ..services.workout_service import WorkoutService
from ..templates.routine import ROUTINE_JSON_SCHEMA, ROUTINE_FILE_PARSE_PROMPT, ROUTINE_SYSTEM_PROMPT
from .base_ai_generation_service import BaseAIGenerationService


logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _build_pt_generation_prompt(
    intake: dict[str, Any],
    free_text: str,
    user_bio: dict[str, Any],
) -> str:
    """Build the complete personal trainer prompt for AI routine generation."""
    objective_labels = {
        RoutineConstants.OBJECTIVE_FAT_LOSS: "Pérdida de grasa / definición muscular",
        RoutineConstants.OBJECTIVE_BODY_RECOMP: "Recomposición corporal (perder grasa y ganar músculo simultáneamente)",
        RoutineConstants.OBJECTIVE_MUSCLE_GAIN: "Ganancia de masa muscular",
    }
    objective = user_bio.get("objective") or intake.get("objective", "body_recomp")
    objective_label = objective_labels.get(objective, objective)

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

    bio_section = "\n".join(bio_lines) if bio_lines else "- (No disponible)"

    health_conditions = intake.get("health_conditions", "ninguna") or "ninguna"
    medications = intake.get("medications", "") or "ninguno"
    injuries = intake.get("injuries", "") or "ninguna"

    preferred = intake.get("preferred_exercises", "") or "Sin preferencias específicas declaradas"
    frequency = intake.get("frequency_days", "3-4")
    experience = intake.get("experience_level", "principiante")
    equipment = intake.get("equipment", "gimnasio completo")
    duration_months = intake.get("duration_months", 1)
    session_duration = intake.get("session_duration_minutes", 60)

    free_text_section = (
        f"\nDESCRIPCIÓN LIBRE DEL USUARIO:\n{free_text.strip()}"
        if free_text and free_text.strip()
        else ""
    )

    return f"""{ROUTINE_SYSTEM_PROMPT}

---

DATOS DEL USUARIO:

DATOS BIOMÉTRICOS:
{bio_section}

OBJETIVO PRINCIPAL: {objective_label}

CONDICIONES DE SALUD / ENFERMEDADES / PATOLOGÍAS:
{health_conditions}

MEDICAMENTOS ACTUALES:
{medications}

LESIONES ACTUALES O RECIENTES:
{injuries}

TIPOS DE EJERCICIO PREFERIDOS:
{preferred}

FRECUENCIA DE ENTRENAMIENTO: {frequency} días por semana
NIVEL DE EXPERIENCIA: {experience}
EQUIPAMIENTO DISPONIBLE: {equipment}
DURACIÓN DEL PLAN: {duration_months} {'mes' if duration_months == 1 else 'meses'}
DURACIÓN POR SESIÓN: {session_duration} minutos aproximadamente
{free_text_section}

---

TU TAREA:
1. Analizar PRIMERO todas las condiciones de salud declaradas y aplicar contraindicaciones estrictas
2. Generar una rutina de entrenamiento 100% personalizada para este usuario
3. La rutina debe tener exactamente {duration_months} {'fase' if duration_months == 1 else 'fases'} de progresión (una por mes)
4. Ajustar volumen, intensidad y tipo de ejercicios al objetivo declarado
5. Respetar el equipamiento disponible y las preferencias del usuario
6. Incluir calentamiento como nota en el primer ejercicio de cada sesión cuando corresponda

{ROUTINE_JSON_SCHEMA}"""


def _build_edit_prompt(current_routine_data: dict[str, Any], edit_instruction: str) -> str:
    """Build the prompt for editing an existing routine."""
    return f"""{ROUTINE_SYSTEM_PROMPT}

---

RUTINA ACTUAL (JSON):
{json.dumps(current_routine_data, ensure_ascii=False, indent=2)}

---

INSTRUCCIÓN DE MODIFICACIÓN DEL USUARIO:
"{edit_instruction}"

---

TU TAREA:
1. Analizar la instrucción de modificación
2. Aplicar los cambios solicitados respetando siempre las contraindicaciones de salud ya registradas
3. Mantener la estructura general de la rutina, modificando solo lo que se indica
4. Si la modificación implica agregar ejercicios contraindicados, rechazarlos y proponer alternativas seguras
5. Actualizar health_analysis.adaptations para registrar los cambios realizados

{ROUTINE_JSON_SCHEMA}"""


# ── Service ───────────────────────────────────────────────────────────────────

class RoutineService(BaseAIGenerationService):
    """Business logic for routine upload, AI generation, editing, and session logging."""

    # ── BaseAIGenerationService abstract method implementations ───────────────

    @classmethod
    def _upsert_record(
        cls, db: Session, *, user_id: int, intake: dict[str, Any]
    ) -> UserRoutine:
        return cls._upsert_routine(
            db,
            user_id=user_id,
            filename="ai_generated",
            source_type=RoutineConstants.SOURCE_AI_TEXT,
            status=RoutineConstants.STATUS_PROCESSING,
            intake_data=intake,
        )

    @classmethod
    def _get_active_record(cls, db: Session, *, user_id: int) -> UserRoutine:
        return cls.get_active_routine(db, user_id=user_id)

    @classmethod
    def _get_record_data(cls, record: Any) -> dict[str, Any] | None:
        return cast(Any, record).routine_data

    @classmethod
    def _set_record_ready(cls, record: Any, *, raw_data: dict[str, Any], html: str) -> None:
        rd = cast(Any, record)
        rd.status = RoutineConstants.STATUS_READY
        rd.html_content = html
        rd.routine_data = raw_data
        rd.health_analysis = raw_data.get("health_analysis")
        rd.error_message = None

    @classmethod
    def _set_record_error(cls, record: Any, *, error_message: str) -> None:
        rd = cast(Any, record)
        rd.status = RoutineConstants.STATUS_ERROR
        rd.error_message = error_message

    @classmethod
    def _set_record_processing(cls, record: Any) -> None:
        cast(Any, record).status = RoutineConstants.STATUS_PROCESSING

    @classmethod
    def _build_generation_prompt(
        cls,
        intake: dict[str, Any],
        free_text: str,
        user_bio: dict[str, Any],
        **kwargs: Any,
    ) -> str:
        return _build_pt_generation_prompt(intake, free_text, user_bio)

    @classmethod
    def _build_edit_prompt(cls, current_data: dict[str, Any], edit_instruction: str) -> str:
        return _build_edit_prompt(current_data, edit_instruction)

    @classmethod
    def _call_gemini_and_parse(cls, prompt: str) -> dict[str, Any]:
        return cls._call_gemini_text(prompt)

    @classmethod
    def _get_no_data_exception(cls) -> Exception:
        return RoutineParsingError("No routine data available to edit.")

    # ── Public API wrappers ───────────────────────────────────────────────────

    @classmethod
    def edit_routine(
        cls,
        db: Session,
        *,
        user_id: int,
        edit_instruction: str,
    ) -> UserRoutine:
        """Apply an edit instruction to the user's current routine via Gemini."""
        return cls.edit_record(db, user_id=user_id, edit_instruction=edit_instruction)  # type: ignore[return-value]

    # ── File upload ───────────────────────────────────────────────────────────

    @classmethod
    def validate_file(cls, file_bytes: bytes, mime_type: str) -> None:
        """Validate file size and MIME type before sending to Gemini."""
        if len(file_bytes) > RoutineConstants.MAX_FILE_SIZE_BYTES:
            raise RoutineFileTooLargeError(
                f"File exceeds maximum allowed size of {RoutineConstants.MAX_FILE_SIZE_MB} MB"
            )
        if mime_type not in RoutineConstants.ALLOWED_MIME_TYPES:
            raise RoutineInvalidFileTypeError(
                f"File type '{mime_type}' is not supported. "
                f"Allowed: {', '.join(sorted(RoutineConstants.ALLOWED_MIME_TYPES))}"
            )

    @classmethod
    def parse_and_save(
        cls,
        db: Session,
        *,
        user_id: int,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> UserRoutine:
        """Upload a file to Gemini, parse the routine, generate HTML, and persist."""
        cls.validate_file(file_bytes, mime_type)

        routine = cls._upsert_routine(
            db,
            user_id=user_id,
            filename=filename,
            source_type=RoutineConstants.SOURCE_FILE,
            status=RoutineConstants.STATUS_PROCESSING,
        )
        db.commit()

        try:
            raw_data = cls._call_gemini_file(file_bytes, mime_type)
            html = cls._generate_html(raw_data)

            rd = cast(Any, routine)
            rd.status = RoutineConstants.STATUS_READY
            rd.html_content = html
            rd.routine_data = raw_data
            rd.health_analysis = raw_data.get("health_analysis")
            rd.error_message = None
        except Exception as exc:
            logger.exception("Failed to parse routine for user_id=%s", user_id)
            rd = cast(Any, routine)
            rd.status = RoutineConstants.STATUS_ERROR
            rd.error_message = str(exc)

        db.commit()
        db.refresh(routine)
        return routine


    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get_active_routine(cls, db: Session, *, user_id: int) -> UserRoutine:
        """Return the user's active routine or raise RoutineNotFoundError."""
        routine = (
            db.query(UserRoutine)
            .filter(UserRoutine.user_id == user_id)
            .first()
        )
        if routine is None:
            raise RoutineNotFoundError("No active routine found.")
        return routine

    # ── Session logging ───────────────────────────────────────────────────────

    @classmethod
    def _calc_routine_kcal(
        cls,
        db: Session,
        *,
        exercises: list[dict[str, Any]],
        skipped_ids: list[str],
        session_duration_minutes: int,
        weight_kg: float,
    ) -> tuple[float, float]:
        """Return (base_kcal, adjusted_kcal) using MET × weight × duration for resistance training.

        Uses the 'fuerza_general' activity key (resistance training) to compute a physics-based
        calorie estimate from session_duration_minutes. Skipped exercises reduce the total
        proportionally by exercise count (fewer completed → fewer active minutes).
        """
        activity = WorkoutService.resolve_activity(db, "fuerza_general")
        metrics = WorkoutService.calculate_block_metrics(
            activity=activity,
            duration_minutes=session_duration_minutes,
            weight_kg=weight_kg,
            intensity_level="media",
            correction_factor=1.0,
        )
        base_kcal = round(float(metrics.kcal_est), 2)

        n_total = len(exercises)
        n_done = max(0, n_total - sum(1 for ex in exercises if ex.get("id") in skipped_ids))
        scale = (n_done / n_total) if n_total > 0 else 1.0
        adjusted_kcal = round(base_kcal * scale, 2)
        return base_kcal, adjusted_kcal

    @classmethod
    def log_session(
        cls,
        db: Session,
        *,
        user_id: int,
        session_id: str,
        session_date: date,
        skipped_exercise_ids: list[str],
        extra_exercises: list[dict[str, Any]],
        weight_kg: float,
    ) -> WorkoutSession:
        """Create a WorkoutSession from a routine session with optional skipped/extra exercises.

        Calories are calculated via MET × weight × hours (resistance training baseline),
        scaled proportionally for skipped exercises, plus extra exercises via their own MET values.
        """
        routine = cls.get_active_routine(db, user_id=user_id)

        routine_data = cast(Any, routine).routine_data or {}
        sessions: list[dict[str, Any]] = routine_data.get("sessions", [])

        target = next((s for s in sessions if s.get("id") == session_id), None)
        if target is None:
            raise RoutineNotFoundError(f"Session '{session_id}' not found in routine.")

        exercises: list[dict[str, Any]] = target.get("exercises", [])
        session_duration_minutes = int(target.get("session_duration_minutes", 60))

        # Routine base: MET × weight × duration (fuerza_general activity), scaled for skips.
        base_kcal, routine_kcal = cls._calc_routine_kcal(
            db,
            exercises=exercises,
            skipped_ids=skipped_exercise_ids,
            session_duration_minutes=session_duration_minutes,
            weight_kg=weight_kg,
        )

        # Extra exercises: MET × weight × hours — appropriate here because extras are
        # typically continuous activities (cardio, walking, HIIT) where MET is accurate.
        from ..schemas.routine import EXTRA_EXERCISE_MET
        extra_kcal = sum(
            round(
                EXTRA_EXERCISE_MET.get(ex.get("exercise_type", "resistance"), 4.5)
                * weight_kg
                * (int(ex.get("duration_minutes", 0)) / 60.0),
                2,
            )
            for ex in extra_exercises
        )

        total_kcal = round(routine_kcal + extra_kcal, 2)

        session = WorkoutSession(
            user_id=user_id,
            session_date=session_date,
            source=WorkoutConstants.SOURCE_ROUTINE,
            status=WorkoutConstants.STATUS_FINAL,
            raw_input=f"Rutina: {target.get('title', session_id)}",
            ai_output={
                "session_id": session_id,
                "session_title": target.get("title"),
                "weight_kg_used": weight_kg,
                "session_duration_minutes": session_duration_minutes,
                "base_kcal": base_kcal,
                "routine_kcal": routine_kcal,
                "extra_kcal": extra_kcal,
                "skipped_exercise_ids": skipped_exercise_ids,
                "extra_exercises": extra_exercises,
            },
            total_kcal_min=round(total_kcal * 0.9, 2),
            total_kcal_max=round(total_kcal * 1.1, 2),
            total_kcal_est=total_kcal,
        )

        db.add(session)
        db.flush()

        WorkoutService.refresh_daily_energy_log(db=db, user_id=user_id, log_date=session_date)
        db.commit()
        db.refresh(session)
        return session

    # ── Advance session (complete or skip) ────────────────────────────────────

    @classmethod
    def advance_session(
        cls,
        db: Session,
        *,
        user_id: int,
        action: str,
        weight_kg: float,
    ) -> dict[str, Any]:
        """Mark the current session as complete or skipped and advance the index.

        - 'complete': logs the session (creates WorkoutSession + calorie entry) then advances
        - 'skip': advances without logging calories
        The index wraps around so the cycle repeats indefinitely.

        Returns a lightweight dict with the advance result instead of the full routine object.
        """
        routine = cls.get_active_routine(db, user_id=user_id)

        routine_data = cast(Any, routine).routine_data or {}
        sessions: list[dict[str, Any]] = routine_data.get("sessions", [])
        if not sessions:
            raise RoutineNotFoundError("Routine has no sessions to advance.")

        current_index: int = int(cast(Any, routine).current_session_index or 0)
        current_session = sessions[current_index % len(sessions)]

        kcal_burned: float | None = None
        if action == "complete":
            from datetime import date as date_type
            workout_session = cls.log_session(
                db,
                user_id=user_id,
                session_id=str(current_session.get("id", "")),
                session_date=date_type.today(),
                skipped_exercise_ids=[],
                extra_exercises=[],
                weight_kg=weight_kg,
            )
            kcal_burned = float(getattr(workout_session, "total_kcal_est", 0.0) or 0.0)

        # Advance index (wraps around)
        next_index = (current_index + 1) % len(sessions)
        cast(Any, routine).current_session_index = next_index

        db.commit()

        next_session = sessions[next_index % len(sessions)]
        return {
            "action": action,
            "current_session_index": next_index,
            "next_session_title": next_session.get("title"),
            "kcal_burned": kcal_burned,
        }

    # ── Gemini calls ──────────────────────────────────────────────────────────

    @classmethod
    def _call_gemini_file(cls, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        """Send a file to Gemini and return parsed routine JSON."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RoutineParsingError("Gemini API key is not configured.")

        model = _normalize_model(settings.GEMINI_MODEL or "gemini-2.5-flash")
        url = f"{GEMINI_API_BASE_URL}/{model}:generateContent?key={api_key}"

        parts: list[dict[str, Any]] = []
        if mime_type == "text/plain":
            parts.append({"text": file_bytes.decode("utf-8", errors="replace")})
        else:
            encoded = base64.b64encode(file_bytes).decode("ascii")
            parts.append({"inlineData": {"mimeType": mime_type, "data": encoded}})
        parts.append({"text": ROUTINE_FILE_PARSE_PROMPT})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": RoutineConstants.GEMINI_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        return cls._execute_gemini_request(url, payload)

    @classmethod
    def _call_gemini_text(cls, prompt: str) -> dict[str, Any]:
        """Send a text-only prompt to Gemini and return parsed routine JSON."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RoutineParsingError("Gemini API key is not configured.")

        model = _normalize_model(settings.GEMINI_MODEL or "gemini-2.5-flash")
        url = f"{GEMINI_API_BASE_URL}/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": RoutineConstants.GEMINI_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        return cls._execute_gemini_request(url, payload)

    @classmethod
    def _execute_gemini_request(cls, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a Gemini API request and return parsed JSON."""
        try:
            with httpx.Client(timeout=RoutineConstants.GEMINI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RoutineParsingError(f"Gemini API request failed: {exc}") from exc

        return cls._extract_json_from_response(response.json())

    @classmethod
    def _extract_json_from_response(cls, response: dict[str, Any]) -> dict[str, Any]:
        """Extract and validate the JSON payload from Gemini response."""
        try:
            text = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RoutineParsingError("Unexpected Gemini response structure.") from exc

        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RoutineParsingError(f"Gemini returned invalid JSON: {exc}") from exc

        if not isinstance(data, dict) or "sessions" not in data:
            raise RoutineParsingError("Gemini response missing required 'sessions' field.")

        return data

    # ── HTML generation ───────────────────────────────────────────────────────

    @classmethod
    def _generate_html(cls, data: dict[str, Any]) -> str:
        """Build a self-contained HTML page with 3 built-in themes from parsed routine data."""
        title = data.get("title", "Mi Rutina")
        subtitle = data.get("subtitle", "")
        phases: list[dict[str, Any]] = data.get("phases", [])
        schedule: list[dict[str, Any]] = data.get("schedule", [])
        sessions: list[dict[str, Any]] = data.get("sessions", [])
        month_data: list[dict[str, Any]] = data.get("month_data", [])
        health_analysis: dict[str, Any] = data.get("health_analysis", {})

        # For old routines without month_data, build it from the first session's exercises
        if not month_data and sessions:
            first_ex = (sessions[0].get("exercises") or [{}])[0]
            month_data = [{
                "month": 1,
                "sets": first_ex.get("sets", "3 series"),
                "reps": first_ex.get("reps", "—"),
                "rest_seconds": first_ex.get("rest_seconds", 60),
                "note": "",
            }]

        multi_month = len(month_data) > 1
        month_data_json = json.dumps(month_data, ensure_ascii=False)
        routines_json = json.dumps([
            {
                "id": s.get("id"),
                "color": s.get("color", "#c8f55a"),
                "exercises": [
                    {"name": ex.get("name", ""), "muscle": ex.get("muscle", ""),
                     "group": ex.get("group", ""), "notes": ex.get("notes", "")}
                    for ex in s.get("exercises", [])
                ],
            }
            for s in sessions
        ], ensure_ascii=False)

        health_html = cls._build_health_analysis_html(health_analysis)
        phases_html = cls._build_phases_html(phases)
        schedule_html = cls._build_schedule_html(schedule, sessions)
        sessions_html = cls._build_sessions_html(sessions, month_data, multi_month)
        stylesheet = cls._build_routine_stylesheet()
        scripts = cls._build_routine_scripts(month_data_json, routines_json)

        return f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
{stylesheet}
</head>
<body>
<div class="container">
  <header>
    <p class="eyebrow">NovaFitness · Rutina personalizada</p>
    <h1>Mi <span>Rutina</span></h1>
    <p class="subtitle">{subtitle}</p>
  </header>
  {health_html}
  {phases_html}
  {schedule_html}
  <div id="routines">
    {sessions_html}
  </div>
  <footer>{title} · Generado por NovaFitness</footer>
</div>

<div class="theme-switcher">
  <button class="theme-btn active" id="btn-dark" onclick="setTheme('dark')" title="Tema oscuro">🌑</button>
  <button class="theme-btn" id="btn-original" onclick="setTheme('original')" title="Tema original">🟣</button>
  <button class="theme-btn" id="btn-light" onclick="setTheme('light')" title="Tema claro">☀️</button>
</div>

{scripts}
</body>
</html>"""

    @classmethod
    def _build_routine_stylesheet(cls) -> str:
        """Return the <style> block for the routine HTML document."""
        return """<style>
  /* ── Themes ── */
  :root {
    --bg: #0e0e0f; --card: #161618; --border: #2a2a2e;
    --text: #f0ede8; --muted: #7a7870; --accent: #c8f55a;
    --warning-bg: rgba(239,68,68,0.12); --warning-border: rgba(239,68,68,0.35); --warning-text: #fca5a5;
    --analysis-bg: rgba(200,245,90,0.06); --analysis-border: rgba(200,245,90,0.2);
  }
  [data-theme="original"] {
    --bg: #1a0a2e; --card: rgba(139,92,246,0.1); --border: rgba(139,92,246,0.25);
    --text: #f0ede8; --muted: rgba(240,237,232,0.55); --accent: #00f2c3;
    --warning-bg: rgba(239,68,68,0.15); --warning-border: rgba(239,68,68,0.4); --warning-text: #fca5a5;
    --analysis-bg: rgba(0,242,195,0.06); --analysis-border: rgba(0,242,195,0.2);
  }
  [data-theme="light"] {
    --bg: #e8feff; --card: rgba(255,255,255,0.85); --border: rgba(10,26,30,0.12);
    --text: #0a1a1e; --muted: rgba(10,26,30,0.52); --accent: #008a96;
    --warning-bg: rgba(239,68,68,0.08); --warning-border: rgba(239,68,68,0.3); --warning-text: #dc2626;
    --analysis-bg: rgba(0,138,150,0.06); --analysis-border: rgba(0,138,150,0.2);
  }

  /* ── Reset & Base ── */
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; padding: 40px 20px 100px; transition: background 0.3s, color 0.3s; }
  [data-theme="original"] body, html[data-theme="original"] { background: linear-gradient(135deg, #1a0a2e 0%, #2d1060 50%, #1a0a2e 100%); }

  .container { max-width: 860px; margin: 0 auto; }
  header { text-align: center; padding: 50px 0 40px; }
  .eyebrow { font-size: 11px; letter-spacing: 4px; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }
  h1 { font-family: 'Playfair Display', serif; font-size: clamp(2rem,6vw,3.5rem); font-weight: 900; line-height: 1.1; margin-bottom: 10px; }
  h1 span { color: var(--accent); }
  .subtitle { color: var(--muted); font-size: 14px; font-weight: 300; letter-spacing: 0.5px; }

  /* ── Health analysis ── */
  .health-analysis { background: var(--analysis-bg); border: 1px solid var(--analysis-border); border-radius: 12px; padding: 20px 24px; margin-bottom: 32px; }
  .health-analysis.has-warning { background: var(--warning-bg); border-color: var(--warning-border); }
  .health-title { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }
  .health-warning { color: var(--warning-text); font-weight: 600; font-size: 14px; margin-bottom: 12px; padding: 8px 12px; background: var(--warning-bg); border-radius: 8px; border-left: 3px solid var(--warning-border); }
  .health-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }
  .health-list li { font-size: 13px; color: var(--muted); padding-left: 16px; position: relative; }
  .health-list li::before { content: '·'; position: absolute; left: 4px; color: var(--accent); }

  /* ── Phases ── */
  .periodization { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 40px; }
  .phase { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; position: relative; overflow: hidden; }
  .phase::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
  .phase:nth-child(1)::before { background: #c8f55a; }
  .phase:nth-child(2)::before { background: #f5c85a; }
  .phase:nth-child(3)::before { background: #f55a8a; }
  .phase:nth-child(n+4)::before { background: #5af0f5; }
  .phase-num { font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
  .phase-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; }
  .phase-detail { font-size: 12px; color: var(--muted); line-height: 1.7; }
  .phase-detail strong { color: var(--text); font-weight: 500; }

  /* ── Schedule grid ── */
  .week-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin-bottom: 40px; }
  .week-day { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 10px; text-align: center; }
  .day-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
  .day-name { font-family: 'Playfair Display', serif; font-size: 0.95rem; font-weight: 700; margin-bottom: 4px; }
  .day-tag { display: inline-block; font-size: 9px; letter-spacing: 1px; text-transform: uppercase; padding: 3px 8px; border-radius: 20px; font-weight: 500; margin-top: 4px; }

  /* ── Session blocks ── */
  .routine-block { background: var(--card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 16px; overflow: hidden; }
  .routine-header { padding: 20px 24px; display: flex; align-items: center; gap: 14px; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; }
  .routine-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .routine-header-text { flex: 1; }
  .routine-day-label { font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
  .routine-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; }
  .chevron { width: 18px; height: 18px; color: var(--muted); transition: transform 0.3s ease; flex-shrink: 0; }
  .routine-block.open .chevron { transform: rotate(180deg); }
  .exercises-table { display: none; padding: 0 24px 20px; }
  .routine-block.open .exercises-table { display: block; }
  .exercise-row { display: grid; grid-template-columns: 24px 1fr auto auto; align-items: start; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
  [data-theme="light"] .exercise-row { border-bottom-color: rgba(10,26,30,0.06); }
  .exercise-row:last-child { border-bottom: none; }
  .ex-num { font-size: 11px; color: var(--muted); font-weight: 500; text-align: center; padding-top: 2px; }
  .ex-name { font-size: 14px; font-weight: 500; }
  .ex-muscle { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .ex-notes { font-size: 11px; color: var(--muted); margin-top: 3px; font-style: italic; }
  .ex-badge { font-size: 10px; padding: 3px 10px; border-radius: 20px; white-space: nowrap; font-weight: 500; align-self: start; margin-top: 2px; }
  .ex-sets { text-align: right; white-space: nowrap; }
  .sets-num { font-size: 13px; font-weight: 600; }
  .sets-label { font-size: 10px; color: var(--muted); }

  /* ── Month tabs ── */
  .month-tabs { display: flex; gap: 8px; flex-wrap: wrap; padding: 20px 0 16px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
  .month-tab { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; transition: all 0.2s; font-family: 'DM Sans', sans-serif; }
  .month-tab:hover { color: var(--text); border-color: var(--text); }
  .month-tab.active { color: var(--text); border-color: currentColor; }
  .month-tab[data-month="1"].active { border-color: #c8f55a; color: #c8f55a; }
  .month-tab[data-month="2"].active { border-color: #f5c85a; color: #f5c85a; }
  .month-tab[data-month="3"].active { border-color: #f55a8a; color: #f55a8a; }
  .month-tab[data-month="4"].active { border-color: #5af0f5; color: #5af0f5; }
  .exercises-list { transition: opacity 0.2s, transform 0.2s; }
  .month-note { background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; font-size: 12px; color: var(--muted); line-height: 1.6; margin-top: 16px; }
  [data-theme="light"] .month-note { background: rgba(10,26,30,0.03); }
  .month-note strong { color: var(--text); }

  /* ── Theme switcher ── */
  .theme-switcher {
    position: fixed; bottom: 24px; right: 24px;
    display: flex; gap: 8px; z-index: 100;
  }
  .theme-btn {
    width: 36px; height: 36px; border-radius: 50%; border: 2px solid var(--border);
    cursor: pointer; transition: transform 0.2s, border-color 0.2s;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; background: var(--card);
  }
  .theme-btn:hover { transform: scale(1.15); border-color: var(--accent); }
  .theme-btn.active { border-color: var(--accent); box-shadow: 0 0 10px rgba(200,245,90,0.3); }

  /* ── Footer ── */
  footer { text-align: center; padding-top: 40px; font-size: 12px; color: var(--muted); }

  /* ── Animations ── */
  @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
  header { animation: fadeUp 0.6s ease both; }
  .health-analysis { animation: fadeUp 0.6s 0.1s ease both; }
  .periodization { animation: fadeUp 0.6s 0.15s ease both; }
  .week-grid { animation: fadeUp 0.6s 0.2s ease both; }

  @media (max-width: 600px) {
    .exercise-row { grid-template-columns: 20px 1fr auto; }
    .ex-badge { display: none; }
    body { padding: 24px 14px 100px; }
  }
</style>"""

    @classmethod
    def _build_routine_scripts(cls, month_data_json: str, routines_json: str) -> str:
        """Return the <script> block with session/month data injected."""
        return (
            """<script>
  // ── Theme switcher ───────────────────────────────────────────────────────────
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + t).classList.add('active');
    localStorage.setItem('nova-routine-theme', t);
  }
  (function() {
    const saved = localStorage.getItem('nova-routine-theme');
    if (saved) setTheme(saved);
  })();

  // ── Session toggle ───────────────────────────────────────────────────────────
  function toggle(block) { block.classList.toggle('open'); }

  // ── Month tabs ───────────────────────────────────────────────────────────────
  const NOVA_MONTH_DATA = __MONTH_DATA__;
  const NOVA_ROUTINES   = __ROUTINES__;

  const GROUP_COLORS = {
    'Espalda':'#c8f55a','Tríceps':'#a8e040','Cuádricep':'#f5c85a','Cuádriceps':'#f5c85a',
    'Glúteo':'#f0a030','Pecho':'#f55a8a','Hombro':'#e03070','Bíceps':'#c03060',
    'Isquio':'#5af0f5','Isquiotibiales':'#5af0f5','Espalda baja':'#40d0d5',
    'Gemelos':'#8a7af5','Aductores':'#f5a05a','Core':'#fb923c','Cardio':'#a78bfa',
  };

  function renderExercises(routineId, month) {
    const r = NOVA_ROUTINES.find(x => x.id === routineId);
    const m = NOVA_MONTH_DATA.find(x => x.month === month) || NOVA_MONTH_DATA[0];
    if (!r || !m) return '';
    return r.exercises.map((ex, i) => {
      const color = GROUP_COLORS[ex.group] || r.color || '#888';
      const notesHtml = ex.notes ? `<p class="ex-notes">💡 ${ex.notes}</p>` : '';
      return `
        <div class="exercise-row">
          <span class="ex-num">${i + 1}</span>
          <div>
            <p class="ex-name">${ex.name}</p>
            <p class="ex-muscle">${ex.muscle}</p>
            ${notesHtml}
          </div>
          <span class="ex-badge" style="background:${color}22; color:${color}">${ex.group}</span>
          <div class="ex-sets">
            <p class="sets-num">${m.sets}</p>
            <p class="sets-label">${m.reps}</p>
          </div>
        </div>`;
    }).join('');
  }

  function switchMonth(btn, routineId) {
    const tabs = btn.closest('.month-tabs').querySelectorAll('.month-tab');
    tabs.forEach(t => t.classList.remove('active'));
    btn.classList.add('active');

    const month = parseInt(btn.dataset.month);
    const m = NOVA_MONTH_DATA.find(x => x.month === month) || NOVA_MONTH_DATA[0];
    const list = document.querySelector(`.exercises-list[data-routine="${routineId}"]`);
    const note = document.querySelector(`.month-note[data-note="${routineId}"]`);

    list.style.opacity = '0';
    list.style.transform = 'translateY(6px)';
    setTimeout(() => {
      list.innerHTML = renderExercises(routineId, month);
      if (note && m) note.innerHTML = m.note || '';
      list.style.opacity = '1';
      list.style.transform = 'translateY(0)';
    }, 150);
  }
</script>"""
            .replace("__MONTH_DATA__", month_data_json)
            .replace("__ROUTINES__", routines_json)
        )

    @classmethod
    def _build_health_analysis_html(cls, analysis: dict[str, Any]) -> str:
        if not analysis:
            return ""

        warning = analysis.get("warning")
        conditions = analysis.get("conditions_detected", [])
        contraindications = analysis.get("contraindications_applied", [])
        adaptations = analysis.get("adaptations", [])

        warning_html = (
            f'<p class="health-warning">⚠️ {warning}</p>'
            if warning else ""
        )
        has_warning_class = " has-warning" if warning else ""

        def make_list(items: list[str], label: str) -> str:
            if not items:
                return ""
            lis = "".join(f"<li>{item}</li>" for item in items)
            return f'<p class="health-title" style="margin-top:12px">{label}</p><ul class="health-list">{lis}</ul>'

        conditions_html = make_list(conditions, "Condiciones detectadas")
        contra_html = make_list(contraindications, "Contraindicaciones aplicadas")
        adapt_html = make_list(adaptations, "Adaptaciones realizadas")

        if not (warning or conditions or contraindications or adaptations):
            return ""

        return f"""<div class="health-analysis{has_warning_class}">
  <p class="health-title">Análisis de salud · Personal Trainer</p>
  {warning_html}
  {conditions_html}
  {contra_html}
  {adapt_html}
</div>"""

    @classmethod
    def _build_phases_html(cls, phases: list[dict[str, Any]]) -> str:
        if not phases:
            return ""
        items = ""
        for p in phases:
            items += f"""
    <div class="phase">
      <p class="phase-num">{p.get('number', '')}</p>
      <p class="phase-title">{p.get('title', '')}</p>
      <p class="phase-detail">
        <strong>Series/Reps:</strong> {p.get('sets_reps', '')}<br>
        <strong>Peso:</strong> {p.get('weight', '')}<br>
        <strong>Foco:</strong> {p.get('focus', '')}
      </p>
    </div>"""
        return f'<div class="periodization">{items}\n</div>'

    @classmethod
    def _build_schedule_html(
        cls,
        schedule: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
    ) -> str:
        if not schedule:
            return ""
        color_map: dict[str, str] = {}
        for s in sessions:
            label = s.get("label", "")
            color_map[label] = s.get("color", "#c8f55a")

        items = ""
        for entry in schedule:
            label = entry.get("label", "")
            color = color_map.get(label, "#c8f55a")
            is_rest = label.lower() in ("descanso", "rest", "")
            tag_style = (
                'background:rgba(120,120,120,0.12); color:var(--muted)'
                if is_rest
                else f"background:{color}22; color:{color}"
            )
            items += f"""
    <div class="week-day">
      <p class="day-label">{entry.get('day', '')}</p>
      <p class="day-name">{label or 'Descanso'}</p>
      <span class="day-tag" style="{tag_style}">{entry.get('focus', 'Recuperación')}</span>
    </div>"""
        return f'<div class="week-grid">{items}\n</div>'

    @classmethod
    def _build_sessions_html(
        cls,
        sessions: list[dict[str, Any]],
        month_data: list[dict[str, Any]],
        multi_month: bool,
    ) -> str:
        """Build collapsible session blocks, with month tabs if the routine spans multiple months."""
        phase_tab_labels = ["Adaptación", "Fuerza", "Negativa", "Pico"]
        blocks = ""
        for i, s in enumerate(sessions):
            sid = s.get("id", f"session_{i}")
            color = s.get("color", "#c8f55a")
            open_class = " open" if i == 0 else ""

            if multi_month:
                # Build month tabs
                tabs_html = ""
                for md in month_data:
                    m = md.get("month", 1)
                    phase_label = phase_tab_labels[m - 1] if m <= len(phase_tab_labels) else f"Mes {m}"
                    active = " active" if m == 1 else ""
                    tabs_html += f'<button class="month-tab{active}" data-month="{m}" onclick="switchMonth(this, \'{sid}\')">{md.get("number", f"Mes {m}")} · {phase_label}</button>\n'

                first_md = month_data[0]
                exercises_inner = cls._build_exercises_html(s.get("exercises", []), color, first_md)
                first_note = first_md.get("note", "")
                note_html = f'<div class="month-note" data-note="{sid}">{first_note}</div>' if first_note else ""

                inner_html = f"""
      <div class="month-tabs">
        {tabs_html}
      </div>
      <div class="exercises-list" data-routine="{sid}">
        {exercises_inner}
      </div>
      {note_html}"""
            else:
                first_md = month_data[0] if month_data else {}
                inner_html = cls._build_exercises_html(s.get("exercises", []), color, first_md)

            blocks += f"""
  <div class="routine-block{open_class}">
    <div class="routine-header" onclick="toggle(this.closest('.routine-block'))">
      <div class="routine-dot" style="background:{color}"></div>
      <div class="routine-header-text">
        <p class="routine-day-label">{s.get('day_label', '')}</p>
        <p class="routine-title">{s.get('title', '')}</p>
      </div>
      <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    <div class="exercises-table">
      {inner_html}
    </div>
  </div>"""
        return blocks

    @classmethod
    def _build_exercises_html(
        cls,
        exercises: list[dict[str, Any]],
        color: str,
        month_data: dict[str, Any],
    ) -> str:
        """Render exercise rows using sets/reps from the given month_data entry."""
        sets = month_data.get("sets", "—")
        reps = month_data.get("reps", "—")
        rows = ""
        for i, ex in enumerate(exercises, start=1):
            group = ex.get("group", "")
            notes = ex.get("notes", "")
            notes_html = f'<p class="ex-notes">💡 {notes}</p>' if notes else ""
            rows += f"""
      <div class="exercise-row">
        <span class="ex-num">{i}</span>
        <div>
          <p class="ex-name">{ex.get('name', '')}</p>
          <p class="ex-muscle">{ex.get('muscle', '')}</p>
          {notes_html}
        </div>
        <span class="ex-badge" style="background:{color}22; color:{color}">{group}</span>
        <div class="ex-sets">
          <p class="sets-num">{sets}</p>
          <p class="sets-label">{reps}</p>
        </div>
      </div>"""
        return rows

    # ── DB helpers ────────────────────────────────────────────────────────────

    @classmethod
    def _upsert_routine(
        cls,
        db: Session,
        *,
        user_id: int,
        filename: str,
        source_type: str,
        status: str,
        intake_data: dict[str, Any] | None = None,
    ) -> UserRoutine:
        """Create or replace the user's routine record."""
        routine = (
            db.query(UserRoutine)
            .filter(UserRoutine.user_id == user_id)
            .first()
        )
        if routine is None:
            routine = UserRoutine(user_id=user_id)
            db.add(routine)

        rd = cast(Any, routine)
        rd.source_filename = filename
        rd.source_type = source_type
        rd.status = status
        rd.html_content = None
        rd.routine_data = None
        rd.health_analysis = None
        rd.intake_data = intake_data
        rd.error_message = None
        rd.current_session_index = 0  # reset progress when a new routine is loaded
        return routine


def _normalize_model(model_name: str) -> str:
    """Strip 'models/' prefix and version suffix from Gemini model name."""
    name = (model_name or "").strip().strip("/")
    if name.lower().startswith("models/"):
        name = name[len("models/"):]
    if ":" in name:
        name = name.split(":", 1)[0]
    return name.lower()

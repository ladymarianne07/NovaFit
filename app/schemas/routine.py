"""Schemas for the routine upload, AI generation, editing, and session log module."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Intake form ───────────────────────────────────────────────────────────────

class RoutineIntakeData(BaseModel):
    """Health and preference data collected before generating an AI routine."""

    duration_months: int = Field(
        ...,
        ge=1,
        le=3,
        description="How many months the routine should last (1–3)",
    )
    health_conditions: str = Field(
        ...,
        description="Medical conditions, diseases, or health limitations. Use 'ninguna' if none.",
    )
    medications: str = Field(
        default="",
        description="Current medications that may affect training",
    )
    injuries: str = Field(
        default="",
        description="Current or recent injuries and their status",
    )
    preferred_exercises: str = Field(
        default="",
        description="Exercise types or specific movements the user enjoys",
    )
    frequency_days: str = Field(
        default="3-4",
        description="Training days per week: '2' | '3-4' | '5+'",
    )
    experience_level: str = Field(
        default="principiante",
        description="'principiante' | 'intermedio' | 'avanzado'",
    )
    equipment: str = Field(
        default="gimnasio completo",
        description="'gimnasio completo' | 'mancuernas en casa' | 'bandas elásticas' | 'peso corporal'",
    )
    session_duration_minutes: int = Field(
        default=60,
        ge=20,
        le=180,
        description="Target duration per session in minutes",
    )


# ── Generation request ────────────────────────────────────────────────────────

class RoutineGenerateRequest(BaseModel):
    """Request to generate a routine from text + health intake form."""

    intake: RoutineIntakeData
    free_text: str = Field(
        default="",
        description="Optional free-text description from the user about goals or preferences",
    )


# ── Edit request ──────────────────────────────────────────────────────────────

class RoutineEditRequest(BaseModel):
    """Request to modify an existing AI-generated routine."""

    edit_instruction: str = Field(
        ...,
        min_length=5,
        description="Plain-language instruction describing what to change in the routine",
    )


# ── Sub-schemas ───────────────────────────────────────────────────────────────

class RoutineExercise(BaseModel):
    """Single exercise within a routine session."""

    id: str
    name: str
    muscle: str
    group: str


class RoutineSession(BaseModel):
    """One training day/session within the routine."""

    id: str
    day: str = ""
    label: str = ""
    day_label: str = ""
    title: str
    color: str = "#c8f55a"
    session_duration_minutes: int = 60
    exercises: list[RoutineExercise]


class RoutineHealthAnalysis(BaseModel):
    """Summary produced by the AI personal trainer before generating exercises."""

    conditions_detected: list[str] = []
    contraindications_applied: list[str] = []
    adaptations: list[str] = []
    warning: str | None = None


# ── Response ──────────────────────────────────────────────────────────────────

class UserRoutineResponse(BaseModel):
    """Response with the user's active routine."""

    id: int
    status: str
    source_filename: str | None = None
    source_type: str | None = None
    html_content: str | None = None
    routine_data: dict[str, Any] | None = None
    health_analysis: dict[str, Any] | None = None
    intake_data: dict[str, Any] | None = None
    error_message: str | None = None
    current_session_index: int = 0

    model_config = {"from_attributes": True}


# ── Advance session ───────────────────────────────────────────────────────────

class RoutineAdvanceSessionRequest(BaseModel):
    """Request to advance the routine to the next session (complete or skip)."""

    action: Literal["complete", "skip"] = Field(..., description="'complete' | 'skip'")


class AdvanceSessionResponse(BaseModel):
    """Lightweight response after advancing a routine session."""

    action: str
    current_session_index: int
    next_session_title: str | None = None
    kcal_burned: float | None = None


# ── Session log ───────────────────────────────────────────────────────────────

EXTRA_EXERCISE_MET: dict[str, float] = {
    "resistance": 4.5,
    "cardio_moderate": 7.0,
    "cardio_high": 9.5,
    "hiit": 8.5,
    "yoga": 2.5,
    "walking": 3.5,
}


class ExtraExercise(BaseModel):
    """An exercise added on top of the routine session."""

    name: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=1, le=180)
    exercise_type: str = Field(
        default="resistance",
        description="'resistance' | 'cardio_moderate' | 'cardio_high' | 'hiit' | 'yoga' | 'walking'",
    )

    def kcal(self, weight_kg: float) -> float:
        met = EXTRA_EXERCISE_MET.get(self.exercise_type, 4.5)
        return round(met * weight_kg * (self.duration_minutes / 60.0), 2)


class RoutineLogSessionRequest(BaseModel):
    """Request to log a completed routine session."""

    session_id: str = Field(..., min_length=1, description="Session id from routine_data.sessions")
    session_date: date
    skipped_exercise_ids: list[str] = Field(
        default_factory=list,
        description="Exercise ids the user did NOT complete",
    )
    extra_exercises: list[ExtraExercise] = Field(
        default_factory=list,
        description="Additional exercises done on top of the routine session",
    )

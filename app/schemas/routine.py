"""Schemas for the routine upload, AI generation, editing, and session log module."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


# ── Intake form ───────────────────────────────────────────────────────────────

class RoutineIntakeData(BaseModel):
    """Health and preference data collected before generating an AI routine."""

    objective: str = Field(
        ...,
        description="'fat_loss' | 'body_recomp' | 'muscle_gain'",
    )
    duration_months: int = Field(
        ...,
        ge=1,
        le=12,
        description="How many months the routine should last",
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
    estimated_calories: float


class RoutineSession(BaseModel):
    """One training day/session within the routine."""

    id: str
    day: str = ""
    label: str = ""
    day_label: str = ""
    title: str
    color: str = "#c8f55a"
    estimated_calories_per_session: float
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

    model_config = {"from_attributes": True}


# ── Session log ───────────────────────────────────────────────────────────────

class RoutineLogSessionRequest(BaseModel):
    """Request to log a completed routine session."""

    session_id: str = Field(..., min_length=1, description="Session id from routine_data.sessions")
    session_date: date
    skipped_exercise_ids: list[str] = Field(
        default_factory=list,
        description="Exercise ids the user did NOT complete",
    )

"""Workout schemas for MET-based session creation and daily energy retrieval."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class WorkoutSessionBlockCreate(BaseModel):
    """Input payload for a workout activity block."""

    activity: str = Field(..., min_length=1, max_length=150)
    duration_minutes: int = Field(..., ge=1, le=1440)
    intensity: str | None = Field(default=None, max_length=120)


class WorkoutSessionCreate(BaseModel):
    """Input payload for workout session creation."""

    session_date: date
    source: str = Field(default="ai", min_length=2, max_length=20)
    status: str = Field(default="final", min_length=2, max_length=20)
    raw_input: str | None = None
    ai_output: dict[str, Any] | None = None
    weight_kg: float | None = Field(default=None, gt=0)
    blocks: list[WorkoutSessionBlockCreate] = Field(..., min_length=1)


class WorkoutSessionBlockResponse(BaseModel):
    """Persisted workout block with calculated metrics."""

    id: int
    block_order: int
    activity_id: int
    duration_minutes: int
    intensity_level: str | None
    intensity_raw: str | None
    weight_kg_used: float | None
    met_used_min: float | None
    met_used_max: float | None
    correction_factor: float
    kcal_min: float | None
    kcal_max: float | None
    kcal_est: float | None

    model_config = {"from_attributes": True}


class WorkoutSessionResponse(BaseModel):
    """Workout session response with totals and blocks."""

    id: int
    user_id: int
    session_date: date
    source: str
    status: str
    total_kcal_min: float | None
    total_kcal_max: float | None
    total_kcal_est: float | None
    blocks: list[WorkoutSessionBlockResponse]

    model_config = {"from_attributes": True}


class DailyEnergyResponse(BaseModel):
    """Daily energy totals combining intake and exercise expenditure."""

    user_id: int
    log_date: date
    exercise_kcal_min: float
    exercise_kcal_max: float
    exercise_kcal_est: float
    intake_kcal: float
    net_kcal_est: float

    model_config = {"from_attributes": True}

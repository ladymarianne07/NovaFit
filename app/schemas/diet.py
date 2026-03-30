"""Schemas for the AI diet plan generation and editing module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Intake form ───────────────────────────────────────────────────────────────

class DietIntakeData(BaseModel):
    """Health and preference data collected before generating an AI diet plan."""

    meals_count: int = Field(
        default=5,
        ge=3,
        le=8,
        description="Number of meals per day (3–8)",
    )
    dietary_restrictions: str = Field(
        default="ninguna",
        description="Dietary restrictions (vegetarian, vegan, gluten-free, etc.). Use 'ninguna' if none.",
    )
    food_allergies: str = Field(
        default="ninguna",
        description="Food allergies or intolerances. Use 'ninguna' if none.",
    )
    health_conditions: str = Field(
        default="ninguna",
        description="Medical conditions relevant to nutrition (diabetes, hypertension, etc.). Use 'ninguna' if none.",
    )
    disliked_foods: str = Field(
        default="",
        description="Foods the user dislikes or refuses to eat.",
    )
    budget_level: str = Field(
        default="moderado",
        description="'económico' | 'moderado' | 'sin límite'",
    )
    cooking_time: str = Field(
        default="moderado",
        description="'mínimo (platos rápidos)' | 'moderado (30-45 min)' | 'sin límite'",
    )
    meal_timing_preference: str = Field(
        default="",
        description="Preferred meal times or schedule (e.g., 'desayuno a las 7, almuerzo a las 13').",
    )


# ── Generation request ────────────────────────────────────────────────────────

class DietGenerateRequest(BaseModel):
    """Request to generate a personalized diet plan via AI."""

    intake: DietIntakeData
    free_text: str = Field(
        default="",
        description="Free-text description from the user about food preferences, schedule, lifestyle, etc.",
    )


# ── Edit request ──────────────────────────────────────────────────────────────

class DietEditRequest(BaseModel):
    """Request to modify an existing AI-generated diet plan."""

    edit_instruction: str = Field(
        ...,
        min_length=5,
        description="Plain-language instruction describing what to change in the diet plan",
    )


# ── Sub-schemas ───────────────────────────────────────────────────────────────

class DietFood(BaseModel):
    """A single food item within a meal."""

    name: str
    portion: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    notes: str = ""


class DietMeal(BaseModel):
    """One meal within a diet day."""

    id: str
    name: str
    time: str = ""
    foods: list[DietFood]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    notes: str = ""


class DietDay(BaseModel):
    """A full day of eating (training or rest)."""

    day_type: str  # 'training' | 'rest'
    label: str
    meals: list[DietMeal]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    water_ml: int
    notes: str = ""


# ── Response ──────────────────────────────────────────────────────────────────

class UserDietResponse(BaseModel):
    """Response with the user's active diet plan."""

    id: int
    status: str
    source_type: str | None = None
    html_content: str | None = None
    diet_data: dict[str, Any] | None = None
    intake_data: dict[str, Any] | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}

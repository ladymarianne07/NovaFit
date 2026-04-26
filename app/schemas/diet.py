"""Schemas for the AI diet plan generation and editing module."""

from __future__ import annotations

from typing import Any, Literal

from datetime import date as date_type

from pydantic import BaseModel, Field, field_validator


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
    training_days: list[str] = Field(
        default_factory=list,
        description="Days of the week the user trains (e.g. ['lunes','miércoles','viernes']). Empty = single-day plan.",
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
    current_meal_index: int = 0
    current_meal_date: str | None = None
    daily_consumed: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @field_validator("current_meal_date", mode="before")
    @classmethod
    def coerce_date_to_str(cls, v: Any) -> str | None:
        """SQLAlchemy Date columns return datetime.date — coerce to ISO string."""
        if isinstance(v, date_type):
            return v.isoformat()
        return v


# ── Meal tracker ──────────────────────────────────────────────────────────────

class DietLogMealRequest(BaseModel):
    """Mark the current planned meal as complete or skipped, advancing the tracker index."""

    action: Literal["complete", "skip"] = Field(..., description="'complete' | 'skip'")


class DietLogMealResponse(BaseModel):
    """Result after logging a meal action."""

    current_meal_index: int
    current_meal_date: str | None = None
    advanced: bool


class DietModifyMealRequest(BaseModel):
    """Add or remove a food item from a specific meal."""

    day_type: str = Field(..., description="'training_day' | 'rest_day'")
    meal_id: str = Field(..., description="Meal id from diet_data (e.g. 'breakfast')")
    action: Literal["add_food", "remove_food"] = Field(..., description="'add_food' | 'remove_food'")
    food: DietFood | None = None        # Required for add_food
    food_index: int | None = None       # Required for remove_food


class CurrentMealResponse(BaseModel):
    """The current planned meal based on today's day type and tracker index."""

    day_type: str  # 'training_day' | 'rest_day'
    meal: dict[str, Any] | None = None
    meal_index: int
    total_meals: int
    is_last_meal: bool
    is_overridden: bool = False


class MealAlternativeResponse(BaseModel):
    """An AI-generated alternative meal for the current planned meal."""

    meal: DietMeal
    day_type: str
    meal_index: int


class ApplyAlternativeRequest(BaseModel):
    """Apply a meal alternative — either permanently to the diet or just for today (24 h)."""

    meal_index: int
    day_type: str = Field(..., description="'training_day' | 'rest_day'")
    scope: str = Field(..., description="'diet' (permanent) | 'today' (24 h override)")
    meal: DietMeal

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FoodParseRequest(BaseModel):
    """Incoming request payload for parse-and-calculate endpoint."""

    text: str = Field(..., min_length=3, max_length=3000)


class ParsedFoodPayload(BaseModel):
    """Strict payload expected from AI parser component."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)


class FoodParseCalculateResponse(BaseModel):
    """Response with calculated calories and macronutrients."""

    food: str
    quantity_grams: float
    calories_per_100g: float
    carbs_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float


class FoodItemDistributionResponse(BaseModel):
    """Nutrition distribution for one parsed food item."""

    food: str
    quantity_grams: float
    calories_per_100g: float
    carbs_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float


class ParsedMealResponse(BaseModel):
    """One detected meal (breakfast/lunch/dinner/snack) with itemized nutrition."""

    meal_type: str
    meal_label: str
    meal_timestamp: datetime
    items: list[FoodItemDistributionResponse]
    total_quantity_grams: float
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float


class FoodParseLogResponse(BaseModel):
    """Meal-separated parsing and logging response with global totals."""

    meals: list[ParsedMealResponse]
    total_quantity_grams: float
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float


class FoodEntryResponse(BaseModel):
    """Food entry database response schema."""

    id: int
    original_text: str
    normalized_name: str
    quantity_grams: float
    usda_fdc_id: str
    calories_per_100g: float
    total_calories: float
    created_at: datetime

    class Config:
        from_attributes = True

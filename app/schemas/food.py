from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FoodParseRequest(BaseModel):
    """Incoming request payload for parse-and-calculate endpoint."""

    text: str = Field(..., min_length=3, max_length=3000)


class ParsedFoodPayload(BaseModel):
    """Payload produced by AI parser. Unknown fields are silently ignored."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    is_supplement: bool = False


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


class ConfirmedFoodItem(BaseModel):
    """One food item submitted by the user after reviewing the AI preview."""

    meal_type: str = Field(..., min_length=1, max_length=50)
    meal_label: str = Field(..., min_length=1, max_length=100)
    food_name: str = Field(..., min_length=1, max_length=200)
    quantity_grams: float = Field(..., gt=0)
    calories_per_100g: float = Field(..., ge=0)
    carbs_per_100g: float = Field(..., ge=0)
    protein_per_100g: float = Field(..., ge=0)
    fat_per_100g: float = Field(..., ge=0)
    is_supplement: bool = False


class ConfirmedMealsRequest(BaseModel):
    """Payload for the confirm-and-log endpoint."""

    items: list[ConfirmedFoodItem] = Field(..., min_length=1)


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

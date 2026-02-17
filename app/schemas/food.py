from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FoodParseRequest(BaseModel):
    """Incoming request payload for parse-and-calculate endpoint."""

    text: str = Field(..., min_length=3, max_length=500)


class ParsedFoodPayload(BaseModel):
    """Strict payload expected from AI parser component."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)


class FoodParseCalculateResponse(BaseModel):
    """Response with calculated calories."""

    food: str
    quantity_grams: float
    calories_per_100g: float
    total_calories: float


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

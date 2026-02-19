from typing import Optional

from pydantic import BaseModel, Field


class FoodNormalized(BaseModel):
    """Unified normalized food payload used across all external connectors."""

    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(default=None, max_length=255)
    calories_per_100g: float = Field(..., ge=0)
    protein_per_100g: float = Field(..., ge=0)
    fat_per_100g: float = Field(..., ge=0)
    carbs_per_100g: float = Field(..., ge=0)
    fiber_per_100g: Optional[float] = Field(default=None, ge=0)
    source: str = Field(..., min_length=1, max_length=50)
    confidence_score: float = Field(..., ge=0, le=1)

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from ..constants import SkinfoldConstants


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class SkinfoldValues(BaseModel):
    chest_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    midaxillary_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    triceps_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    subscapular_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    abdomen_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    suprailiac_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)
    thigh_mm: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_SKINFOLD_MM, le=SkinfoldConstants.MAX_SKINFOLD_MM)


class SkinfoldCalculationRequest(SkinfoldValues):
    sex: Sex
    age_years: int = Field(..., ge=SkinfoldConstants.MIN_AGE, le=SkinfoldConstants.MAX_AGE)
    weight_kg: Optional[float] = Field(None, ge=SkinfoldConstants.MIN_WEIGHT_KG, le=SkinfoldConstants.MAX_WEIGHT_KG)
    measurement_unit: str = Field(default="mm")

    @model_validator(mode="after")
    def validate_unit(self):
        if self.measurement_unit != "mm":
            raise ValueError("measurement_unit must be 'mm'")
        return self


class SkinfoldAIParseRequest(BaseModel):
    text: str = Field(..., min_length=3)


class SkinfoldCalculationResponse(BaseModel):
    method: str
    measured_at: datetime
    sum_of_skinfolds_mm: float
    body_density: float
    body_fat_percent: float
    fat_free_mass_percent: float
    fat_mass_kg: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    warnings: list[str]


class SkinfoldAIParseResponse(BaseModel):
    parsed: SkinfoldValues
    warnings: list[str]


class SkinfoldHistoryItem(SkinfoldCalculationResponse):
    id: int

    model_config = {"from_attributes": True}

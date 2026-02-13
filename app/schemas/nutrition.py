from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class MacronutrientBase(BaseModel):
    """Base macronutrient data"""
    carbs: float = Field(ge=0, description="Carbohydrates in grams")
    protein: float = Field(ge=0, description="Protein in grams")  
    fat: float = Field(ge=0, description="Fat in grams")


class MacronutrientTargets(MacronutrientBase):
    """Daily macronutrient targets"""
    pass


class MacronutrientCreate(MacronutrientBase):
    """Create/Update macronutrient consumption"""
    pass


class MacronutrientResponse(MacronutrientBase):
    """Macronutrient consumption with progress"""
    carbs_target: float
    protein_target: float
    fat_target: float
    
    carbs_percentage: float = Field(description="Percentage of carbs target consumed")
    protein_percentage: float = Field(description="Percentage of protein target consumed") 
    fat_percentage: float = Field(description="Percentage of fat target consumed")
    
    total_calories: float = Field(description="Total calories from macros")
    calories_target: float = Field(description="Target calories for the day")
    calories_percentage: float = Field(description="Percentage of calorie target consumed")
    
    class Config:
        from_attributes = True


class DailyNutritionBase(BaseModel):
    """Base daily nutrition schema"""
    date: date
    carbs_consumed: float = Field(default=0.0, ge=0)
    protein_consumed: float = Field(default=0.0, ge=0)
    fat_consumed: float = Field(default=0.0, ge=0)


class DailyNutritionCreate(DailyNutritionBase):
    """Create daily nutrition record"""
    pass


class DailyNutritionUpdate(BaseModel):
    """Update daily nutrition consumption"""
    carbs_consumed: Optional[float] = Field(None, ge=0)
    protein_consumed: Optional[float] = Field(None, ge=0)
    fat_consumed: Optional[float] = Field(None, ge=0)


class DailyNutritionResponse(DailyNutritionBase):
    """Daily nutrition with calculated fields"""
    id: int
    user_id: int
    
    carbs_target: float
    protein_target: float
    fat_target: float
    
    total_calories: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FoodItemBase(BaseModel):
    """Base food item for meal logging"""
    name: str = Field(..., min_length=1, max_length=200)
    calories_per_100g: float = Field(ge=0, description="Calories per 100g")
    carbs_per_100g: float = Field(ge=0, description="Carbs per 100g")
    protein_per_100g: float = Field(ge=0, description="Protein per 100g")  
    fat_per_100g: float = Field(ge=0, description="Fat per 100g")


class MealLogCreate(BaseModel):
    """Create meal log entry"""
    food_name: str = Field(..., min_length=1, max_length=200)
    quantity_grams: float = Field(gt=0, description="Quantity consumed in grams")
    
    # Nutritional info per 100g
    calories_per_100g: float = Field(ge=0)
    carbs_per_100g: float = Field(ge=0)
    protein_per_100g: float = Field(ge=0)
    fat_per_100g: float = Field(ge=0)


class MealLogResponse(MealLogCreate):
    """Meal log with calculated nutritional values"""
    id: int
    user_id: int
    
    # Calculated nutritional values for the consumed quantity
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float
    
    event_timestamp: datetime
    
    class Config:
        from_attributes = True
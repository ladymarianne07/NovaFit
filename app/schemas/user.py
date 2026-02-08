from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from ..constants import DatabaseConstants, BiometricConstants


class Gender(str, Enum):
    """Gender options for biometric calculations"""
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(float, Enum):
    """Activity level multipliers for caloric expenditure"""
    SEDENTARY = 1.20          # Sedentario real
    LIGHTLY_ACTIVE = 1.35     # Ligeramente activo
    MODERATELY_ACTIVE = 1.50  # Moderadamente activo
    ACTIVE = 1.65             # Activo
    VERY_ACTIVE = 1.80        # Muy activo


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserBiometrics(BaseModel):
    """Biometric data for caloric calculations - all fields required"""
    age: int = Field(
        ..., 
        ge=BiometricConstants.MIN_AGE, 
        le=BiometricConstants.MAX_AGE, 
        description="Age in years (required)"
    )
    gender: Gender = Field(..., description="Gender for BMR calculation (required)")
    weight: float = Field(
        ..., 
        ge=BiometricConstants.MIN_WEIGHT, 
        le=BiometricConstants.MAX_WEIGHT, 
        description="Weight in kg (required)"
    )
    height: float = Field(
        ..., 
        ge=BiometricConstants.MIN_HEIGHT, 
        le=BiometricConstants.MAX_HEIGHT, 
        description="Height in cm (required)"
    )
    activity_level: ActivityLevel = Field(..., description="Daily activity level (required)")


class UserCreate(UserBase, UserBiometrics):
    """User creation schema with biometric data"""
    password: str = Field(
        ..., 
        min_length=DatabaseConstants.MIN_PASSWORD_LENGTH, 
        description=f"Password (min {DatabaseConstants.MIN_PASSWORD_LENGTH} characters)"
    )


class UserBiometricsOptional(BaseModel):
    """Optional biometric data for updates"""
    age: Optional[int] = Field(
        None, 
        ge=BiometricConstants.MIN_AGE, 
        le=BiometricConstants.MAX_AGE, 
        description="Age in years"
    )
    gender: Optional[Gender] = Field(None, description="Gender for BMR calculation")
    weight: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_WEIGHT, 
        le=BiometricConstants.MAX_WEIGHT, 
        description="Weight in kg"
    )
    height: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_HEIGHT, 
        le=BiometricConstants.MAX_HEIGHT, 
        description="Height in cm"
    )
    activity_level: Optional[ActivityLevel] = Field(None, description="Daily activity level")


class UserBiometricsUpdate(BaseModel):
    """Biometric update schema - automatically recalculates BMR and TDEE when fields change"""
    age: Optional[int] = Field(
        None, 
        ge=BiometricConstants.MIN_AGE, 
        le=BiometricConstants.MAX_AGE, 
        description="Age in years"
    )
    gender: Optional[Gender] = Field(None, description="Gender for BMR calculation")
    weight: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_WEIGHT, 
        le=BiometricConstants.MAX_WEIGHT, 
        description="Weight in kg"
    )
    height: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_HEIGHT, 
        le=BiometricConstants.MAX_HEIGHT, 
        description="Height in cm"
    )
    activity_level: Optional[ActivityLevel] = Field(None, description="Daily activity level")


class UserUpdate(BaseModel):
    """User update schema with optional biometric data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # Biometric fields for updates
    age: Optional[int] = Field(
        None, 
        ge=BiometricConstants.MIN_AGE, 
        le=BiometricConstants.MAX_AGE, 
        description="Age in years"
    )
    gender: Optional[Gender] = Field(None, description="Gender for BMR calculation")
    weight: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_WEIGHT, 
        le=BiometricConstants.MAX_WEIGHT, 
        description="Weight in kg"
    )
    height: Optional[float] = Field(
        None, 
        ge=BiometricConstants.MIN_HEIGHT, 
        le=BiometricConstants.MAX_HEIGHT, 
        description="Height in cm"
    )
    activity_level: Optional[ActivityLevel] = Field(None, description="Daily activity level")


class UserResponse(UserBase):
    """User response schema (excludes sensitive data)"""
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Biometric data (required in the response if user is fully registered)
    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[Gender] = Field(None, description="Gender")
    weight: Optional[float] = Field(None, description="Weight in kg")
    height: Optional[float] = Field(None, description="Height in cm")
    activity_level: Optional[ActivityLevel] = Field(None, description="Activity level")
    
    # Calculated values (automatically computed when biometric data is complete)
    bmr: Optional[float] = Field(None, description="Basal Metabolic Rate (kcal/day)")
    daily_caloric_expenditure: Optional[float] = Field(None, description="Total daily energy expenditure (kcal/day)")
    
    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
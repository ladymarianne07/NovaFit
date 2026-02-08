from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_user_service, get_biometric_service, get_current_active_user
from ..schemas.user import UserResponse, UserUpdate, UserBiometricsUpdate
from ..services.user_service import UserService
from ..services.biometric_service import BiometricService
from ..db.models import User
from ..constants import SuccessMessages
from ..core.custom_exceptions import BiometricValidationError, IncompleteBiometricDataError


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile"""
    return current_user


@router.get("/all", response_model=List[UserResponse])
async def get_all_users(
    user_service: UserService = Depends(get_user_service)
):
    """Get all users for development/testing purposes"""
    # Note: In production, this should be restricted to admin users only
    return user_service.get_all_users()


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user's profile including biometric data with automatic recalculation"""
    try:
        # Update user profile using service with automatic biometric recalculation
        updated_user = user_service.update_user_profile_with_biometrics(
            current_user,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            age=user_update.age,
            gender=user_update.gender,
            weight=user_update.weight,
            height=user_update.height,
            activity_level=user_update.activity_level
        )
        
        return updated_user
        
    except BiometricValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biometric validation failed: {e.errors}"
        )


@router.put("/me/biometrics", response_model=UserResponse)
async def update_user_biometrics(
    biometric_update: UserBiometricsUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user's biometric data with automatic BMR and TDEE recalculation
    
    When any biometric field (weight, height, age, gender, activity_level) is updated,
    the system automatically recalculates:
    - BMR (Basal Metabolic Rate)
    - Daily Caloric Expenditure (TDEE)
    
    This ensures the user's caloric calculations are always up-to-date.
    """
    try:
        # Update biometric data with automatic recalculation
        updated_user = user_service.update_user_biometrics(current_user, biometric_update)
        
        return updated_user
        
    except BiometricValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biometric validation failed: {e.errors}"
        )


@router.post("/me/recalculate", response_model=UserResponse)
async def recalculate_user_metrics(
    current_user: User = Depends(get_current_active_user),
    biometric_service: BiometricService = Depends(get_biometric_service),
    user_service: UserService = Depends(get_user_service)
):
    """Force recalculation of BMR and daily caloric expenditure for current user
    
    This endpoint manually triggers recalculation of caloric metrics using
    the user's current biometric data. Useful for fixing any inconsistencies.
    """
    try:
        # Recalculate metrics using current biometric data
        bmr, daily_expenditure = biometric_service.recalculate_user_metrics(current_user)
        
        if bmr is None or daily_expenditure is None:
            raise IncompleteBiometricDataError([
                "age", "gender", "weight", "height", "activity_level"
            ])
        
        # Update the calculated values via service
        updated_user = user_service.update_calculated_metrics(current_user, bmr, daily_expenditure)
        
        return updated_user
        
    except IncompleteBiometricDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
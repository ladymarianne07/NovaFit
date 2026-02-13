"""
Nutrition API endpoints for macronutrient tracking and meal logging

Provides endpoints for:
- Getting daily macronutrient progress  
- Logging meals and updating nutrition
- Getting AI-powered nutrition suggestions
"""
from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user
from ..db.database import get_database_session
from ..db.models import User
from ..schemas.nutrition import (
    MacronutrientResponse,
    MealLogCreate, 
    MealLogResponse
)
from ..services.nutrition_service import NutritionService
from ..core.custom_exceptions import ValidationError, UserNotFoundError


router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/macros", response_model=MacronutrientResponse)
async def get_macronutrient_progress(
    target_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get daily macronutrient progress for the current user"""
    try:
        user_id: int = current_user.id  # type: ignore
        progress = NutritionService.get_macronutrient_progress(
            db=db,
            user_id=user_id,
            target_date=target_date
        )
        return progress
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve macronutrient data"
        )


@router.post("/meals", response_model=MealLogResponse)
async def log_meal(
    meal_data: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Log a meal and update daily nutrition tracking"""
    try:
        user_id: int = current_user.id  # type: ignore
        meal_log = NutritionService.log_meal(
            db=db,
            user_id=user_id,
            meal_data=meal_data
        )
        return meal_log
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log meal"
        )


@router.get("/suggestions")
async def get_nutrition_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get AI-powered nutrition suggestions based on current progress"""
    try:
        user_id: int = current_user.id  # type: ignore
        suggestion = NutritionService.get_ai_nutrition_suggestion(
            db=db,
            user_id=user_id
        )
        return suggestion
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate nutrition suggestions"
        )
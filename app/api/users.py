from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_user_service, get_biometric_service, get_skinfold_service, get_current_active_user
from ..schemas.user import UserResponse, UserUpdate, UserBiometricsUpdate, FitnessObjective
from ..schemas.progress import ProgressEvaluationResponse, ProgressEvaluationRequest, ProgressTimelineResponse
from ..schemas.skinfold import (
    SkinfoldCalculationRequest,
    SkinfoldCalculationResponse,
    SkinfoldHistoryItem,
    SkinfoldAIParseRequest,
    SkinfoldAIParseResponse,
)
from ..services.user_service import UserService
from ..services.biometric_service import BiometricService
from ..services.skinfold_service import SkinfoldService
from ..services.progress_evaluation_service import evaluarProgreso
from ..services.progress_timeline_service import ProgressTimelineService
from ..db.models import User, SkinfoldMeasurement
from ..db.database import get_database_session
from ..core.custom_exceptions import BiometricValidationError, IncompleteBiometricDataError
from pydantic import BaseModel, Field


class ObjectiveUpdate(BaseModel):
    """Request model for updating user's fitness objective"""
    objective: FitnessObjective = Field(..., description="Fitness objective")
    aggressiveness_level: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Aggressiveness level (1=conservative, 2=moderate, 3=aggressive)"
    )


router = APIRouter(prefix="/users", tags=["users"])


OBJECTIVE_TO_PROGRESS_OBJECTIVE = {
    "fat_loss": "perdida_grasa",
    "maintenance": "mantenimiento",
    "muscle_gain": "aumento_muscular",
    "body_recomp": "recomposicion",
    "performance": "rendimiento",
}


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


@router.put("/me/objective", response_model=UserResponse)
async def update_user_objective(
    objective_data: ObjectiveUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user's fitness objective and recalculate calorie/macro targets
    
    This endpoint updates the user's fitness objective (maintenance, fat_loss, muscle_gain, 
    body_recomposition, performance) and an optional aggressiveness level. The system 
    automatically recalculates:
    - Target daily calories (based on objective and TDEE)
    - Protein, fat, and carbohydrate targets (in grams)
    """
    try:
        updated_user = user_service.update_user_objective(
            current_user,
            objective_data.objective.value,
            objective_data.aggressiveness_level
        )
        
        return updated_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update objective: {str(e)}"
        )


@router.post("/me/progress-evaluation", response_model=ProgressEvaluationResponse)
async def evaluate_current_user_progress(
    payload: ProgressEvaluationRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Evaluate user progress using stored objective + available historical body metrics.

    Data source strategy:
    - Objective: current user's configured objective (fallback: maintenance)
    - History: skinfold measurements ordered by date ASC
    - Weight: measurement weight when available, else current user weight
    """
    target_objective = OBJECTIVE_TO_PROGRESS_OBJECTIVE.get(current_user.objective or "", "mantenimiento")

    measurements = (
        db.query(SkinfoldMeasurement)
        .filter(SkinfoldMeasurement.user_id == current_user.id)
        .order_by(SkinfoldMeasurement.measured_at.asc())
        .all()
    )

    history_payload: list[dict] = []

    if measurements:
        for measurement in measurements:
            resolved_weight = measurement.weight_kg if measurement.weight_kg is not None else current_user.weight

            history_payload.append(
                {
                    "fecha": measurement.measured_at,
                    "peso": resolved_weight,
                    "porcentaje_grasa": measurement.body_fat_percent,
                    "porcentaje_masa_magra": measurement.fat_free_mass_percent,
                }
            )
    else:
        # Fallback to current profile point so evaluator can return explicit "insufficient data" warning
        history_payload = [
            {
                "fecha": current_user.created_at,
                "peso": current_user.weight,
                "porcentaje_grasa": None,
                "porcentaje_masa_magra": None,
            }
        ]

    requested_period = payload.periodo.value if payload is not None else "mes"

    evaluation = evaluarProgreso(
        objetivo=target_objective,
        periodo=requested_period,
        historial=history_payload,
    )
    return evaluation


@router.get("/me/progress/timeline", response_model=ProgressTimelineResponse)
async def get_progress_timeline(
    periodo: str = "mes",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Get historical progress timeline for charts.

    Returns time-series data for:
    - Weight (from explicit weight events + skinfold measurements)
    - Body fat percentage (from skinfold measurements)
    - Lean mass percentage (from skinfold measurements)
    - Daily calories consumed vs target
    - Daily macro percentages
    """
    timeline_data = ProgressTimelineService.build_timeline(db=db, user=current_user, periodo=periodo)
    return timeline_data


@router.post("/me/skinfolds/ai-parse", response_model=SkinfoldAIParseResponse)
async def parse_skinfolds_ai(
    payload: SkinfoldAIParseRequest,
    current_user: User = Depends(get_current_active_user),
    skinfold_service: SkinfoldService = Depends(get_skinfold_service),
):
    """Parse skinfold text input with AI-assisted rules (regex-based extraction)."""
    parsed, warnings = skinfold_service.parse_ai_text(payload.text)
    return {
        "parsed": parsed,
        "warnings": warnings,
    }


@router.post("/me/skinfolds", response_model=SkinfoldCalculationResponse)
async def calculate_and_save_skinfolds(
    payload: SkinfoldCalculationRequest,
    current_user: User = Depends(get_current_active_user),
    skinfold_service: SkinfoldService = Depends(get_skinfold_service),
):
    """Calculate body composition using skinfolds and persist the result."""
    result = skinfold_service.calculate(payload)
    skinfold_service.save_measurement(current_user, payload, result)
    return result


@router.get("/me/skinfolds", response_model=List[SkinfoldHistoryItem])
async def get_skinfold_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    skinfold_service: SkinfoldService = Depends(get_skinfold_service),
):
    """Return latest saved skinfold calculations for current user."""
    safe_limit = min(max(limit, 1), 100)
    items = skinfold_service.get_history(current_user.id, safe_limit)
    return items
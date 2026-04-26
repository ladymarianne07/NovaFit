"""Diet API endpoints — AI generation, editing, and retrieval of diet plans."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..db.models import User, UserRoutine
from ..dependencies import get_current_active_user
from ..schemas.diet import (
    ApplyAlternativeRequest,
    CurrentMealResponse,
    DietEditRequest,
    DietGenerateRequest,
    DietLogMealRequest,
    DietLogMealResponse,
    DietModifyMealRequest,
    MealAlternativeResponse,
    UserDietResponse,
)
from ..services.diet_service import DietService
from ..core.custom_exceptions import DietNotFoundError, DietParsingError
from ..core.exception_handlers import service_error_handler
from ..core.user_helpers import extract_user_bio, get_current_user_id


router = APIRouter(prefix="/v1/diet", tags=["diet"])

_RESPONSES_404 = {404: {"description": "No active diet plan found for this user"}}
_RESPONSES_422 = {422: {"description": "AI response could not be parsed into a valid diet structure"}}
_RESPONSES_500 = {500: {"description": "Unexpected server error"}}


# ── AI generation ─────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=UserDietResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI diet plan",
    response_description="The newly generated diet plan (status=ready) or an error record (status=error)",
    responses={**_RESPONSES_422, **_RESPONSES_500},
)
async def generate_diet(
    payload: DietGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Generate a personalized diet plan from intake form + free text using AI."""
    try:
        with service_error_handler("Failed to generate diet plan"):
            user_bio = extract_user_bio(current_user, [
                "age", "gender", "weight_kg", "height_cm", "activity_level",
                "objective", "target_calories", "protein_target_g", "carbs_target_g", "fat_target_g",
            ])

            # Fetch active routine data for training-day calorie adjustment
            routine_data: dict[str, Any] | None = None
            routine = db.query(UserRoutine).filter(
                UserRoutine.user_id == get_current_user_id(current_user),
                UserRoutine.status == "ready",
            ).first()
            if routine is not None:
                routine_data = getattr(routine, "routine_data", None)

            diet = DietService.generate_from_text(
                db,
                user_id=get_current_user_id(current_user),
                intake=payload.intake.model_dump(),
                free_text=payload.free_text,
                user_bio=user_bio,
                routine_data=routine_data,
            )
            return diet

    except DietParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Edit diet ─────────────────────────────────────────────────────────────────

@router.post(
    "/edit",
    response_model=UserDietResponse,
    summary="Edit diet with natural language instruction",
    responses={**_RESPONSES_404, **_RESPONSES_422, **_RESPONSES_500},
)
async def edit_diet(
    payload: DietEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Apply an edit instruction to the user's current diet plan using AI."""
    try:
        with service_error_handler("Failed to edit diet plan"):
            diet = DietService.edit_diet(
                db,
                user_id=get_current_user_id(current_user),
                edit_instruction=payload.edit_instruction,
            )
            return diet

    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DietParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get(
    "/active",
    response_model=UserDietResponse,
    summary="Get active diet plan",
    responses={**_RESPONSES_404, **_RESPONSES_500},
)
async def get_active_diet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return the user's current active diet plan."""
    try:
        with service_error_handler("Failed to retrieve diet plan"):
            diet = DietService.get_active_diet(
                db,
                user_id=get_current_user_id(current_user),
            )
            return diet
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Meal tracker ──────────────────────────────────────────────────────────────

@router.get(
    "/current-meal",
    response_model=CurrentMealResponse,
    summary="Get current planned meal",
    responses={**_RESPONSES_404, **_RESPONSES_500},
)
async def get_current_meal(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return the current planned meal based on today's day type and tracker index."""
    try:
        with service_error_handler("Failed to retrieve current meal"):
            result = DietService.get_current_meal(
                db,
                user_id=get_current_user_id(current_user),
            )
            return result
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/log-meal",
    response_model=DietLogMealResponse,
    summary="Mark meal as complete or skipped",
    responses={400: {"description": "action must be 'complete' or 'skip'"}, **_RESPONSES_404, **_RESPONSES_500},
)
async def log_meal(
    payload: DietLogMealRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Mark the current planned meal as complete or skipped, advancing the tracker."""
    try:
        with service_error_handler("Failed to log meal"):
            result = DietService.log_meal(
                db,
                user_id=get_current_user_id(current_user),
                action=payload.action,
            )
            return result
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/meals/alternative",
    response_model=MealAlternativeResponse,
    summary="Generate AI alternative for current meal",
    responses={**_RESPONSES_404, **_RESPONSES_500},
)
async def generate_meal_alternative(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Generate an AI alternative for the current planned meal (same macros ±ranges)."""
    try:
        with service_error_handler("Failed to generate meal alternative"):
            result = DietService.get_meal_alternative(db, user_id=get_current_user_id(current_user))
            return result
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/meals/apply-alternative",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Apply meal alternative (permanent or 24 h override)",
    responses={400: {"description": "scope must be 'diet' or 'today'"}, **_RESPONSES_404, **_RESPONSES_500},
)
async def apply_meal_alternative(
    payload: ApplyAlternativeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Apply a meal alternative — permanently to the diet or as a 24 h daily override."""
    if payload.scope not in ("diet", "today"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope must be 'diet' or 'today'")
    try:
        with service_error_handler("Failed to apply meal alternative"):
            DietService.apply_meal_alternative(
                db,
                user_id=get_current_user_id(current_user),
                meal_index=payload.meal_index,
                day_type=payload.day_type,
                scope=payload.scope,
                meal=payload.meal.model_dump(),
            )
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/modify-meal",
    response_model=UserDietResponse,
    summary="Add or remove a food item from a meal",
    responses={400: {"description": "Invalid action or missing required field"}, **_RESPONSES_404, **_RESPONSES_422, **_RESPONSES_500},
)
async def modify_meal(
    payload: DietModifyMealRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Add or remove a food item from a specific meal in the diet plan."""
    if payload.action == "add_food" and payload.food is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="food is required for add_food")
    if payload.action == "remove_food" and payload.food_index is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="food_index is required for remove_food")
    try:
        with service_error_handler("Failed to modify meal"):
            diet = DietService.modify_meal(
                db,
                user_id=get_current_user_id(current_user),
                day_type=payload.day_type,
                meal_id=payload.meal_id,
                action=payload.action,
                food=payload.food.model_dump() if payload.food else None,
                food_index=payload.food_index,
            )
            return diet
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DietParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

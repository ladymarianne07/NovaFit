"""Diet API endpoints — AI generation, editing, and retrieval of diet plans."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..db.models import User, UserRoutine
from ..dependencies import get_current_active_user
from ..schemas.diet import DietEditRequest, DietGenerateRequest, UserDietResponse
from ..services.diet_service import DietService
from ..core.custom_exceptions import DietNotFoundError, DietParsingError


router = APIRouter(prefix="/v1/diet", tags=["diet"])


# ── AI generation ─────────────────────────────────────────────────────────────

@router.post("/generate", response_model=UserDietResponse, status_code=status.HTTP_201_CREATED)
async def generate_diet(
    payload: DietGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Generate a personalized diet plan from intake form + free text using AI."""
    try:
        user_bio: dict[str, Any] = {
            "age": getattr(current_user, "age", None),
            "gender": getattr(current_user, "gender", None),
            "weight_kg": getattr(current_user, "weight_kg", None),
            "height_cm": getattr(current_user, "height_cm", None),
            "activity_level": getattr(current_user, "activity_level", None),
            "objective": getattr(current_user, "objective", None),
            "target_calories": getattr(current_user, "target_calories", None),
            "protein_target_g": getattr(current_user, "protein_target_g", None),
            "carbs_target_g": getattr(current_user, "carbs_target_g", None),
            "fat_target_g": getattr(current_user, "fat_target_g", None),
        }

        # Fetch active routine data for training-day calorie adjustment
        routine_data: dict[str, Any] | None = None
        routine = db.query(UserRoutine).filter(
            UserRoutine.user_id == int(getattr(current_user, "id")),
            UserRoutine.status == "ready",
        ).first()
        if routine is not None:
            routine_data = getattr(routine, "routine_data", None)

        diet = DietService.generate_from_text(
            db,
            user_id=int(getattr(current_user, "id")),
            intake=payload.intake.model_dump(),
            free_text=payload.free_text,
            user_bio=user_bio,
            routine_data=routine_data,
        )
        return diet

    except DietParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate diet plan",
        )


# ── Edit diet ─────────────────────────────────────────────────────────────────

@router.post("/edit", response_model=UserDietResponse)
async def edit_diet(
    payload: DietEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Apply an edit instruction to the user's current diet plan using AI."""
    try:
        diet = DietService.edit_diet(
            db,
            user_id=int(getattr(current_user, "id")),
            edit_instruction=payload.edit_instruction,
        )
        return diet

    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DietParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit diet plan",
        )


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get("/active", response_model=UserDietResponse)
async def get_active_diet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return the user's current active diet plan."""
    try:
        diet = DietService.get_active_diet(
            db,
            user_id=int(getattr(current_user, "id")),
        )
        return diet
    except DietNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve diet plan",
        )

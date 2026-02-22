"""Workout API endpoints for session creation and daily energy summaries."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..db.models import User
from ..dependencies import get_current_active_user
from ..schemas.workout import DailyEnergyResponse, WorkoutSessionCreate, WorkoutSessionResponse
from ..services.workout_service import WorkoutService
from ..core.custom_exceptions import (
    WorkoutActivityNotFoundError,
    WorkoutValidationError,
    WorkoutWeightRequiredError,
)


router = APIRouter(prefix="/v1", tags=["workout"])


@router.post("/sessions", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_workout_session(
    payload: WorkoutSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Create a workout session and recalculate daily exercise energy."""
    try:
        user_data = current_user  # keep name for readability in getattr usage
        weight_kg = payload.weight_kg
        if weight_kg is None:
            weight_kg = float(getattr(user_data, "weight_kg", 0.0) or 0.0)

        blocks_data: list[dict[str, Any]] = [
            {
                "activity": block.activity,
                "duration_minutes": block.duration_minutes,
                "intensity": block.intensity,
            }
            for block in payload.blocks
        ]

        session = WorkoutService.create_session(
            db=db,
            user_id=int(getattr(user_data, "id")),
            session_date=payload.session_date,
            source=payload.source,
            status=payload.status,
            blocks_data=blocks_data,
            weight_kg=weight_kg,
            raw_input=payload.raw_input,
            ai_output=payload.ai_output,
        )
        return session

    except WorkoutActivityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (WorkoutValidationError, WorkoutWeightRequiredError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workout session",
        )


@router.get("/days/{target_date}/energy", response_model=DailyEnergyResponse)
async def get_daily_energy(
    target_date: date,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return daily exercise + intake + net energy totals for a date."""
    try:
        daily_log = WorkoutService.get_daily_energy(
            db=db,
            user_id=int(getattr(current_user, "id")),
            log_date=target_date,
        )
        return daily_log
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily energy",
        )


@router.get("/sessions", response_model=list[WorkoutSessionResponse])
async def list_workout_sessions(
    session_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """List current user's workout sessions, optionally filtered by date."""
    try:
        sessions = WorkoutService.list_sessions(
            db=db,
            user_id=int(getattr(current_user, "id")),
            session_date=session_date,
            limit=limit,
            offset=offset,
        )
        return sessions
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workout sessions",
        )


@router.delete("/sessions/{session_id}")
async def delete_workout_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Delete a workout session and refresh daily energy aggregation."""
    try:
        deleted = WorkoutService.delete_session(
            db=db,
            user_id=int(getattr(current_user, "id")),
            session_id=session_id,
        )
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout session not found")

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workout session",
        )

"""Routine API endpoints — upload, AI generation, editing, retrieve, and log sessions."""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..db.models import User
from ..dependencies import get_current_active_user
from ..schemas.routine import (
    RoutineEditRequest,
    RoutineGenerateRequest,
    RoutineLogSessionRequest,
    UserRoutineResponse,
)
from ..schemas.workout import WorkoutSessionResponse
from ..services.routine_service import RoutineService
from ..core.custom_exceptions import (
    RoutineFileTooLargeError,
    RoutineInvalidFileTypeError,
    RoutineNotFoundError,
    RoutineParsingError,
)


router = APIRouter(prefix="/v1/routines", tags=["routine"])


# ── File upload ───────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UserRoutineResponse, status_code=status.HTTP_201_CREATED)
async def upload_routine(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Upload a routine file (PDF, image, or text) and parse it with Gemini."""
    try:
        file_bytes = await file.read()
        mime_type = file.content_type or "application/octet-stream"
        filename = file.filename or "routine"

        routine = RoutineService.parse_and_save(
            db,
            user_id=int(getattr(current_user, "id")),
            file_bytes=file_bytes,
            mime_type=mime_type,
            filename=filename,
        )
        return routine

    except RoutineFileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except RoutineInvalidFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except RoutineParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process routine file",
        )


# ── AI text generation ────────────────────────────────────────────────────────

@router.post("/generate", response_model=UserRoutineResponse, status_code=status.HTTP_201_CREATED)
async def generate_routine(
    payload: RoutineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Generate a personalized routine from intake form + free text using the AI personal trainer."""
    try:
        user_data = current_user
        user_bio: dict[str, Any] = {
            "age": getattr(user_data, "age", None),
            "gender": getattr(user_data, "gender", None),
            "weight_kg": getattr(user_data, "weight_kg", None),
            "height_cm": getattr(user_data, "height_cm", None),
        }

        routine = RoutineService.generate_from_text(
            db,
            user_id=int(getattr(current_user, "id")),
            intake=payload.intake.model_dump(),
            free_text=payload.free_text,
            user_bio=user_bio,
        )
        return routine

    except RoutineParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate routine",
        )


# ── Edit routine ──────────────────────────────────────────────────────────────

@router.post("/edit", response_model=UserRoutineResponse)
async def edit_routine(
    payload: RoutineEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Apply an edit instruction to the user's current routine using the AI personal trainer."""
    try:
        routine = RoutineService.edit_routine(
            db,
            user_id=int(getattr(current_user, "id")),
            edit_instruction=payload.edit_instruction,
        )
        return routine

    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RoutineParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit routine",
        )


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get("/active", response_model=UserRoutineResponse)
async def get_active_routine(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return the user's current active routine."""
    try:
        routine = RoutineService.get_active_routine(
            db,
            user_id=int(getattr(current_user, "id")),
        )
        return routine
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve routine",
        )


# ── Log session ───────────────────────────────────────────────────────────────

@router.post("/log-session", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def log_routine_session(
    payload: RoutineLogSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Log a completed routine session, optionally marking exercises as skipped."""
    try:
        user_data = current_user
        weight_kg = float(getattr(user_data, "weight_kg", 0.0) or 0.0)

        session = RoutineService.log_session(
            db,
            user_id=int(getattr(user_data, "id")),
            session_id=payload.session_id,
            session_date=payload.session_date,
            skipped_exercise_ids=payload.skipped_exercise_ids,
            weight_kg=weight_kg,
        )
        return session

    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log routine session",
        )

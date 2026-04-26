"""Routine API endpoints — upload, AI generation, editing, retrieve, and log sessions."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..db.database import get_database_session
from ..db.models import User
from ..dependencies import get_current_active_user
from ..schemas.routine import (
    AdvanceSessionResponse,
    RoutineAdvanceSessionRequest,
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
from ..core.exception_handlers import service_error_handler
from ..core.user_helpers import extract_user_bio, extract_weight_kg, get_current_user_id


router = APIRouter(prefix="/v1/routines", tags=["routines"])

_RESPONSES_404 = {404: {"description": "No active routine found for this user"}}
_413 = {413: {"description": "File exceeds 5 MB limit"}}
_415 = {415: {"description": "File type not supported (only PDF, JPEG, PNG, WebP, GIF)"}}
_RESPONSES_422 = {422: {"description": "Gemini response could not be parsed into a valid routine structure"}}
_RESPONSES_500 = {500: {"description": "Unexpected server error"}}


# ── File upload ───────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UserRoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload routine file (PDF / image) and parse with AI",
    responses={**_413, **_415, **_RESPONSES_422, **_RESPONSES_500},
)
async def upload_routine(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Upload a routine file (PDF, image, or text) and parse it with Gemini."""
    try:
        with service_error_handler("Failed to process routine file"):
            file_bytes = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            filename = file.filename or "routine"

            routine = RoutineService.parse_and_save(
                db,
                user_id=get_current_user_id(current_user),
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


# ── AI text generation ────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=UserRoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI routine from intake form",
    responses={**_RESPONSES_422, **_RESPONSES_500},
)
async def generate_routine(
    payload: RoutineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Generate a personalized routine from intake form + free text using the AI personal trainer."""
    try:
        with service_error_handler("Failed to generate routine"):
            user_bio = extract_user_bio(current_user, [
                "age", "gender", "weight_kg", "height_cm", "objective",
            ])

            routine = RoutineService.generate_from_text(
                db,
                user_id=get_current_user_id(current_user),
                intake=payload.intake.model_dump(),
                free_text=payload.free_text,
                user_bio=user_bio,
            )
            return routine

    except RoutineParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Edit routine ──────────────────────────────────────────────────────────────

@router.post(
    "/edit",
    response_model=UserRoutineResponse,
    summary="Edit routine with natural language instruction",
    responses={**_RESPONSES_404, **_RESPONSES_422, **_RESPONSES_500},
)
async def edit_routine(
    payload: RoutineEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Apply an edit instruction to the user's current routine using the AI personal trainer."""
    try:
        with service_error_handler("Failed to edit routine"):
            routine = RoutineService.edit_routine(
                db,
                user_id=get_current_user_id(current_user),
                edit_instruction=payload.edit_instruction,
            )
            return routine

    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RoutineParsingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Retrieve ──────────────────────────────────────────────────────────────────

@router.get(
    "/active",
    response_model=UserRoutineResponse,
    summary="Get active routine",
    responses={**_RESPONSES_404, **_RESPONSES_500},
)
async def get_active_routine(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Return the user's current active routine."""
    try:
        with service_error_handler("Failed to retrieve routine"):
            routine = RoutineService.get_active_routine(
                db,
                user_id=get_current_user_id(current_user),
            )
            return routine
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Advance session ───────────────────────────────────────────────────────────

@router.post("/advance-session", response_model=AdvanceSessionResponse)
async def advance_routine_session(
    payload: RoutineAdvanceSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Advance the routine to the next session (complete or skip the current one)."""
    try:
        with service_error_handler("Failed to advance routine session"):
            user_data = current_user
            weight_kg = extract_weight_kg(user_data)

            routine = RoutineService.advance_session(
                db,
                user_id=get_current_user_id(current_user),
                action=payload.action,
                weight_kg=weight_kg,
            )
            return routine

    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Log session ───────────────────────────────────────────────────────────────

@router.post("/log-session", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def log_routine_session(
    payload: RoutineLogSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
):
    """Log a completed routine session, optionally marking exercises as skipped."""
    try:
        with service_error_handler("Failed to log routine session"):
            user_data = current_user
            weight_kg = extract_weight_kg(user_data)

            session = RoutineService.log_session(
                db,
                user_id=get_current_user_id(user_data),
                session_id=payload.session_id,
                session_date=payload.session_date,
                skipped_exercise_ids=payload.skipped_exercise_ids,
                extra_exercises=[ex.model_dump() for ex in payload.extra_exercises],
                weight_kg=weight_kg,
            )
            return session

    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

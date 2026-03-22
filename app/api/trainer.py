from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_active_user, get_current_trainer, get_trainer_service, get_notification_service, get_user_service, get_skinfold_service
from ..db.database import get_database_session
from ..db.models import User
from ..schemas.trainer import TrainerInviteResponse, StudentSummary, TrainerStudentLinkResponse
from ..schemas.user import UserResponse, UserBiometricsUpdate
from ..schemas.skinfold import SkinfoldHistoryItem
from ..schemas.nutrition import MacronutrientResponse
from ..services.trainer_service import TrainerService
from ..services.notification_service import NotificationService
from ..services.user_service import UserService
from ..services.nutrition_service import NutritionService
from ..services.skinfold_service import SkinfoldService
from ..core.custom_exceptions import (
    BiometricValidationError,
    InviteNotFoundError,
    StudentNotLinkedError,
    UserNotFoundError,
)
from ..api.users import ObjectiveUpdate, NutritionTargetsUpdate
from sqlalchemy.orm import Session

router = APIRouter(prefix="/trainer", tags=["trainer"])


# ── Invite endpoints ───────────────────────────────────────────────────────────

@router.get("/invite", response_model=TrainerInviteResponse)
async def get_current_invite(
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
):
    """Get the current active invite code for the authenticated trainer."""
    invite = trainer_service.get_latest_invite(current_user.id)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay un código de invitación activo. Genera uno nuevo.",
        )
    return invite


@router.post("/invite", response_model=TrainerInviteResponse, status_code=status.HTTP_201_CREATED)
async def generate_invite(
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
):
    """Generate a new invite code valid for 7 days."""
    return trainer_service.generate_invite(current_user)


# ── Student management ─────────────────────────────────────────────────────────

@router.get("/students", response_model=List[StudentSummary])
async def list_students(
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
):
    """List all active students linked to this trainer."""
    students = trainer_service.get_students(current_user.id)

    result = []
    for student in students:
        link = trainer_service.get_student_link(current_user.id, student.id)
        result.append(
            StudentSummary(
                id=student.id,
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,
                objective=student.objective,
                target_calories=student.target_calories,
                weight_kg=student.weight_kg,
                linked_at=link.linked_at,
            )
        )
    return result


@router.get("/students/{student_id}", response_model=UserResponse)
async def get_student_profile(
    student_id: int,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
):
    """Get a specific student's full profile."""
    try:
        return trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_student(
    student_id: int,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
):
    """Revoke the link between this trainer and a student."""
    try:
        trainer_service.unlink_student(current_user.id, student_id)
    except StudentNotLinkedError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# ── Trainer edits student data ─────────────────────────────────────────────────

@router.put("/students/{student_id}/biometrics", response_model=UserResponse)
async def update_student_biometrics(
    student_id: int,
    biometric_update: UserBiometricsUpdate,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
    notification_service: NotificationService = Depends(get_notification_service),
    user_service: UserService = Depends(get_user_service),
):
    """Trainer updates a student's biometric data and notifies the student."""
    try:
        student = trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    try:
        updated_student = user_service.update_user_biometrics(student, biometric_update)
    except BiometricValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Biometric validation failed: {e.errors}")

    notification_service.notify_student_of_trainer_edit(current_user, student, "biometrics")
    return updated_student


@router.put("/students/{student_id}/objective", response_model=UserResponse)
async def update_student_objective(
    student_id: int,
    objective_data: ObjectiveUpdate,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
    notification_service: NotificationService = Depends(get_notification_service),
    user_service: UserService = Depends(get_user_service),
):
    """Trainer updates a student's fitness objective and notifies the student."""
    try:
        student = trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    try:
        updated_student = user_service.update_user_objective(
            student, objective_data.objective.value, objective_data.aggressiveness_level
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    notification_service.notify_student_of_trainer_edit(current_user, student, "objective")
    return updated_student


@router.put("/students/{student_id}/nutrition-targets", response_model=UserResponse)
async def update_student_nutrition_targets(
    student_id: int,
    nutrition_targets: NutritionTargetsUpdate,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
    notification_service: NotificationService = Depends(get_notification_service),
    user_service: UserService = Depends(get_user_service),
):
    """Trainer updates a student's custom nutrition targets and notifies the student."""
    try:
        student = trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    updated_student = user_service.update_user_nutrition_targets(
        student,
        custom_target_calories=nutrition_targets.custom_target_calories,
        carbs_target_percent=nutrition_targets.carbs_target_percent,
        protein_target_percent=nutrition_targets.protein_target_percent,
        fat_target_percent=nutrition_targets.fat_target_percent,
    )
    notification_service.notify_student_of_trainer_edit(current_user, student, "nutrition_targets")
    return updated_student


# ── Trainer reads student data ──────────────────────────────────────────────

@router.get("/students/{student_id}/macros", response_model=MacronutrientResponse)
async def get_student_macros(
    student_id: int,
    target_date: Optional[date] = None,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
    db: Session = Depends(get_database_session),
):
    """Get a specific student's daily macronutrient progress (trainer view)."""
    try:
        trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    return NutritionService.get_macronutrient_progress(
        db=db,
        user_id=student_id,
        target_date=target_date,
    )


@router.get("/students/{student_id}/skinfolds", response_model=List[SkinfoldHistoryItem])
async def get_student_skinfolds(
    student_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_trainer),
    trainer_service: TrainerService = Depends(get_trainer_service),
    skinfold_service: SkinfoldService = Depends(get_skinfold_service),
):
    """Get a specific student's skinfold history (trainer view)."""
    try:
        trainer_service.get_student(current_user.id, student_id)
    except (StudentNotLinkedError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    return skinfold_service.get_history(student_id, limit)

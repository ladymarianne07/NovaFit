from fastapi import APIRouter, Depends, status

from ..dependencies import get_current_active_user, get_trainer_service, get_notification_service
from ..db.models import User
from ..schemas.trainer import AcceptInviteRequest, TrainerStudentLinkResponse
from ..services.trainer_service import TrainerService
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/invite", tags=["invite"])


@router.post("/accept", response_model=TrainerStudentLinkResponse, status_code=status.HTTP_201_CREATED)
async def accept_invite(
    request: AcceptInviteRequest,
    current_user: User = Depends(get_current_active_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Student accepts a trainer's invite code to link accounts."""
    link = trainer_service.accept_invite(current_user, request.code)

    # Notify the trainer that the student accepted
    notification_service.create(
        recipient_id=link.trainer_id,
        sender_id=current_user.id,
        type="invite_accepted",
        title="Nuevo alumno vinculado",
        body=f"{current_user.first_name} {current_user.last_name} aceptó tu invitación.",
        data={"student_id": current_user.id},
    )

    return link

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_active_user, get_notification_service
from ..db.models import User
from ..schemas.notification import NotificationResponse, NotificationListResponse
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    current_user: User = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Get all notifications for the current user (latest 50)."""
    notifications = notification_service.get_for_user(current_user.id)
    unread_count = notification_service.get_unread_count(current_user.id)

    result = []
    for n in notifications:
        sender = n.sender
        result.append(
            NotificationResponse(
                id=n.id,
                sender_id=n.sender_id,
                sender_name=f"{sender.first_name} {sender.last_name}" if sender else "Sistema",
                type=n.type,
                title=n.title,
                body=n.body,
                data=n.data,
                is_read=n.is_read,
                created_at=n.created_at,
            )
        )
    return NotificationListResponse(notifications=result, unread_count=unread_count)


@router.put("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark a single notification as read."""
    found = notification_service.mark_read(notification_id, current_user.id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada.")


@router.put("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    notification_service.mark_all_read(current_user.id)

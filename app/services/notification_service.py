from typing import List, Optional
from sqlalchemy.orm import Session

from ..constants import TrainerConstants
from ..db.models import Notification, TrainerStudent, User


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        recipient_id: int,
        sender_id: int,
        type: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> Notification:
        notification = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=type,
            title=title,
            body=body,
            data=data,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_for_user(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.recipient_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)  # noqa: E712
        return query.order_by(Notification.created_at.desc()).limit(TrainerConstants.MAX_NOTIFICATIONS_RETURNED).all()

    def get_unread_count(self, user_id: int) -> int:
        return (
            self.db.query(Notification)
            .filter(Notification.recipient_id == user_id, Notification.is_read == False)
            .count()
        )

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.recipient_id == user_id)
            .first()
        )
        if not notification:
            return False
        notification.is_read = True
        self.db.commit()
        return True

    def mark_all_read(self, user_id: int) -> int:
        updated = (
            self.db.query(Notification)
            .filter(Notification.recipient_id == user_id, Notification.is_read == False)
            .all()
        )
        count = len(updated)
        for n in updated:
            n.is_read = True
        self.db.commit()
        return count

    def get_active_trainer_for_student(self, student_id: int) -> Optional[User]:
        """Return the active trainer of a student, or None if not linked."""
        link = (
            self.db.query(TrainerStudent)
            .filter(
                TrainerStudent.student_id == student_id,
                TrainerStudent.status == TrainerConstants.LINK_STATUS_ACTIVE,
            )
            .first()
        )
        if not link:
            return None
        return self.db.query(User).filter(User.id == link.trainer_id).first()

    def notify_trainer_of_student_edit(
        self, student: User, field_group: str
    ) -> Optional[Notification]:
        """Notify a student's trainer when the student edits their own profile data.

        Returns None silently if the student has no active trainer.
        """
        trainer = self.get_active_trainer_for_student(student.id)
        if not trainer:
            return None

        label = TrainerConstants.FIELD_GROUP_LABELS.get(field_group, field_group)
        notif_type = f"student_edited_{field_group}"

        return self.create(
            recipient_id=trainer.id,
            sender_id=student.id,
            type=notif_type,
            title=f"{student.first_name} actualizó su perfil",
            body=f"{student.first_name} {student.last_name} editó sus {label}.",
            data={"student_id": student.id, "field_group": field_group},
        )

    def notify_student_of_trainer_edit(
        self, trainer: User, student: User, field_group: str
    ) -> Notification:
        """Notify a student when their trainer edits their profile data."""
        label = TrainerConstants.FIELD_GROUP_LABELS.get(field_group, field_group)
        notif_type = f"trainer_edited_{field_group}"

        return self.create(
            recipient_id=student.id,
            sender_id=trainer.id,
            type=notif_type,
            title="Tu entrenador actualizó tu perfil",
            body=f"{trainer.first_name} {trainer.last_name} editó tus {label}.",
            data={"trainer_id": trainer.id, "field_group": field_group},
        )

import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from ..constants import TrainerConstants
from ..core.custom_exceptions import (
    TrainerOnlyError,
    InviteNotFoundError,
    InviteAlreadyUsedError,
    InviteExpiredError,
    StudentAlreadyLinkedError,
    StudentNotLinkedError,
    UserNotFoundError,
)
from ..db.models import TrainerInvite, TrainerStudent, User


def _generate_code() -> str:
    """Generate a random uppercase alphanumeric invite code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(TrainerConstants.INVITE_CODE_LENGTH))


class TrainerService:
    """Service for trainer invite management and student relationship operations."""

    def __init__(self, db: Session):
        self.db = db

    # ── Invite management ──────────────────────────────────────────────────────

    def generate_invite(self, trainer: User) -> TrainerInvite:
        """Generate a new invite code for the trainer."""
        for _ in range(10):
            code = _generate_code()
            if not self.db.query(TrainerInvite).filter(TrainerInvite.code == code).first():
                break

        expires_at = datetime.now(timezone.utc) + timedelta(days=TrainerConstants.INVITE_EXPIRY_DAYS)
        invite = TrainerInvite(
            trainer_id=trainer.id,
            code=code,
            expires_at=expires_at,
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def get_latest_invite(self, trainer_id: int) -> Optional[TrainerInvite]:
        """Return the most recent unused, non-expired invite for a trainer, or None."""
        now = datetime.now(timezone.utc)
        return (
            self.db.query(TrainerInvite)
            .filter(
                TrainerInvite.trainer_id == trainer_id,
                TrainerInvite.used_by_user_id == None,  # noqa: E711
                TrainerInvite.expires_at > now,
            )
            .order_by(TrainerInvite.created_at.desc())
            .first()
        )

    def accept_invite(self, student: User, code: str) -> TrainerStudent:
        """Link a student to a trainer via an invite code.

        Raises:
            InviteNotFoundError: Code does not exist.
            InviteAlreadyUsedError: Code was already redeemed.
            InviteExpiredError: Code is past expiry.
            StudentAlreadyLinkedError: Student already has an active trainer.
        """
        now = datetime.now(timezone.utc)

        invite = (
            self.db.query(TrainerInvite)
            .filter(TrainerInvite.code == code.strip().upper())
            .first()
        )

        if not invite:
            raise InviteNotFoundError("Código de invitación no encontrado.")

        if invite.used_by_user_id is not None:
            raise InviteAlreadyUsedError("Este código ya fue utilizado.")

        invite_expiry = invite.expires_at
        if invite_expiry.tzinfo is None:
            invite_expiry = invite_expiry.replace(tzinfo=timezone.utc)
        if invite_expiry < now:
            raise InviteExpiredError("El código de invitación ha expirado.")

        if invite.trainer_id == student.id:
            raise StudentAlreadyLinkedError("Un entrenador no puede ser su propio alumno.")

        existing_link = (
            self.db.query(TrainerStudent)
            .filter(
                TrainerStudent.student_id == student.id,
                TrainerStudent.status == TrainerConstants.LINK_STATUS_ACTIVE,
            )
            .first()
        )
        if existing_link:
            raise StudentAlreadyLinkedError(
                "Ya estás vinculado a un entrenador. Desvinculáte primero."
            )

        # Reactivate a previously revoked link with this same trainer
        old_link = (
            self.db.query(TrainerStudent)
            .filter(
                TrainerStudent.trainer_id == invite.trainer_id,
                TrainerStudent.student_id == student.id,
            )
            .first()
        )
        if old_link:
            old_link.status = TrainerConstants.LINK_STATUS_ACTIVE
            invite.used_by_user_id = student.id
            self.db.commit()
            self.db.refresh(old_link)
            return old_link

        link = TrainerStudent(
            trainer_id=invite.trainer_id,
            student_id=student.id,
            status=TrainerConstants.LINK_STATUS_ACTIVE,
        )
        invite.used_by_user_id = student.id
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    # ── Student management ─────────────────────────────────────────────────────

    def get_students(self, trainer_id: int) -> List[User]:
        """Return all active students linked to a trainer."""
        links = (
            self.db.query(TrainerStudent)
            .filter(
                TrainerStudent.trainer_id == trainer_id,
                TrainerStudent.status == TrainerConstants.LINK_STATUS_ACTIVE,
            )
            .all()
        )
        if not links:
            return []
        student_ids = [link.student_id for link in links]
        return self.db.query(User).filter(User.id.in_(student_ids)).all()

    def get_student_link(self, trainer_id: int, student_id: int) -> TrainerStudent:
        """Return the active TrainerStudent link, or raise StudentNotLinkedError.

        Raises:
            StudentNotLinkedError: Student is not linked to this trainer.
        """
        link = (
            self.db.query(TrainerStudent)
            .filter(
                TrainerStudent.trainer_id == trainer_id,
                TrainerStudent.student_id == student_id,
                TrainerStudent.status == TrainerConstants.LINK_STATUS_ACTIVE,
            )
            .first()
        )
        if not link:
            raise StudentNotLinkedError(
                "Alumno no encontrado o no vinculado a este entrenador."
            )
        return link

    def get_student(self, trainer_id: int, student_id: int) -> User:
        """Return a student's User object after verifying trainer authorization.

        Raises:
            StudentNotLinkedError: Student is not linked to this trainer.
            UserNotFoundError: Student user record does not exist.
        """
        self.get_student_link(trainer_id, student_id)
        student = self.db.query(User).filter(User.id == student_id).first()
        if not student:
            raise UserNotFoundError("Alumno no encontrado.")
        return student

    def unlink_student(self, trainer_id: int, student_id: int) -> bool:
        """Revoke the active trainer-student link.

        Raises:
            StudentNotLinkedError: Student is not linked to this trainer.
        """
        link = self.get_student_link(trainer_id, student_id)
        link.status = TrainerConstants.LINK_STATUS_REVOKED
        self.db.commit()
        return True

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

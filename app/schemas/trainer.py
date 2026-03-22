from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TrainerInviteResponse(BaseModel):
    code: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    code: str


class StudentSummary(BaseModel):
    """Compact student info for trainer's student list."""
    id: int
    first_name: str
    last_name: str
    email: str
    objective: Optional[str] = None
    target_calories: Optional[float] = None
    weight_kg: Optional[float] = None
    linked_at: datetime

    model_config = {"from_attributes": True}


class TrainerStudentLinkResponse(BaseModel):
    id: int
    trainer_id: int
    student_id: int
    status: str
    linked_at: datetime

    model_config = {"from_attributes": True}

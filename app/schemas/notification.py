from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    type: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class EventBase(BaseModel):
    """Base event schema"""
    event_type: str
    title: str
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    event_timestamp: Optional[datetime] = None  # Defaults to now if not provided


class EventCreate(EventBase):
    """Event creation schema"""
    pass


class EventUpdate(BaseModel):
    """Event update schema (minimal - events are mostly append-only)"""
    title: Optional[str] = None
    description: Optional[str] = None
    # Note: event_type, data, and timestamp should not be editable for integrity


class EventResponse(BaseModel):
    """Event response schema"""
    id: int
    user_id: int
    event_type: str
    title: str
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    event_timestamp: datetime
    created_at: datetime
    is_deleted: bool
    
    model_config = {"from_attributes": True}


class EventFilter(BaseModel):
    """Event filtering parameters"""
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class EventStats(BaseModel):
    """Event statistics response"""
    total_events: int
    event_types: Dict[str, int]  # event_type -> count
    date_range: Dict[str, Optional[datetime]]  # first_event, last_event
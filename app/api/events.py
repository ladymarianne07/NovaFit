from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..dependencies import get_database_session, get_current_active_user
from ..schemas.event import EventCreate, EventResponse, EventUpdate, EventStats
from ..db.models import User, Event


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """Create a new event for the current user"""
    
    # Set event timestamp to now if not provided
    event_timestamp = event_data.event_timestamp
    if event_timestamp is None:
        event_timestamp = datetime.now(timezone.utc)
    
    # Create event
    event = Event(
        user_id=current_user.id,
        event_type=event_data.event_type,
        title=event_data.title,
        description=event_data.description,
        data=event_data.data,
        event_timestamp=event_timestamp
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event


@router.get("/", response_model=List[EventResponse])
async def get_user_events(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """Get events for the current user with optional filtering"""
    
    # Build query
    query = db.query(Event).filter(
        and_(
            Event.user_id == current_user.id,
            Event.is_deleted == False
        )
    )
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if start_date:
        query = query.filter(Event.event_timestamp >= start_date)
    if end_date:
        query = query.filter(Event.event_timestamp <= end_date)
    
    # Order by event timestamp (newest first) and apply pagination
    events = query.order_by(desc(Event.event_timestamp)).offset(offset).limit(limit).all()
    
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """Get a specific event by ID"""
    
    event = db.query(Event).filter(
        and_(
            Event.id == event_id,
            Event.user_id == current_user.id,
            Event.is_deleted == False
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """Update an event (limited fields for data integrity)"""
    
    event = db.query(Event).filter(
        and_(
            Event.id == event_id,
            Event.user_id == current_user.id,
            Event.is_deleted == False
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update allowed fields only
    if event_update.title is not None:
        event.title = event_update.title
    if event_update.description is not None:
        event.description = event_update.description
    
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """Soft delete an event (sets is_deleted=True for data integrity)"""
    
    event = db.query(Event).filter(
        and_(
            Event.id == event_id,
            Event.user_id == current_user.id,
            Event.is_deleted == False
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Soft delete
    event.is_deleted = True
    db.commit()


@router.get("/stats/summary", response_model=EventStats)
async def get_event_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """Get event statistics for the current user"""
    
    # Get all user events (not deleted)
    events = db.query(Event).filter(
        and_(
            Event.user_id == current_user.id,
            Event.is_deleted == False
        )
    ).all()
    
    if not events:
        return EventStats(
            total_events=0,
            event_types={},
            date_range={"first_event": None, "last_event": None}
        )
    
    # Calculate stats
    total_events = len(events)
    
    # Count by event type
    event_types = {}
    for event in events:
        event_type = event.event_type
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Date range
    event_dates = [event.event_timestamp for event in events]
    first_event = min(event_dates)
    last_event = max(event_dates)
    
    return EventStats(
        total_events=total_events,
        event_types=event_types,
        date_range={"first_event": first_event, "last_event": last_event}
    )
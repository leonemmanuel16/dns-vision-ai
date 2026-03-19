import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user, require_operator
from models.user import User
from schemas.event import EventResponse, EventListResponse
from services.event_service import list_events, get_event, delete_event

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventListResponse)
async def get_events(
    camera_id: uuid.UUID | None = Query(None),
    event_type: str | None = Query(None),
    zone_id: uuid.UUID | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    min_confidence: float | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    events, total = await list_events(
        db,
        camera_id=camera_id,
        event_type=event_type,
        zone_id=zone_id,
        start_time=start_time,
        end_time=end_time,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset,
    )
    return EventListResponse(
        events=[EventResponse(**e) for e in events],
        total=total,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    event = await get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    deleted = await delete_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

import uuid
from datetime import datetime
from pydantic import BaseModel


class EventResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    event_type: str
    label: str | None
    confidence: float | None
    bbox: dict | None
    zone_id: uuid.UUID | None
    snapshot_url: str | None = None
    clip_url: str | None = None
    thumbnail_url: str | None = None
    metadata: dict | None = None
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    events: list[EventResponse]
    total: int


class EventFilter(BaseModel):
    camera_id: uuid.UUID | None = None
    event_type: str | None = None
    zone_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    min_confidence: float | None = None
    limit: int = 50
    offset: int = 0

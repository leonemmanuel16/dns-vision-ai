import uuid
from datetime import datetime
from pydantic import BaseModel


class ZoneCreate(BaseModel):
    camera_id: uuid.UUID
    name: str
    zone_type: str  # roi, tripwire, perimeter
    points: list[dict]  # [{x, y}, ...]
    direction: str | None = None  # in, out, both
    detect_classes: list[str] = ["person", "vehicle"]
    is_enabled: bool = True
    config: dict | None = None


class ZoneUpdate(BaseModel):
    name: str | None = None
    zone_type: str | None = None
    points: list[dict] | None = None
    direction: str | None = None
    detect_classes: list[str] | None = None
    is_enabled: bool | None = None
    config: dict | None = None


class ZoneResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    name: str
    zone_type: str
    points: list[dict]
    direction: str | None
    detect_classes: list[str] | None
    is_enabled: bool
    config: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ZoneListResponse(BaseModel):
    zones: list[ZoneResponse]
    total: int

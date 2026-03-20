import uuid
import structlog
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from utils.minio_client import get_presigned_url

logger = structlog.get_logger()


async def list_events(
    db: AsyncSession,
    camera_id: uuid.UUID | None = None,
    event_type: str | None = None,
    zone_id: uuid.UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    min_confidence: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    conditions = []
    if camera_id:
        conditions.append(Event.camera_id == camera_id)
    if event_type:
        conditions.append(Event.event_type == event_type)
    if zone_id:
        conditions.append(Event.zone_id == zone_id)
    if start_time:
        conditions.append(Event.occurred_at >= start_time)
    if end_time:
        conditions.append(Event.occurred_at <= end_time)
    if min_confidence:
        conditions.append(Event.confidence >= min_confidence)

    where_clause = and_(*conditions) if conditions else True

    count_result = await db.execute(select(func.count(Event.id)).where(where_clause))
    total = count_result.scalar()

    result = await db.execute(
        select(Event)
        .where(where_clause)
        .order_by(Event.occurred_at.desc())
        .limit(limit)
        .offset(offset)
    )
    events = list(result.scalars().all())

    enriched = []
    for event in events:
        event_dict = {
            "id": event.id,
            "camera_id": event.camera_id,
            "event_type": event.event_type,
            "label": event.label,
            "confidence": event.confidence,
            "bbox": event.bbox,
            "zone_id": event.zone_id,
            "snapshot_url": get_presigned_url(event.snapshot_path) if event.snapshot_path else None,
            "clip_url": get_presigned_url(event.clip_path) if event.clip_path else None,
            "thumbnail_url": get_presigned_url(event.thumbnail_path) if event.thumbnail_path else None,
            "metadata": event.metadata_,
            "occurred_at": event.occurred_at,
            "created_at": event.created_at,
        }
        enriched.append(event_dict)

    return enriched, total


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> dict | None:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        return None

    return {
        "id": event.id,
        "camera_id": event.camera_id,
        "event_type": event.event_type,
        "label": event.label,
        "confidence": event.confidence,
        "bbox": event.bbox,
        "zone_id": event.zone_id,
        "snapshot_url": get_presigned_url(event.snapshot_path) if event.snapshot_path else None,
        "clip_url": get_presigned_url(event.clip_path) if event.clip_path else None,
        "thumbnail_url": get_presigned_url(event.thumbnail_path) if event.thumbnail_path else None,
        "metadata": event.metadata_,
        "occurred_at": event.occurred_at,
        "created_at": event.created_at,
    }


async def delete_event(db: AsyncSession, event_id: uuid.UUID) -> bool:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        return False
    await db.delete(event)
    await db.flush()
    return True

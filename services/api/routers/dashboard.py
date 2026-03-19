from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.camera import Camera
from models.event import Event

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStats(BaseModel):
    total_cameras: int
    online_cameras: int
    total_events_today: int
    total_events_week: int
    events_by_type: dict[str, int]
    recent_events: list[dict]


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Camera counts
    total_cams = (await db.execute(select(func.count(Camera.id)))).scalar()
    online_cams = (await db.execute(
        select(func.count(Camera.id)).where(Camera.is_online == True)
    )).scalar()

    # Events today
    events_today = (await db.execute(
        select(func.count(Event.id)).where(Event.occurred_at >= today_start)
    )).scalar()

    # Events this week
    events_week = (await db.execute(
        select(func.count(Event.id)).where(Event.occurred_at >= week_start)
    )).scalar()

    # Events by type (last 7 days)
    type_counts = await db.execute(
        select(Event.event_type, func.count(Event.id))
        .where(Event.occurred_at >= week_start)
        .group_by(Event.event_type)
    )
    events_by_type = {row[0]: row[1] for row in type_counts.all()}

    # Recent events
    recent = await db.execute(
        select(Event)
        .order_by(Event.occurred_at.desc())
        .limit(10)
    )
    recent_events = [
        {
            "id": str(e.id),
            "camera_id": str(e.camera_id),
            "event_type": e.event_type,
            "label": e.label,
            "confidence": e.confidence,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in recent.scalars().all()
    ]

    return DashboardStats(
        total_cameras=total_cams,
        online_cameras=online_cams,
        total_events_today=events_today,
        total_events_week=events_week,
        events_by_type=events_by_type,
        recent_events=recent_events,
    )

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select

from database import async_session
from models.camera import Camera
from models.event import Event
from utils.minio_client import upload_file

router = APIRouter(prefix="/ingest", tags=["Ingest"])


class MotionIngestRequest(BaseModel):
    event_id: str | None = None
    camera_name: str
    camera_ip: str
    event_type: str = "motion"
    label: str | None = "Movimiento"
    confidence: float | None = None
    occurred_at: datetime | None = None
    snapshot_path: str
    metadata: dict | None = None


@router.post("/motion")
async def ingest_motion(payload: MotionIngestRequest, x_ingest_token: str | None = Header(default=None)):
    expected = os.getenv("INGEST_TOKEN", "")
    if expected and x_ingest_token != expected:
        raise HTTPException(status_code=401, detail="Invalid ingest token")

    snap = Path(payload.snapshot_path)
    if not snap.exists():
        raise HTTPException(status_code=400, detail="snapshot_path not found")

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)

    # Upload snapshot to MinIO for dashboard rendering
    object_name = f"snapshots/{payload.camera_name}/{occurred_at.strftime('%Y/%m/%d')}/{snap.name}"
    data = snap.read_bytes()
    upload_file(object_name, data, content_type="image/jpeg")

    async with async_session() as db:
        # Find existing camera by IP first, then by name
        result = await db.execute(select(Camera).where(Camera.ip_address == payload.camera_ip))
        camera = result.scalar_one_or_none()

        if camera is None:
            result = await db.execute(select(Camera).where(Camera.name == payload.camera_name))
            camera = result.scalar_one_or_none()

        if camera is None:
            camera = Camera(
                name=payload.camera_name,
                ip_address=payload.camera_ip,
                manufacturer="Hikvision",
                model="Unknown",
                is_enabled=True,
                is_online=True,
                config={"source": "motion_detector_azure.py"},
            )
            db.add(camera)
            await db.flush()

        event = Event(
            id=uuid.UUID(payload.event_id) if payload.event_id else uuid.uuid4(),
            camera_id=camera.id,
            event_type=payload.event_type,
            label=payload.label,
            confidence=payload.confidence,
            bbox=None,
            snapshot_path=object_name,
            clip_path=None,
            thumbnail_path=None,
            metadata_=payload.metadata or {},
            occurred_at=occurred_at,
        )
        db.add(event)
        await db.commit()

    return {"ok": True, "camera_id": str(camera.id), "snapshot": object_name}

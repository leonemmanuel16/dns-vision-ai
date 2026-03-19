import os
import uuid
import json
import asyncio
import structlog
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as aioredis
from minio import Minio
import io

logger = structlog.get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://vision:changeme@localhost:5432/visionai")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "visionai")


class EventPublisher:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._pg_pool: asyncpg.Pool | None = None
        self._minio: Minio | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self):
        self._redis = aioredis.from_url(REDIS_URL)
        self._pg_pool = await asyncpg.create_pool(
            POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2,
            max_size=10,
        )
        self._minio = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        if not self._minio.bucket_exists(MINIO_BUCKET):
            self._minio.make_bucket(MINIO_BUCKET)
        logger.info("event_publisher_connected")

    async def close(self):
        if self._redis:
            await self._redis.aclose()
        if self._pg_pool:
            await self._pg_pool.close()

    def upload_snapshot(self, frame_bytes: bytes, camera_id: str) -> str:
        """Upload snapshot to MinIO, returns object path."""
        now = datetime.now(timezone.utc)
        object_name = f"snapshots/{camera_id}/{now.strftime('%Y/%m/%d')}/{uuid.uuid4()}.jpg"
        self._minio.put_object(
            MINIO_BUCKET,
            object_name,
            io.BytesIO(frame_bytes),
            length=len(frame_bytes),
            content_type="image/jpeg",
        )
        return object_name

    async def publish_event(
        self,
        camera_id: str,
        event_type: str,
        label: str,
        confidence: float,
        bbox: dict,
        snapshot_path: str | None = None,
        zone_id: str | None = None,
        tracker_id: int | None = None,
    ):
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Insert into PostgreSQL
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (id, camera_id, event_type, label, confidence, bbox,
                    snapshot_path, zone_id, metadata, occurred_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                uuid.UUID(event_id),
                uuid.UUID(camera_id),
                event_type,
                label,
                confidence,
                json.dumps(bbox),
                snapshot_path,
                uuid.UUID(zone_id) if zone_id else None,
                json.dumps({"tracker_id": tracker_id}) if tracker_id else "{}",
                now,
            )

        # Publish to Redis Streams
        await self._redis.xadd(
            "detection_events",
            {
                "event_id": event_id,
                "camera_id": camera_id,
                "event_type": event_type,
                "label": label,
                "confidence": str(confidence),
                "bbox": json.dumps(bbox),
                "snapshot_path": snapshot_path or "",
                "zone_id": zone_id or "",
                "occurred_at": now.isoformat(),
            },
            maxlen=10000,
        )

        logger.info(
            "event_published",
            event_id=event_id,
            camera_id=camera_id,
            event_type=event_type,
            label=label,
            confidence=confidence,
        )

    async def load_zones(self, camera_id: str) -> list[dict]:
        """Load zones for a camera from PostgreSQL."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, zone_type, points, direction, detect_classes, is_enabled, config
                FROM zones WHERE camera_id = $1 AND is_enabled = true
                """,
                uuid.UUID(camera_id),
            )
            return [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "zone_type": row["zone_type"],
                    "points": json.loads(row["points"]) if isinstance(row["points"], str) else row["points"],
                    "direction": row["direction"],
                    "detect_classes": row["detect_classes"],
                    "is_enabled": row["is_enabled"],
                }
                for row in rows
            ]

    async def get_active_cameras(self) -> list[dict]:
        """Get active cameras from PostgreSQL."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, rtsp_sub_stream, rtsp_main_stream
                FROM cameras WHERE is_enabled = true AND is_online = true
                """
            )
            return [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "rtsp_url": row["rtsp_sub_stream"] or row["rtsp_main_stream"],
                }
                for row in rows
                if row["rtsp_sub_stream"] or row["rtsp_main_stream"]
            ]

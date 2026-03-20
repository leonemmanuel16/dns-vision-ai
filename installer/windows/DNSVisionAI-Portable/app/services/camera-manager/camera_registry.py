"""Camera registry - Track discovered cameras in Redis and PostgreSQL."""

import json
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class CameraRegistry:
    """Manages camera state in Redis (fast lookup) and PostgreSQL (persistence)."""

    def __init__(self, redis_url: str, postgres_url: str):
        self.redis_url = redis_url
        self.postgres_url = postgres_url
        self._redis: Optional[redis.Redis] = None
        self._pg_pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize Redis and PostgreSQL connections."""
        self._redis = redis.from_url(self.redis_url, decode_responses=True)
        self._pg_pool = await asyncpg.create_pool(self.postgres_url, min_size=2, max_size=10)
        logger.info("camera_registry_connected")

    async def close(self):
        """Close connections."""
        if self._redis:
            await self._redis.close()
        if self._pg_pool:
            await self._pg_pool.close()

    async def upsert_camera(self, camera_data: dict) -> str:
        """Insert or update a camera in PostgreSQL and Redis.

        Returns the camera UUID.
        """
        async with self._pg_pool.acquire() as conn:
            # Check if camera already exists by IP
            existing = await conn.fetchrow(
                "SELECT id FROM cameras WHERE ip_address = $1",
                camera_data["ip"],
            )

            now = datetime.now(timezone.utc)

            if existing:
                camera_id = str(existing["id"])
                await conn.execute(
                    """UPDATE cameras SET
                        manufacturer = COALESCE($2, manufacturer),
                        model = COALESCE($3, model),
                        firmware = COALESCE($4, firmware),
                        serial_number = COALESCE($5, serial_number),
                        mac_address = COALESCE($6, mac_address),
                        rtsp_main_stream = COALESCE($7, rtsp_main_stream),
                        rtsp_sub_stream = COALESCE($8, rtsp_sub_stream),
                        onvif_profile_token = COALESCE($9, onvif_profile_token),
                        has_ptz = $10,
                        is_online = true,
                        last_seen_at = $11,
                        updated_at = $11
                    WHERE id = $12""",
                    camera_data.get("manufacturer"),
                    camera_data.get("model"),
                    camera_data.get("firmware"),
                    camera_data.get("serial_number"),
                    camera_data.get("mac_address"),
                    camera_data.get("rtsp_main_stream"),
                    camera_data.get("rtsp_sub_stream"),
                    camera_data.get("profile_token"),
                    camera_data.get("has_ptz", False),
                    now,
                    existing["id"],
                )
                logger.info("camera_updated", camera_id=camera_id, ip=camera_data["ip"])
            else:
                name = camera_data.get("name") or f"Camera {camera_data['ip']}"
                row = await conn.fetchrow(
                    """INSERT INTO cameras
                        (name, ip_address, onvif_port, username, password_encrypted,
                         manufacturer, model, firmware, serial_number, mac_address,
                         rtsp_main_stream, rtsp_sub_stream, onvif_profile_token,
                         has_ptz, is_online, last_seen_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,true,$15)
                    RETURNING id""",
                    name,
                    camera_data["ip"],
                    camera_data.get("port", 80),
                    camera_data.get("username"),
                    camera_data.get("password"),
                    camera_data.get("manufacturer"),
                    camera_data.get("model"),
                    camera_data.get("firmware"),
                    camera_data.get("serial_number"),
                    camera_data.get("mac_address"),
                    camera_data.get("rtsp_main_stream"),
                    camera_data.get("rtsp_sub_stream"),
                    camera_data.get("profile_token"),
                    camera_data.get("has_ptz", False),
                    now,
                )
                camera_id = str(row["id"])
                logger.info("camera_registered", camera_id=camera_id, ip=camera_data["ip"])

        # Cache in Redis
        redis_key = f"camera:{camera_id}"
        await self._redis.hset(redis_key, mapping={
            "id": camera_id,
            "ip": camera_data["ip"],
            "port": str(camera_data.get("port", 80)),
            "name": camera_data.get("name") or f"Camera {camera_data['ip']}",
            "rtsp_main": camera_data.get("rtsp_main_stream", ""),
            "rtsp_sub": camera_data.get("rtsp_sub_stream", ""),
            "is_online": "1",
            "last_seen": now.isoformat(),
        })
        await self._redis.sadd("cameras:active", camera_id)

        # Publish discovery event
        await self._redis.xadd("events:cameras", {
            "type": "camera_discovered",
            "camera_id": camera_id,
            "ip": camera_data["ip"],
            "timestamp": now.isoformat(),
        })

        return camera_id

    async def set_camera_offline(self, camera_id: str):
        """Mark camera as offline."""
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE cameras SET is_online = false, updated_at = NOW() WHERE id = $1::uuid",
                camera_id,
            )
        await self._redis.hset(f"camera:{camera_id}", "is_online", "0")
        await self._redis.srem("cameras:active", camera_id)
        logger.info("camera_offline", camera_id=camera_id)

    async def set_camera_online(self, camera_id: str):
        """Mark camera as online."""
        now = datetime.now(timezone.utc)
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE cameras SET is_online = true, last_seen_at = $1, updated_at = $1 WHERE id = $2::uuid",
                now, camera_id,
            )
        await self._redis.hset(f"camera:{camera_id}", mapping={
            "is_online": "1",
            "last_seen": now.isoformat(),
        })
        await self._redis.sadd("cameras:active", camera_id)

    async def get_all_cameras(self) -> list:
        """Get all cameras from PostgreSQL."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM cameras WHERE is_enabled = true ORDER BY created_at"
            )
            return [dict(r) for r in rows]

    async def get_active_camera_ids(self) -> list:
        """Get IDs of active (online + enabled) cameras from Redis."""
        return list(await self._redis.smembers("cameras:active"))

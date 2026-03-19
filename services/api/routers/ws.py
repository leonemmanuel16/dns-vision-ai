import json
import asyncio
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from config import get_settings

logger = structlog.get_logger()
router = APIRouter()

settings = get_settings()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("ws_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("ws_disconnected", total=len(self.active_connections))

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Start Redis stream listener in background
        redis_task = asyncio.create_task(_listen_redis_events(websocket))
        try:
            while True:
                # Keep connection alive, handle client messages
                data = await websocket.receive_text()
                # Client can send ping or filter commands
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            redis_task.cancel()
    finally:
        manager.disconnect(websocket)


async def _listen_redis_events(websocket: WebSocket):
    """Listen to Redis Streams for detection events and forward to WebSocket."""
    try:
        r = aioredis.from_url(settings.redis_url)
        last_id = "$"
        while True:
            try:
                streams = await r.xread({"detection_events": last_id}, count=10, block=1000)
                for stream_name, messages in streams:
                    for msg_id, data in messages:
                        last_id = msg_id
                        event = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}
                        await websocket.send_json({"type": "detection", "data": event})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("redis_stream_error", error=str(e))
                await asyncio.sleep(1)
        await r.aclose()
    except asyncio.CancelledError:
        pass

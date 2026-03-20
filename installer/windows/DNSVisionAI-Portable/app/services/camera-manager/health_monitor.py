"""Health monitor - Periodic camera health checks."""

import asyncio
import socket
from typing import Optional

import structlog

from camera_registry import CameraRegistry

logger = structlog.get_logger()


async def check_camera_reachable(ip: str, port: int = 80, timeout: float = 5.0) -> bool:
    """Check if a camera is reachable via TCP connection."""
    try:
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = await loop.run_in_executor(None, sock.connect_ex, (ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


async def run_health_checks(
    registry: CameraRegistry,
    interval: int = 60,
):
    """Continuously check camera health and update status."""
    logger.info("health_monitor_started", interval=interval)

    while True:
        try:
            cameras = await registry.get_all_cameras()
            for camera in cameras:
                camera_id = str(camera["id"])
                ip = camera["ip_address"]
                port = camera.get("onvif_port", 80)

                reachable = await check_camera_reachable(ip, port)

                was_online = camera.get("is_online", True)

                if reachable and not was_online:
                    await registry.set_camera_online(camera_id)
                    logger.info("camera_back_online", camera_id=camera_id, ip=ip)
                elif not reachable and was_online:
                    await registry.set_camera_offline(camera_id)
                    logger.warning("camera_went_offline", camera_id=camera_id, ip=ip)
                elif reachable:
                    # Update last_seen timestamp
                    await registry.set_camera_online(camera_id)

        except Exception as e:
            logger.error("health_check_error", error=str(e))

        await asyncio.sleep(interval)

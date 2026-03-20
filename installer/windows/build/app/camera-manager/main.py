"""Camera Manager - ONVIF discovery, registration, health monitoring, and go2rtc config."""

import asyncio
import os
import signal
import sys

import structlog

from onvif_discovery import discover_cameras
from onvif_client import get_camera_info
from camera_registry import CameraRegistry
from health_monitor import run_health_checks
from go2rtc_config import write_config

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.environ.get("POSTGRES_URL", "postgresql://vision:changeme@localhost:5432/visionai")
DISCOVERY_INTERVAL = int(os.environ.get("DISCOVERY_INTERVAL", "300"))
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", "60"))
ONVIF_DEFAULT_USER = os.environ.get("ONVIF_DEFAULT_USER", "admin")
ONVIF_DEFAULT_PASS = os.environ.get("ONVIF_DEFAULT_PASS", "admin123")
GO2RTC_CONFIG_PATH = os.environ.get("GO2RTC_CONFIG_PATH", "/config/go2rtc.yaml")


async def run_discovery(registry: CameraRegistry):
    """Discover ONVIF cameras and register them."""
    logger.info("discovery_starting")
    discovered = await discover_cameras(timeout=5.0)
    logger.info("discovery_found", count=len(discovered))

    registered_cameras = []

    for cam in discovered:
        ip = cam["ip"]
        port = cam.get("port", 80)

        camera_info = await get_camera_info(
            ip=ip,
            port=port,
            username=ONVIF_DEFAULT_USER,
            password=ONVIF_DEFAULT_PASS,
        )

        if camera_info is None:
            logger.warning("discovery_camera_unreachable", ip=ip)
            continue

        camera_data = {
            "ip": ip,
            "port": port,
            "username": ONVIF_DEFAULT_USER,
            "password": ONVIF_DEFAULT_PASS,
            "name": f"{camera_info.manufacturer} {camera_info.model}".strip() or f"Camera {ip}",
            "manufacturer": camera_info.manufacturer,
            "model": camera_info.model,
            "firmware": camera_info.firmware,
            "serial_number": camera_info.serial_number,
            "mac_address": camera_info.mac_address,
            "rtsp_main_stream": camera_info.rtsp_main_stream,
            "rtsp_sub_stream": camera_info.rtsp_sub_stream,
            "profile_token": camera_info.profile_token,
            "has_ptz": camera_info.has_ptz,
        }

        camera_id = await registry.upsert_camera(camera_data)
        camera_data["id"] = camera_id
        registered_cameras.append(camera_data)
        logger.info("discovery_camera_registered", camera_id=camera_id, ip=ip)

    # Update go2rtc config with all known cameras
    all_cameras = await registry.get_all_cameras()
    go2rtc_cameras = [
        {
            "name": c.get("name", f"Camera {c['ip_address']}"),
            "ip": c["ip_address"],
            "rtsp_main_stream": c.get("rtsp_main_stream", ""),
            "rtsp_sub_stream": c.get("rtsp_sub_stream", ""),
        }
        for c in all_cameras
        if c.get("rtsp_main_stream")
    ]

    if go2rtc_cameras:
        write_config(go2rtc_cameras, config_path=GO2RTC_CONFIG_PATH)

    logger.info("discovery_complete", registered=len(registered_cameras), total_cameras=len(all_cameras))
    return registered_cameras


async def discovery_loop(registry: CameraRegistry):
    """Run discovery periodically."""
    while True:
        try:
            await run_discovery(registry)
        except Exception as e:
            logger.error("discovery_loop_error", error=str(e))
        await asyncio.sleep(DISCOVERY_INTERVAL)


async def main():
    """Main entry point - start discovery and health monitoring."""
    logger.info(
        "camera_manager_starting",
        redis_url=REDIS_URL,
        discovery_interval=DISCOVERY_INTERVAL,
        health_check_interval=HEALTH_CHECK_INTERVAL,
    )

    registry = CameraRegistry(redis_url=REDIS_URL, postgres_url=POSTGRES_URL)
    await registry.connect()

    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("shutdown_signal_received")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    # Run initial discovery immediately
    try:
        await run_discovery(registry)
    except Exception as e:
        logger.error("initial_discovery_failed", error=str(e))

    # Start background tasks
    tasks = [
        asyncio.create_task(discovery_loop(registry)),
        asyncio.create_task(run_health_checks(registry, interval=HEALTH_CHECK_INTERVAL)),
    ]

    logger.info("camera_manager_running")

    # Wait for shutdown signal
    await shutdown_event.wait()

    logger.info("camera_manager_shutting_down")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await registry.close()
    logger.info("camera_manager_stopped")


if __name__ == "__main__":
    asyncio.run(main())

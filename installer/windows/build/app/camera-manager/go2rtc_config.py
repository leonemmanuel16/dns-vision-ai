"""go2rtc config generator - Auto-generate go2rtc.yaml from discovered cameras."""

import re
from typing import List

import yaml
import structlog

logger = structlog.get_logger()

GO2RTC_CONFIG_PATH = "/config/go2rtc.yaml"


def sanitize_name(name: str) -> str:
    """Convert camera name to a valid go2rtc stream name."""
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    return name.strip('_') or 'camera'


def generate_config(cameras: List[dict]) -> dict:
    """Generate go2rtc configuration from camera list.

    Each camera dict should have: name, rtsp_main_stream, rtsp_sub_stream
    """
    config = {
        "api": {"listen": ":1984"},
        "rtsp": {"listen": ":8554"},
        "webrtc": {
            "listen": ":8555",
            "candidates": ["stun:8555"],
        },
        "streams": {},
    }

    for camera in cameras:
        name = sanitize_name(camera.get("name", f"camera_{camera.get('ip', 'unknown')}"))
        main_stream = camera.get("rtsp_main_stream", "")
        sub_stream = camera.get("rtsp_sub_stream", "")

        if main_stream:
            config["streams"][name] = main_stream
        if sub_stream and sub_stream != main_stream:
            config["streams"][f"{name}_sub"] = sub_stream

    return config


def write_config(cameras: List[dict], config_path: str = GO2RTC_CONFIG_PATH) -> bool:
    """Write go2rtc.yaml config file from camera list."""
    try:
        config = generate_config(cameras)

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(
            "go2rtc_config_written",
            path=config_path,
            stream_count=len(config["streams"]),
        )
        return True
    except Exception as e:
        logger.error("go2rtc_config_error", error=str(e))
        return False

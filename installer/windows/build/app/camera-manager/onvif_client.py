"""ONVIF client - Connect to cameras and get device info, streams, capabilities."""

import asyncio
from typing import Optional
from dataclasses import dataclass, field

import structlog
from onvif import ONVIFCamera

logger = structlog.get_logger()


@dataclass
class CameraInfo:
    """Camera information retrieved via ONVIF."""
    ip: str
    port: int
    manufacturer: str = ""
    model: str = ""
    firmware: str = ""
    serial_number: str = ""
    mac_address: str = ""
    rtsp_main_stream: str = ""
    rtsp_sub_stream: str = ""
    profile_token: str = ""
    has_ptz: bool = False
    profiles: list = field(default_factory=list)


async def get_camera_info(
    ip: str,
    port: int,
    username: str,
    password: str,
) -> Optional[CameraInfo]:
    """Connect to an ONVIF camera and retrieve its info and stream URIs."""
    try:
        cam = ONVIFCamera(ip, port, username, password)
        await asyncio.to_thread(cam.update_xaddrs)

        info = CameraInfo(ip=ip, port=port)

        # Get device information
        try:
            device_service = cam.create_devicemgmt_service()
            device_info = await asyncio.to_thread(device_service.GetDeviceInformation)
            info.manufacturer = getattr(device_info, "Manufacturer", "")
            info.model = getattr(device_info, "Model", "")
            info.firmware = getattr(device_info, "FirmwareVersion", "")
            info.serial_number = getattr(device_info, "SerialNumber", "")
            logger.info(
                "camera_device_info",
                ip=ip,
                manufacturer=info.manufacturer,
                model=info.model,
            )
        except Exception as e:
            logger.warning("camera_device_info_error", ip=ip, error=str(e))

        # Get network interfaces for MAC address
        try:
            device_service = cam.create_devicemgmt_service()
            network_interfaces = await asyncio.to_thread(
                device_service.GetNetworkInterfaces
            )
            if network_interfaces:
                hw = getattr(network_interfaces[0], "Info", None)
                if hw:
                    info.mac_address = getattr(hw, "HwAddress", "")
        except Exception as e:
            logger.debug("camera_mac_error", ip=ip, error=str(e))

        # Get media profiles and stream URIs
        try:
            media_service = cam.create_media_service()
            profiles = await asyncio.to_thread(media_service.GetProfiles)

            if profiles:
                info.profiles = [
                    {"token": p.token, "name": getattr(p, "Name", "")}
                    for p in profiles
                ]

                # Main stream (first profile - usually highest resolution)
                main_profile = profiles[0]
                info.profile_token = main_profile.token
                stream_uri = await asyncio.to_thread(
                    media_service.GetStreamUri,
                    {
                        "StreamSetup": {
                            "Stream": "RTP-Unicast",
                            "Transport": {"Protocol": "RTSP"},
                        },
                        "ProfileToken": main_profile.token,
                    },
                )
                info.rtsp_main_stream = _inject_credentials(
                    stream_uri.Uri, username, password
                )

                # Sub stream (second profile - usually lower resolution)
                if len(profiles) > 1:
                    sub_profile = profiles[1]
                    sub_uri = await asyncio.to_thread(
                        media_service.GetStreamUri,
                        {
                            "StreamSetup": {
                                "Stream": "RTP-Unicast",
                                "Transport": {"Protocol": "RTSP"},
                            },
                            "ProfileToken": sub_profile.token,
                        },
                    )
                    info.rtsp_sub_stream = _inject_credentials(
                        sub_uri.Uri, username, password
                    )
                else:
                    info.rtsp_sub_stream = info.rtsp_main_stream

                logger.info(
                    "camera_streams",
                    ip=ip,
                    main=info.rtsp_main_stream,
                    sub=info.rtsp_sub_stream,
                )
        except Exception as e:
            logger.warning("camera_media_error", ip=ip, error=str(e))

        # Check PTZ capability
        try:
            ptz_service = cam.create_ptz_service()
            if ptz_service:
                info.has_ptz = True
                logger.info("camera_ptz_available", ip=ip)
        except Exception:
            info.has_ptz = False

        return info

    except Exception as e:
        logger.error("camera_connect_error", ip=ip, port=port, error=str(e))
        return None


def _inject_credentials(uri: str, username: str, password: str) -> str:
    """Inject username:password into an RTSP URI."""
    if not uri:
        return uri
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(uri)
    netloc = f"{username}:{password}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


async def ptz_move(
    ip: str,
    port: int,
    username: str,
    password: str,
    profile_token: str,
    pan: float = 0.0,
    tilt: float = 0.0,
    zoom: float = 0.0,
) -> bool:
    """Send PTZ continuous move command to camera."""
    try:
        cam = ONVIFCamera(ip, port, username, password)
        await asyncio.to_thread(cam.update_xaddrs)

        ptz_service = cam.create_ptz_service()
        request = ptz_service.create_type("ContinuousMove")
        request.ProfileToken = profile_token
        request.Velocity = {
            "PanTilt": {"x": pan, "y": tilt},
            "Zoom": {"x": zoom},
        }
        await asyncio.to_thread(ptz_service.ContinuousMove, request)
        logger.info("ptz_move", ip=ip, pan=pan, tilt=tilt, zoom=zoom)
        return True
    except Exception as e:
        logger.error("ptz_move_error", ip=ip, error=str(e))
        return False


async def ptz_stop(
    ip: str,
    port: int,
    username: str,
    password: str,
    profile_token: str,
) -> bool:
    """Stop PTZ movement."""
    try:
        cam = ONVIFCamera(ip, port, username, password)
        await asyncio.to_thread(cam.update_xaddrs)

        ptz_service = cam.create_ptz_service()
        await asyncio.to_thread(
            ptz_service.Stop, {"ProfileToken": profile_token}
        )
        logger.info("ptz_stop", ip=ip)
        return True
    except Exception as e:
        logger.error("ptz_stop_error", ip=ip, error=str(e))
        return False

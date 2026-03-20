"""ONVIF WS-Discovery - Find cameras on the network."""

import asyncio
import socket
import struct
import uuid
from typing import List

import structlog

logger = structlog.get_logger()

WS_DISCOVERY_MULTICAST = "239.255.255.250"
WS_DISCOVERY_PORT = 3702

PROBE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
            xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <e:Header>
        <w:MessageID>uuid:{message_id}</w:MessageID>
        <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
        <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
    </e:Header>
    <e:Body>
        <d:Probe>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
        </d:Probe>
    </e:Body>
</e:Envelope>"""


def _parse_xaddrs(response: str) -> List[str]:
    """Extract XAddrs (service URLs) from WS-Discovery response."""
    xaddrs = []
    import re
    matches = re.findall(r'<[^>]*XAddrs[^>]*>([^<]+)</[^>]*XAddrs>', response)
    for match in matches:
        for addr in match.strip().split():
            if addr.startswith("http"):
                xaddrs.append(addr)
    return xaddrs


def _extract_ip_from_xaddr(xaddr: str) -> str:
    """Extract IP address from an XAddr URL."""
    from urllib.parse import urlparse
    parsed = urlparse(xaddr)
    return parsed.hostname or ""


async def discover_cameras(timeout: float = 5.0) -> List[dict]:
    """Send WS-Discovery probe and collect ONVIF camera responses.

    Returns list of dicts with keys: ip, port, xaddr
    """
    message_id = str(uuid.uuid4())
    probe = PROBE_TEMPLATE.format(message_id=message_id).encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_MULTICAST_TTL,
        struct.pack("b", 2),
    )
    sock.settimeout(timeout)

    discovered = {}

    try:
        sock.sendto(probe, (WS_DISCOVERY_MULTICAST, WS_DISCOVERY_PORT))
        logger.info("ws_discovery_probe_sent", multicast=WS_DISCOVERY_MULTICAST)

        end_time = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = end_time - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            try:
                data, addr = sock.recvfrom(65535)
                response = data.decode("utf-8", errors="ignore")
                xaddrs = _parse_xaddrs(response)
                for xaddr in xaddrs:
                    ip = _extract_ip_from_xaddr(xaddr)
                    if ip and ip not in discovered:
                        from urllib.parse import urlparse
                        parsed = urlparse(xaddr)
                        port = parsed.port or 80
                        discovered[ip] = {
                            "ip": ip,
                            "port": port,
                            "xaddr": xaddr,
                        }
                        logger.info("camera_discovered", ip=ip, port=port, xaddr=xaddr)
            except socket.timeout:
                break
            except Exception as e:
                logger.warning("ws_discovery_recv_error", error=str(e))
                break
    finally:
        sock.close()

    cameras = list(discovered.values())
    logger.info("ws_discovery_complete", cameras_found=len(cameras))
    return cameras

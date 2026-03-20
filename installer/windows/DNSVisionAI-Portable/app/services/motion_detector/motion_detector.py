"""
DNS Vision AI — Motion Detector v2 (HTTP Snapshots)
Usa snapshots HTTP de la cámara (más estable que RTSP con H.265).
Detecta movimiento, guarda eventos con 5 snapshots.
"""

import cv2
import os
import time
import json
import logging
import urllib.request
import ssl
import numpy as np
from datetime import datetime
from pathlib import Path

# Config
CAMERA_IP = os.environ.get("CAMERA_IP", "192.168.8.26")
CAMERA_USER = os.environ.get("CAMERA_USER", "dns")
CAMERA_PASS = os.environ.get("CAMERA_PASS", "admin12345")
CAMERA_NAME = os.environ.get("CAMERA_NAME", "hikvision_principal")
SNAPSHOT_URL = os.environ.get("SNAPSHOT_URL", "")  # auto-detect if empty
EVENTS_DIR = os.environ.get("EVENTS_DIR", "/home/manny/dns-vision-ai/events")
MOTION_THRESHOLD = int(os.environ.get("MOTION_THRESHOLD", "5000"))
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "10"))
FRAMES_PER_EVENT = int(os.environ.get("FRAMES_PER_EVENT", "5"))
FRAME_INTERVAL = float(os.environ.get("FRAME_INTERVAL", "1.0"))
CHECK_INTERVAL = float(os.environ.get("CHECK_INTERVAL", "1.0"))  # seconds between checks
RESIZE_WIDTH = int(os.environ.get("RESIZE_WIDTH", "640"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("motion_detector")


def ensure_dirs():
    Path(f"{EVENTS_DIR}/snapshots").mkdir(parents=True, exist_ok=True)
    Path(f"{EVENTS_DIR}/metadata").mkdir(parents=True, exist_ok=True)


def setup_auth(url, user, password):
    """Setup digest auth for Hikvision cameras"""
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, user, password)
    auth_handler = urllib.request.HTTPDigestAuthHandler(password_mgr)
    opener = urllib.request.build_opener(auth_handler)
    return opener


def grab_snapshot(opener, url, timeout=5):
    """Grab a JPEG snapshot from the camera via HTTP"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = opener.open(url, timeout=timeout)
        data = response.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        log.warning(f"⚠️ Snapshot error: {e}")
        return None


def detect_motion(frame1_gray, frame2_gray):
    """Detecta movimiento entre dos frames grises"""
    diff = cv2.absdiff(frame1_gray, frame2_gray)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_area = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 500)
    return total_area > MOTION_THRESHOLD, total_area, contours


def capture_event_frames(opener, url, event_id):
    """Captura N snapshots de alta resolución para el evento"""
    frames_saved = []
    for i in range(FRAMES_PER_EVENT):
        img = grab_snapshot(opener, url)
        if img is None:
            log.warning(f"  ⚠️ Frame {i+1} no capturado")
            continue
        filename = f"{event_id}_frame_{i+1}.jpg"
        filepath = f"{EVENTS_DIR}/snapshots/{filename}"
        cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frames_saved.append(filename)
        log.info(f"  📸 Frame {i+1}/{FRAMES_PER_EVENT} guardado ({img.shape[1]}x{img.shape[0]})")
        if i < FRAMES_PER_EVENT - 1:
            time.sleep(FRAME_INTERVAL)
    return frames_saved


def save_event_metadata(event_id, motion_area, frames):
    """Guarda metadata del evento como JSON"""
    event = {
        "event_id": event_id,
        "camera": CAMERA_NAME,
        "camera_ip": CAMERA_IP,
        "timestamp": datetime.now().isoformat(),
        "motion_area": motion_area,
        "frames": frames,
        "frames_count": len(frames),
        "analyzed": False,
        "analysis_result": None,
        "alert_sent": False
    }
    filepath = f"{EVENTS_DIR}/metadata/{event_id}.json"
    with open(filepath, "w") as f:
        json.dump(event, f, indent=2)
    log.info(f"  📋 Metadata guardada: {event_id}.json")
    return event


def run():
    ensure_dirs()

    # Auto-detect snapshot URL
    snapshot_url = SNAPSHOT_URL or f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/picture"

    log.info("=" * 60)
    log.info("🎥 DNS Vision AI — Motion Detector v2 (HTTP Snapshots)")
    log.info(f"📍 Cámara: {CAMERA_NAME} ({CAMERA_IP})")
    log.info(f"🔗 Snapshot URL: {snapshot_url}")
    log.info(f"⚙️  Threshold: {MOTION_THRESHOLD} | Cooldown: {COOLDOWN_SECONDS}s")
    log.info(f"📸 Frames por evento: {FRAMES_PER_EVENT}")
    log.info(f"⏱️  Check interval: {CHECK_INTERVAL}s")
    log.info("=" * 60)

    opener = setup_auth(snapshot_url, CAMERA_USER, CAMERA_PASS)

    # Test connection
    test = grab_snapshot(opener, snapshot_url)
    if test is None:
        log.error("❌ No se pudo conectar a la cámara")
        return
    log.info(f"✅ Conectado! Resolución: {test.shape[1]}x{test.shape[0]}")

    # First frame for comparison
    small = cv2.resize(test, (RESIZE_WIDTH, int(test.shape[0] * RESIZE_WIDTH / test.shape[1])))
    prev_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

    last_event_time = 0
    event_count = 0
    check_count = 0
    start_time = time.time()

    log.info("👀 Monitoreando movimiento...")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            check_count += 1

            img = grab_snapshot(opener, snapshot_url)
            if img is None:
                continue

            small = cv2.resize(img, (RESIZE_WIDTH, int(img.shape[0] * RESIZE_WIDTH / img.shape[1])))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            has_motion, area, contours = detect_motion(prev_gray, gray)
            prev_gray = gray

            if has_motion:
                now = time.time()
                if now - last_event_time < COOLDOWN_SECONDS:
                    continue

                last_event_time = now
                event_count += 1
                event_id = f"{CAMERA_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{event_count:04d}"

                log.info(f"🚨 MOVIMIENTO DETECTADO! Área: {area:.0f} | Evento: {event_id}")

                # Guardar el frame que detectó movimiento
                trigger_file = f"{event_id}_trigger.jpg"
                cv2.imwrite(f"{EVENTS_DIR}/snapshots/{trigger_file}", img, [cv2.IMWRITE_JPEG_QUALITY, 85])

                # Capturar frames adicionales
                frames = [trigger_file] + capture_event_frames(opener, snapshot_url, event_id)

                # Guardar metadata
                event = save_event_metadata(event_id, area, frames)

                log.info(f"  ✅ Evento #{event_count} registrado con {len(frames)} frames")
                log.info(f"  ⏳ Cooldown {COOLDOWN_SECONDS}s...")

            # Stats cada 5 minutos
            if check_count % 300 == 0:
                elapsed = time.time() - start_time
                log.info(f"📊 Stats: {check_count} checks | {event_count} eventos | {elapsed/60:.0f} min uptime")

    except KeyboardInterrupt:
        log.info("\n⛔ Detenido por usuario")
    finally:
        elapsed = time.time() - start_time
        log.info(f"📊 Resumen: {event_count} eventos en {elapsed/60:.1f} minutos | {check_count} checks")


if __name__ == "__main__":
    run()

"""
DNS Vision AI — Motion Detector for Fisheye Camera
Detects motion, saves trigger frame + 3 dewarped panels, sends WhatsApp alert.
"""

import cv2
import os
import time
import json
import logging
import shutil
import urllib.request
import urllib.error
import ssl
import numpy as np
from datetime import datetime
from pathlib import Path

# ─── Config ───
CAMERA_IP = os.environ.get("FISHEYE_IP", "192.168.8.64")
CAMERA_USER = os.environ.get("FISHEYE_USER", "dns")
CAMERA_PASS = os.environ.get("FISHEYE_PASS", "admin12345")
CAMERA_NAME = os.environ.get("FISHEYE_NAME", "hikvision_fisheye")
EVENTS_DIR = os.environ.get("EVENTS_DIR", "/home/manny/dns-vision-ai/events")
BANK_DIR = os.environ.get("BANK_DIR", "/home/manny/dns-vision-ai/image_bank")
WORKSPACE_DIR = "/home/manny/.openclaw/workspace"
MOTION_THRESHOLD = int(os.environ.get("FISHEYE_MOTION_THRESHOLD", "8000"))
COOLDOWN_SECONDS = int(os.environ.get("FISHEYE_COOLDOWN", "15"))
CHECK_INTERVAL = float(os.environ.get("FISHEYE_CHECK_INTERVAL", "1.5"))
RESIZE_WIDTH = int(os.environ.get("FISHEYE_RESIZE_WIDTH", "640"))
SEND_WHATSAPP = os.environ.get("FISHEYE_SEND_WHATSAPP", "false").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("dns_vision_fisheye")


def ensure_dirs():
    for d in [
        f"{EVENTS_DIR}/snapshots",
        f"{EVENTS_DIR}/metadata",
        f"{EVENTS_DIR}/fisheye_panels",
        f"{BANK_DIR}/fisheye",
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)


def setup_camera_auth():
    url = f"http://{CAMERA_IP}"
    pm = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pm.add_password(None, url, CAMERA_USER, CAMERA_PASS)
    return urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(pm))


def grab_snapshot(opener):
    try:
        url = f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/picture"
        resp = opener.open(url, timeout=8)
        data = resp.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        log.warning(f"⚠️ Snapshot: {e}")
        return None


def detect_motion(prev_gray, curr_gray):
    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big_contours = [c for c in contours if cv2.contourArea(c) > 1500]
    total_area = sum(cv2.contourArea(c) for c in big_contours)
    return total_area > MOTION_THRESHOLD, total_area, len(big_contours)


def dewarp_panel(img, cx, cy, radius, start_deg, end_deg, out_w=1280, out_h=640):
    """Dewarping equirectangular limpio."""
    angles = np.linspace(np.radians(start_deg), np.radians(end_deg), out_w, dtype=np.float32)
    radii = np.linspace(radius * 0.95, radius * 0.15, out_h, dtype=np.float32)
    angle_grid, radius_grid = np.meshgrid(angles, radii)
    map_x = (cx + radius_grid * np.cos(angle_grid)).astype(np.float32)
    map_y = (cy + radius_grid * np.sin(angle_grid)).astype(np.float32)
    return cv2.remap(img, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)


def generate_panels(img, event_id):
    """Genera 3 paneles dewarped y los guarda."""
    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2
    radius = int(min(h, w) * 0.48)

    panel_dir = f"{EVENTS_DIR}/fisheye_panels"
    panels = []
    for start, end, label in [(0, 120, "A"), (120, 240, "B"), (240, 360, "C")]:
        panel = dewarp_panel(img, cx, cy, radius, start, end)
        fname = f"{event_id}_panel_{label}.jpg"
        fpath = f"{panel_dir}/{fname}"
        cv2.imwrite(fpath, panel, [cv2.IMWRITE_JPEG_QUALITY, 95])
        panels.append(fpath)

    return panels


def send_whatsapp_alert(event_id, timestamp, snapshot_path, panel_paths):
    """Envía frame trigger + 3 paneles por WhatsApp."""
    try:
        import subprocess
        time_str = timestamp.strftime("%H:%M:%S")
        date_str = timestamp.strftime("%d/%m/%Y")
        msg = (
            f"🎥 *MOVIMIENTO — FISHEYE*\n\n"
            f"📍 Cámara: {CAMERA_NAME}\n"
            f"📅 {date_str} — {time_str}\n"
            f"🆔 `{event_id}`"
        )

        # Copy trigger to workspace
        ws_trigger = f"{WORKSPACE_DIR}/{os.path.basename(snapshot_path)}"
        shutil.copy2(snapshot_path, ws_trigger)

        result = subprocess.run([
            "openclaw", "message", "send",
            "--channel", "whatsapp",
            "-t", "+5218186651436",
            "-m", msg,
            "--media", ws_trigger
        ], timeout=15, capture_output=True, text=True)

        if result.returncode == 0:
            log.info("  📱 Fisheye trigger enviado ✅")
        else:
            log.warning(f"  ⚠️ WhatsApp trigger: {result.stderr[:200]}")

        # Send panels
        for ppath in panel_paths:
            ws_panel = f"{WORKSPACE_DIR}/{os.path.basename(ppath)}"
            shutil.copy2(ppath, ws_panel)
            label = os.path.basename(ppath).split("_panel_")[1].replace(".jpg", "")
            subprocess.run([
                "openclaw", "message", "send",
                "--channel", "whatsapp",
                "-t", "+5218186651436",
                "-m", f"📷 Panel {label}",
                "--media", ws_panel
            ], timeout=15, capture_output=True, text=True)
            try:
                os.remove(ws_panel)
            except:
                pass

        try:
            os.remove(ws_trigger)
        except:
            pass

    except Exception as e:
        log.warning(f"  ⚠️ WhatsApp error: {e}")


def run():
    ensure_dirs()

    log.info("=" * 60)
    log.info("🎥 DNS Vision AI — Detector Fisheye")
    log.info(f"📍 Cámara: {CAMERA_NAME} ({CAMERA_IP})")
    log.info(f"⚙️  Motion threshold: {MOTION_THRESHOLD}")
    log.info(f"📱 WhatsApp alertas: {'✅ Sí' if SEND_WHATSAPP else '❌ No'}")
    log.info(f"⏱️  Cooldown: {COOLDOWN_SECONDS}s | Check: {CHECK_INTERVAL}s")
    log.info("=" * 60)

    opener = setup_camera_auth()

    test_img = grab_snapshot(opener)
    if test_img is None:
        log.error("❌ No se pudo conectar a fisheye")
        return
    log.info(f"✅ Fisheye OK: {test_img.shape[1]}x{test_img.shape[0]}")

    small = cv2.resize(test_img, (RESIZE_WIDTH, int(test_img.shape[0] * RESIZE_WIDTH / test_img.shape[1])))
    prev_gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (21, 21), 0)

    last_event_time = 0
    event_count = 0
    motion_count = 0

    log.info("👀 Monitoreando fisheye...")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)

            img = grab_snapshot(opener)
            if img is None:
                continue

            small = cv2.resize(img, (RESIZE_WIDTH, int(img.shape[0] * RESIZE_WIDTH / img.shape[1])))
            gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (21, 21), 0)
            has_motion, area, num_contours = detect_motion(prev_gray, gray)
            prev_gray = gray

            if not has_motion:
                continue

            now = time.time()
            if now - last_event_time < COOLDOWN_SECONDS:
                continue

            last_event_time = now
            motion_count += 1
            event_count += 1
            timestamp = datetime.now()
            event_id = f"{CAMERA_NAME}_{timestamp.strftime('%Y%m%d_%H%M%S')}_motion_{motion_count:04d}"

            log.info(f"🔍 Movimiento #{motion_count} (área: {area:.0f}, contornos: {num_contours})")

            # Save trigger
            trigger_file = f"{event_id}_trigger.jpg"
            trigger_path = f"{EVENTS_DIR}/snapshots/{trigger_file}"
            cv2.imwrite(trigger_path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])

            # Generate 3 dewarped panels
            panel_paths = generate_panels(img, event_id)

            # Save metadata
            event = {
                "event_id": event_id,
                "camera": CAMERA_NAME,
                "camera_ip": CAMERA_IP,
                "camera_type": "fisheye",
                "timestamp": timestamp.isoformat(),
                "motion_area": area,
                "motion_contours": num_contours,
                "trigger": trigger_file,
                "panels": [os.path.basename(p) for p in panel_paths],
                "type": "movimiento",
            }
            with open(f"{EVENTS_DIR}/metadata/{event_id}.json", "w") as f:
                json.dump(event, f, indent=2, default=str)

            if SEND_WHATSAPP:
                send_whatsapp_alert(event_id, timestamp, trigger_path, panel_paths)

            log.info(f"  ✅ Fisheye guardado: trigger + 3 paneles")
            log.info(f"  📊 Total: {event_count} movimientos")

    except KeyboardInterrupt:
        log.info("\n⛔ Detenido")
    finally:
        log.info(f"📊 Final: {event_count} movimientos | {motion_count} detecciones")


if __name__ == "__main__":
    run()

"""
DNS Vision AI — Heat Map Generator
Acumula movimiento de la cámara y genera mapa de calor.
"""

import cv2
import numpy as np
import os
import time
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

CAMERA_IP = os.environ.get("CAMERA_IP", "192.168.8.26")
CAMERA_USER = os.environ.get("CAMERA_USER", "dns")
CAMERA_PASS = os.environ.get("CAMERA_PASS", "admin12345")
HEATMAP_DIR = os.environ.get("HEATMAP_DIR", "/home/manny/dns-vision-ai/heatmaps")
CHECK_INTERVAL = float(os.environ.get("HEATMAP_INTERVAL", "2.0"))
SAVE_INTERVAL = int(os.environ.get("HEATMAP_SAVE_INTERVAL", "300"))  # save every 5 min

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("heatmap")


def setup_auth():
    pm = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pm.add_password(None, f"http://{CAMERA_IP}", CAMERA_USER, CAMERA_PASS)
    return urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(pm))


def grab_snapshot(opener):
    try:
        resp = opener.open(f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/picture", timeout=5)
        data = resp.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except:
        return None


def generate_heatmap_overlay(accumulator, base_img):
    """Genera imagen con overlay de mapa de calor"""
    # Normalize accumulator
    norm = cv2.normalize(accumulator, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    # Apply color map
    heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    # Resize heatmap to match base image
    heatmap = cv2.resize(heatmap, (base_img.shape[1], base_img.shape[0]))
    # Blend
    overlay = cv2.addWeighted(base_img, 0.5, heatmap, 0.5, 0)

    # Add legend
    h, w = overlay.shape[:2]
    cv2.putText(overlay, "MAPA DE CALOR - DNS Vision AI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(overlay, datetime.now().strftime("%Y-%m-%d %H:%M"), (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Color bar legend
    for i in range(256):
        color = cv2.applyColorMap(np.array([[i]], dtype=np.uint8), cv2.COLORMAP_JET)[0][0]
        cv2.rectangle(overlay, (w - 40, h - 20 - i), (w - 10, h - 19 - i), color.tolist(), -1)
    cv2.putText(overlay, "Alto", (w - 55, h - 270), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(overlay, "Bajo", (w - 55, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return overlay


def run():
    Path(HEATMAP_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{HEATMAP_DIR}/daily").mkdir(parents=True, exist_ok=True)

    log.info("🔥 DNS Vision AI — Heat Map Generator")
    log.info(f"📍 Cámara: {CAMERA_IP}")
    log.info(f"💾 Dir: {HEATMAP_DIR}")

    opener = setup_auth()

    # Get first frame for dimensions
    first = grab_snapshot(opener)
    if first is None:
        log.error("❌ No se pudo conectar")
        return

    # Work at reduced resolution for speed
    scale = 0.25
    small_h = int(first.shape[0] * scale)
    small_w = int(first.shape[1] * scale)
    log.info(f"✅ Resolución heatmap: {small_w}x{small_h}")

    accumulator = np.zeros((small_h, small_w), dtype=np.float64)
    prev_gray = cv2.cvtColor(cv2.resize(first, (small_w, small_h)), cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

    frame_count = 0
    last_save = time.time()
    base_img = first.copy()
    start_time = time.time()

    log.info("👀 Acumulando movimiento...")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)

            img = grab_snapshot(opener)
            if img is None:
                continue

            frame_count += 1
            base_img = img.copy()  # keep latest for overlay

            small = cv2.resize(img, (small_w, small_h))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Motion diff
            diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            prev_gray = gray

            # Accumulate motion (add to heatmap)
            accumulator += thresh.astype(np.float64)

            # Save periodically
            now = time.time()
            if now - last_save >= SAVE_INTERVAL:
                last_save = now

                # Generate overlay
                overlay = generate_heatmap_overlay(accumulator, base_img)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Save latest (always overwritten)
                cv2.imwrite(f"{HEATMAP_DIR}/heatmap_latest.jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 90])

                # Save timestamped copy
                date_dir = f"{HEATMAP_DIR}/daily/{datetime.now().strftime('%Y-%m-%d')}"
                Path(date_dir).mkdir(parents=True, exist_ok=True)
                cv2.imwrite(f"{date_dir}/heatmap_{ts}.jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 85])

                # Save raw accumulator for continuation
                np.save(f"{HEATMAP_DIR}/accumulator.npy", accumulator)

                elapsed = (now - start_time) / 60
                log.info(f"🔥 Heatmap guardado ({frame_count} frames, {elapsed:.0f} min)")

    except KeyboardInterrupt:
        log.info("\n⛔ Guardando último heatmap...")
        overlay = generate_heatmap_overlay(accumulator, base_img)
        cv2.imwrite(f"{HEATMAP_DIR}/heatmap_latest.jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 90])
        np.save(f"{HEATMAP_DIR}/accumulator.npy", accumulator)
        log.info("✅ Guardado")


if __name__ == "__main__":
    run()

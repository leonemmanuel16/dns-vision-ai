"""
DNS Vision AI — Motion Detector + Azure AI (Solo Humanos)
Pipeline: Movimiento Local → Azure verifica humano → 5 frames + evento
Ignora sombras, luces, animales — solo personas reales.
"""

import cv2
import os
import time
import json
import logging
import urllib.request
import urllib.error
import ssl
import numpy as np
from datetime import datetime
from pathlib import Path

# ─── Config ───
CAMERA_IP = os.environ.get("CAMERA_IP", "192.168.8.26")
CAMERA_USER = os.environ.get("CAMERA_USER", "dns")
CAMERA_PASS = os.environ.get("CAMERA_PASS", "admin12345")
CAMERA_NAME = os.environ.get("CAMERA_NAME", "hikvision_principal")
AZURE_KEY = os.environ.get("AZURE_KEY", "")
AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "")
EVENTS_DIR = os.environ.get("EVENTS_DIR", "/home/manny/dns-vision-ai/events")
BANK_DIR = os.environ.get("BANK_DIR", "/home/manny/dns-vision-ai/image_bank")
MOTION_THRESHOLD = int(os.environ.get("MOTION_THRESHOLD", "8000"))  # más alto para ignorar sombras
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "15"))
FRAMES_PER_EVENT = int(os.environ.get("FRAMES_PER_EVENT", "5"))
FRAME_INTERVAL = float(os.environ.get("FRAME_INTERVAL", "1.0"))
CHECK_INTERVAL = float(os.environ.get("CHECK_INTERVAL", "1.5"))
RESIZE_WIDTH = int(os.environ.get("RESIZE_WIDTH", "640"))
MIN_PERSON_CONFIDENCE = float(os.environ.get("MIN_PERSON_CONFIDENCE", "0.55"))
STORE_ALL_MOTION = os.environ.get("STORE_ALL_MOTION", "true").lower() == "true"
RECORD_VIDEO_CLIPS = os.environ.get("RECORD_VIDEO_CLIPS", "false").lower() == "true"
CAPTURE_EXTRA_FRAMES = os.environ.get("CAPTURE_EXTRA_FRAMES", "true").lower() == "true"
SEND_WHATSAPP_ALERTS = os.environ.get("SEND_WHATSAPP_ALERTS", "false").lower() == "true"
USE_AZURE_VALIDATION = os.environ.get("USE_AZURE_VALIDATION", "true").lower() == "true"
SEND_MOTION_FRAME_WHATSAPP = os.environ.get("SEND_MOTION_FRAME_WHATSAPP", "true").lower() == "true"
ALERT_ONLY_IF_AZURE_PERSON = os.environ.get("ALERT_ONLY_IF_AZURE_PERSON", "true").lower() == "true"
PUBLISH_DASHBOARD_EVENTS = os.environ.get("PUBLISH_DASHBOARD_EVENTS", "true").lower() == "true"
INGEST_API_URL = os.environ.get("INGEST_API_URL", "http://127.0.0.1:8000/api/ingest/motion")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("dns_vision")


def ensure_dirs():
    for d in [
        f"{EVENTS_DIR}/snapshots",
        f"{EVENTS_DIR}/metadata",
        f"{EVENTS_DIR}/videos",
        f"{EVENTS_DIR}/azure",
        f"{BANK_DIR}/personas",
        f"{BANK_DIR}/descartados",
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
        resp = opener.open(url, timeout=5)
        data = resp.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img, data
    except Exception as e:
        log.warning(f"⚠️ Snapshot: {e}")
        return None, None


def detect_motion(prev_gray, curr_gray):
    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    # Erosionar para quitar ruido pequeño (sombras, luces parpadeantes)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Solo contar contornos grandes (humano mínimo ~2000px área en 640px wide)
    big_contours = [c for c in contours if cv2.contourArea(c) > 1500]
    total_area = sum(cv2.contourArea(c) for c in big_contours)
    return total_area > MOTION_THRESHOLD, total_area, len(big_contours)


def save_azure_response(event_id, payload):
    """Guarda respuesta cruda de Azure para auditoría/debug."""
    try:
        with open(f"{EVENTS_DIR}/azure/{event_id}.json", "w") as f:
            json.dump(payload, f, indent=2, default=str)
    except Exception as e:
        log.warning(f"⚠️ No se pudo guardar respuesta Azure: {e}")


def azure_check_person(image_bytes):
    """Envía 1 frame a Azure. Retorna True solo si detecta persona real."""
    if not AZURE_KEY:
        return False, None

    try:
        url = f"{AZURE_ENDPOINT}computervision/imageanalysis:analyze?api-version=2024-02-01&features=people,tags,caption"
        req = urllib.request.Request(url, data=image_bytes, method="POST")
        req.add_header("Ocp-Apim-Subscription-Key", AZURE_KEY)
        req.add_header("Content-Type", "application/octet-stream")
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        result = json.loads(resp.read().decode())

        # Check people detection ONLY (stricter, avoids false positives from tags/captions)
        people = result.get("peopleResult", {}).get("values", [])
        confident_people = [p for p in people if p.get("confidence", 0) >= MIN_PERSON_CONFIDENCE]

        # Keep tags only for logging/debug, NOT for decision
        tags = result.get("tagsResult", {}).get("values", [])

        has_person = len(confident_people) > 0
        caption = result.get("captionResult", {}).get("text", "")

        return has_person, {
            "caption": caption,
            "persons": len(confident_people),
            "persons_detail": [{"confidence": p["confidence"], "box": p["boundingBox"]} for p in confident_people],
            "tags": [{"name": t["name"], "confidence": t["confidence"]} for t in tags[:10]],
            "person_in_tags": person_tags,
            "raw": result
        }

    except Exception as e:
        log.error(f"❌ Azure: {e}")
        return False, None


VIDEO_DURATION = int(os.environ.get("VIDEO_DURATION", "10"))  # seconds
VIDEO_FPS = float(os.environ.get("VIDEO_FPS", "2"))  # snapshots per second for video


def capture_5_frames(opener, event_id):
    """Captura 5 frames con intervalo"""
    frames = []
    for i in range(FRAMES_PER_EVENT):
        img, _ = grab_snapshot(opener)
        if img is None:
            continue
        filename = f"{event_id}_frame_{i+1}.jpg"
        filepath = f"{EVENTS_DIR}/snapshots/{filename}"
        cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frames.append(filename)
        if i < FRAMES_PER_EVENT - 1:
            time.sleep(FRAME_INTERVAL)
    return frames


def record_video_clip(opener, event_id, trigger_img=None):
    """Graba un video corto capturando snapshots rápidos y armando MP4"""
    video_dir = f"{EVENTS_DIR}/videos"
    Path(video_dir).mkdir(parents=True, exist_ok=True)

    total_frames = int(VIDEO_DURATION * VIDEO_FPS)
    interval = 1.0 / VIDEO_FPS
    collected = []

    # Include trigger frame as first frame
    if trigger_img is not None:
        collected.append(trigger_img)

    log.info(f"  🎬 Grabando video: {VIDEO_DURATION}s ({total_frames} frames)...")

    for i in range(total_frames):
        img, _ = grab_snapshot(opener)
        if img is not None:
            collected.append(img)
        time.sleep(interval)

    if len(collected) < 3:
        log.warning("  ⚠️ Muy pocos frames para video")
        return None

    # Build MP4 from frames
    h, w = collected[0].shape[:2]
    video_file = f"{event_id}_clip.mp4"
    video_path = f"{video_dir}/{video_file}"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(video_path, fourcc, VIDEO_FPS, (w, h))

    for frame in collected:
        # Resize if needed (all frames same size)
        if frame.shape[:2] != (h, w):
            frame = cv2.resize(frame, (w, h))
        # Add timestamp overlay
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, ts, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, CAMERA_NAME, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        writer.write(frame)

    writer.release()

    size_kb = os.path.getsize(video_path) / 1024
    log.info(f"  🎬 Video guardado: {video_file} ({len(collected)} frames, {size_kb:.0f} KB)")
    return video_file


def save_to_bank(img, event_id, timestamp):
    """Guarda en banco: personas/YYYY-MM-DD/"""
    date_str = timestamp.strftime("%Y-%m-%d")
    bank_path = f"{BANK_DIR}/personas/{date_str}"
    Path(bank_path).mkdir(parents=True, exist_ok=True)
    filepath = f"{bank_path}/{event_id}.jpg"
    cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 85])


def send_whatsapp_alert(event_id, azure_info, timestamp, snapshot_path):
    """Envía alerta a Manny por WhatsApp via OpenClaw CLI"""
    try:
        import subprocess
        time_str = timestamp.strftime("%H:%M:%S")
        date_str = timestamp.strftime("%d/%m/%Y")
        persons = azure_info.get("persons", 0)
        caption = azure_info.get("caption", "")

        msg = (
            f"🚨 *PERSONA DETECTADA*\n\n"
            f"📍 Cámara: {CAMERA_NAME}\n"
            f"📅 {date_str} — {time_str}\n"
            f"👥 Personas: {persons}\n"
            f"📝 _{caption}_\n"
            f"🆔 `{event_id}`"
        )

        # Send photo + caption via openclaw
        result = subprocess.run([
            "openclaw", "message", "send",
            "--channel", "whatsapp",
            "-t", "+5218186651436",
            "-m", msg,
            "--media", snapshot_path
        ], timeout=15, capture_output=True, text=True)

        if result.returncode == 0:
            log.info(f"  📱 WhatsApp enviado a Manny ✅")
        else:
            log.warning(f"  ⚠️ WhatsApp returncode {result.returncode}: {result.stderr[:200]}")

    except Exception as e:
        log.warning(f"  ⚠️ WhatsApp error: {e}")


WORKSPACE_DIR = "/home/manny/.openclaw/workspace"

def send_whatsapp_motion_frame(event_id, timestamp, snapshot_path):
    """Envía frame de movimiento por WhatsApp (sin validación Azure)."""
    try:
        import subprocess, shutil
        time_str = timestamp.strftime("%H:%M:%S")
        date_str = timestamp.strftime("%d/%m/%Y")
        msg = (
            f"🎥 *MOVIMIENTO DETECTADO*\n\n"
            f"📍 Cámara: {CAMERA_NAME}\n"
            f"📅 {date_str} — {time_str}\n"
            f"🆔 `{event_id}`"
        )
        # Copy to workspace (allowed dir for WhatsApp)
        ws_path = f"{WORKSPACE_DIR}/{os.path.basename(snapshot_path)}"
        shutil.copy2(snapshot_path, ws_path)
        
        result = subprocess.run([
            "openclaw", "message", "send",
            "--channel", "whatsapp",
            "-t", "+5218186651436",
            "-m", msg,
            "--media", ws_path
        ], timeout=15, capture_output=True, text=True)
        if result.returncode == 0:
            log.info("  📱 Frame de movimiento enviado por WhatsApp ✅")
        else:
            log.warning(f"  ⚠️ WhatsApp returncode {result.returncode}: {result.stderr[:200]}")
        # Cleanup workspace copy
        try:
            os.remove(ws_path)
        except:
            pass
    except Exception as e:
        log.warning(f"  ⚠️ WhatsApp error: {e}")


def publish_dashboard_event(event_id, timestamp, snapshot_path, motion_area, contours):
    """Publica evento al API para que aparezca en dashboard."""
    if not PUBLISH_DASHBOARD_EVENTS:
        return
    try:
        payload = {
            "event_id": event_id,
            "camera_name": CAMERA_NAME,
            "camera_ip": CAMERA_IP,
            "event_type": "motion",
            "label": "Movimiento",
            "occurred_at": timestamp.isoformat(),
            "snapshot_path": snapshot_path,
            "metadata": {
                "motion_area": motion_area,
                "contours": contours,
                "source": "motion_detector_azure.py"
            }
        }
        req = urllib.request.Request(
            INGEST_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        if INGEST_TOKEN:
            req.add_header("X-Ingest-Token", INGEST_TOKEN)

        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                log.warning(f"  ⚠️ Ingest status: {resp.status}")
            else:
                log.info("  📊 Evento publicado en dashboard")
    except urllib.error.HTTPError as e:
        log.warning(f"  ⚠️ Ingest HTTP {e.code}: {e.reason}")
    except Exception as e:
        log.warning(f"  ⚠️ Ingest error: {e}")


def run():
    ensure_dirs()

    log.info("=" * 60)
    log.info("🎥 DNS Vision AI — Detector de Movimiento")
    log.info(f"📍 Cámara: {CAMERA_NAME} ({CAMERA_IP})")
    log.info(f"☁️  Azure validación: {'✅ Sí' if USE_AZURE_VALIDATION else '❌ No'}")
    log.info(f"⚙️  Motion threshold: {MOTION_THRESHOLD}")
    log.info(f"💾 Guardar todo movimiento: {'✅ Sí' if STORE_ALL_MOTION else '❌ No'}")
    log.info(f"🎬 Guardar clips 10s: {'✅ Sí' if RECORD_VIDEO_CLIPS else '❌ No'}")
    log.info(f"📸 Frames extra: {'✅ Sí' if CAPTURE_EXTRA_FRAMES else '❌ No'}")
    log.info(f"📱 Enviar frame por WhatsApp: {'✅ Sí' if SEND_MOTION_FRAME_WHATSAPP else '❌ No'}")
    log.info(f"👤 Alerta solo si Azure=persona: {'✅ Sí' if ALERT_ONLY_IF_AZURE_PERSON else '❌ No'}")
    log.info(f"📊 Publicar en dashboard: {'✅ Sí' if PUBLISH_DASHBOARD_EVENTS else '❌ No'}")
    log.info(f"⏱️  Cooldown: {COOLDOWN_SECONDS}s | Check: {CHECK_INTERVAL}s")
    log.info("=" * 60)

    opener = setup_camera_auth()

    # Test camera
    test_img, test_data = grab_snapshot(opener)
    if test_img is None:
        log.error("❌ No se pudo conectar")
        return
    log.info(f"✅ Cámara OK: {test_img.shape[1]}x{test_img.shape[0]}")

    # Test Azure (opcional)
    if USE_AZURE_VALIDATION and AZURE_KEY:
        has_person, info = azure_check_person(test_data)
        if info:
            log.info(f"☁️ Azure OK: \"{info['caption']}\" | Persona: {'SÍ' if has_person else 'NO'}")
        else:
            log.warning("⚠️ Azure no respondió en test")

    # Init motion
    small = cv2.resize(test_img, (RESIZE_WIDTH, int(test_img.shape[0] * RESIZE_WIDTH / test_img.shape[1])))
    prev_gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (21, 21), 0)

    last_event_time = 0
    event_count = 0
    motion_count = 0
    azure_calls = 0
    false_alarms = 0
    check_count = 0
    start_time = time.time()

    log.info("👀 Monitoreando (solo personas)...")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            check_count += 1

            img, img_data = grab_snapshot(opener)
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

            motion_count += 1
            log.info(f"🔍 Movimiento #{motion_count} (área: {area:.0f}, contornos: {num_contours})")

            last_event_time = now
            event_count += 1
            timestamp = datetime.now()
            event_id = f"{CAMERA_NAME}_{timestamp.strftime('%Y%m%d_%H%M%S')}_motion_{motion_count:04d}"
            trigger_file = f"{event_id}_trigger.jpg"
            trigger_path = f"{EVENTS_DIR}/snapshots/{trigger_file}"
            cv2.imwrite(trigger_path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])

            azure_info = None
            has_person = None
            if USE_AZURE_VALIDATION and AZURE_KEY:
                azure_event_id = f"{CAMERA_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_azure"
                has_person, azure_info = azure_check_person(img_data)
                azure_calls += 1
                save_azure_response(azure_event_id, {
                    "camera": CAMERA_NAME,
                    "timestamp": datetime.now().isoformat(),
                    "has_person": has_person,
                    "azure_info": azure_info,
                })

            frames = [trigger_file]
            video_file = None
            if RECORD_VIDEO_CLIPS:
                video_file = record_video_clip(opener, event_id, trigger_img=img)
            if CAPTURE_EXTRA_FRAMES:
                frames += capture_5_frames(opener, event_id)

            event = {
                "event_id": event_id,
                "camera": CAMERA_NAME,
                "camera_ip": CAMERA_IP,
                "timestamp": timestamp.isoformat(),
                "motion_area": area,
                "motion_contours": num_contours,
                "frames": frames,
                "frames_count": len(frames),
                "video_clip": video_file,
                "video_duration_seconds": VIDEO_DURATION if video_file else 0,
                "azure_validation_enabled": USE_AZURE_VALIDATION,
                "azure_has_person": has_person,
                "azure_caption": (azure_info or {}).get("caption") if isinstance(azure_info, dict) else None,
                "type": "movimiento",
            }
            with open(f"{EVENTS_DIR}/metadata/{event_id}.json", "w") as f:
                json.dump(event, f, indent=2, default=str)

            publish_dashboard_event(event_id, timestamp, trigger_path, area, num_contours)

            should_send_whatsapp = SEND_MOTION_FRAME_WHATSAPP
            if ALERT_ONLY_IF_AZURE_PERSON:
                should_send_whatsapp = (
                    SEND_MOTION_FRAME_WHATSAPP and
                    USE_AZURE_VALIDATION and
                    has_person is True
                )

            if should_send_whatsapp:
                send_whatsapp_motion_frame(event_id, timestamp, trigger_path)

            log.info(f"  ✅ Movimiento guardado: {trigger_file}")
            log.info(f"  📊 Total: {event_count} movimientos | {azure_calls} Azure calls")

            # Stats cada 5 min
            if check_count % 200 == 0:
                elapsed = (time.time() - start_time) / 60
                hit_rate = (event_count / azure_calls * 100) if azure_calls > 0 else 0
                log.info(f"📊 {elapsed:.0f}min | checks:{check_count} | motion:{motion_count} | personas:{event_count} | descartados:{false_alarms} | hit:{hit_rate:.0f}% | azure:{azure_calls}")

    except KeyboardInterrupt:
        log.info("\n⛔ Detenido")
    finally:
        elapsed = (time.time() - start_time) / 60
        log.info(f"📊 Final: {event_count} personas | {false_alarms} falsas alarmas | {azure_calls} Azure calls | {elapsed:.1f} min")


if __name__ == "__main__":
    run()

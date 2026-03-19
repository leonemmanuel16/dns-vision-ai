"""
Alert consumer that listens to Redis Streams for detection events
and triggers alert rules (webhook, WhatsApp, email).
Runs as a background task inside the API service.
"""

import os
import json
import asyncio
import structlog
import redis.asyncio as aioredis
from sqlalchemy import select
from datetime import datetime, timezone

from config import get_settings
from database import async_session
from models.alert_rule import AlertRule
from services.alert_service import send_webhook, send_whatsapp

logger = structlog.get_logger()
settings = get_settings()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "")


async def start_alert_consumer():
    """Listen to detection_events Redis Stream and process alerts."""
    logger.info("alert_consumer_starting")
    r = aioredis.from_url(settings.redis_url)
    last_id = "$"

    while True:
        try:
            streams = await r.xread({"detection_events": last_id}, count=10, block=2000)

            for stream_name, messages in streams:
                for msg_id, raw_data in messages:
                    last_id = msg_id
                    data = {
                        k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                        for k, v in raw_data.items()
                    }

                    await _process_event(data)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("alert_consumer_error", error=str(e))
            await asyncio.sleep(2)

    await r.aclose()
    logger.info("alert_consumer_stopped")


async def _process_event(event: dict):
    """Check all alert rules against a detection event."""
    now = datetime.now(timezone.utc)

    async with async_session() as db:
        result = await db.execute(
            select(AlertRule).where(AlertRule.is_enabled == True)
        )
        rules = list(result.scalars().all())

        for rule in rules:
            # Filter by camera
            if rule.camera_id and str(rule.camera_id) != event.get("camera_id", ""):
                continue

            # Filter by zone
            if rule.zone_id and str(rule.zone_id) != event.get("zone_id", ""):
                continue

            # Filter by event type
            if event.get("event_type") not in rule.event_types:
                continue

            # Check cooldown
            if rule.last_triggered_at:
                elapsed = (now - rule.last_triggered_at).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue

            # Check schedule
            if rule.schedule:
                start = rule.schedule.get("start")
                end = rule.schedule.get("end")
                days = rule.schedule.get("days", [])
                if days and now.isoweekday() not in days:
                    continue
                if start and end:
                    current_time = now.strftime("%H:%M")
                    if not (start <= current_time <= end):
                        continue

            # Build payload
            payload = {
                "alert_rule": rule.name,
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "label": event.get("label"),
                "confidence": event.get("confidence"),
                "camera_id": event.get("camera_id"),
                "zone_id": event.get("zone_id"),
                "snapshot_path": event.get("snapshot_path"),
                "occurred_at": event.get("occurred_at"),
                "triggered_at": now.isoformat(),
            }

            # Send notification
            try:
                if rule.channel == "webhook":
                    await send_webhook(rule.target, payload)
                elif rule.channel == "whatsapp" and WHATSAPP_WEBHOOK_URL:
                    msg = f"Alert: {rule.name} - {event.get('label', event.get('event_type'))} detected"
                    await send_whatsapp(WHATSAPP_WEBHOOK_URL, rule.target, msg, event.get("snapshot_path"))
                elif rule.channel == "email":
                    # Email support can be added here
                    logger.info("email_alert_skipped", rule=rule.name, target=rule.target)

                # Update last triggered
                rule.last_triggered_at = now
                await db.commit()

                logger.info(
                    "alert_sent",
                    rule=rule.name,
                    channel=rule.channel,
                    event_type=event.get("event_type"),
                )
            except Exception as e:
                logger.error("alert_send_failed", rule=rule.name, error=str(e))

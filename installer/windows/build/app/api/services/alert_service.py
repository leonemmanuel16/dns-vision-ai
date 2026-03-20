import uuid
import structlog
import httpx
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.alert_rule import AlertRule

logger = structlog.get_logger()


async def list_alert_rules(db: AsyncSession) -> tuple[list[AlertRule], int]:
    result = await db.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    rules = list(result.scalars().all())
    count_result = await db.execute(select(func.count(AlertRule.id)))
    total = count_result.scalar()
    return rules, total


async def get_alert_rule(db: AsyncSession, rule_id: uuid.UUID) -> AlertRule | None:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    return result.scalar_one_or_none()


async def create_alert_rule(db: AsyncSession, data: dict) -> AlertRule:
    rule = AlertRule(**data)
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    logger.info("alert_rule_created", name=rule.name, channel=rule.channel)
    return rule


async def update_alert_rule(db: AsyncSession, rule_id: uuid.UUID, data: dict) -> AlertRule | None:
    rule = await get_alert_rule(db, rule_id)
    if rule is None:
        return None
    for field, value in data.items():
        if value is not None:
            setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return rule


async def delete_alert_rule(db: AsyncSession, rule_id: uuid.UUID) -> bool:
    rule = await get_alert_rule(db, rule_id)
    if rule is None:
        return False
    await db.delete(rule)
    await db.flush()
    return True


async def send_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            logger.info("webhook_sent", url=url, status=resp.status_code)
    except Exception as e:
        logger.error("webhook_failed", url=url, error=str(e))


async def send_whatsapp(webhook_url: str, phone: str, message: str, image_url: str | None = None):
    payload = {"phone": phone, "message": message}
    if image_url:
        payload["image_url"] = image_url
    await send_webhook(webhook_url, payload)


async def process_event_alerts(db: AsyncSession, event: dict, webhook_url: str | None = None, whatsapp_url: str | None = None):
    """Check all alert rules against an event and send notifications."""
    result = await db.execute(
        select(AlertRule).where(AlertRule.is_enabled == True)
    )
    rules = list(result.scalars().all())

    now = datetime.now(timezone.utc)

    for rule in rules:
        if rule.camera_id and str(rule.camera_id) != str(event.get("camera_id")):
            continue
        if rule.zone_id and str(rule.zone_id) != str(event.get("zone_id", "")):
            continue
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

        # Send alert
        alert_payload = {
            "rule_name": rule.name,
            "event_type": event.get("event_type"),
            "label": event.get("label"),
            "confidence": event.get("confidence"),
            "camera_id": str(event.get("camera_id")),
            "occurred_at": str(event.get("occurred_at")),
            "snapshot_url": event.get("snapshot_url"),
        }

        if rule.channel == "webhook" and rule.target:
            await send_webhook(rule.target, alert_payload)
        elif rule.channel == "whatsapp" and whatsapp_url:
            msg = f"🚨 {rule.name}: {event.get('label', event.get('event_type'))} detected"
            await send_whatsapp(whatsapp_url, rule.target, msg, event.get("snapshot_url"))

        # Update last triggered
        rule.last_triggered_at = now
        await db.flush()
        logger.info("alert_triggered", rule=rule.name, channel=rule.channel)

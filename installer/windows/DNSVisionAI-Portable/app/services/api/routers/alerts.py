import uuid
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user, require_operator
from models.user import User
from services.alert_service import list_alert_rules, get_alert_rule, create_alert_rule, update_alert_rule, delete_alert_rule

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertRuleCreate(BaseModel):
    name: str
    camera_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    event_types: list[str]
    channel: str  # whatsapp, webhook, email
    target: str
    cooldown_seconds: int = 60
    schedule: dict | None = None
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    camera_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    event_types: list[str] | None = None
    channel: str | None = None
    target: str | None = None
    cooldown_seconds: int | None = None
    schedule: dict | None = None
    is_enabled: bool | None = None


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    camera_id: uuid.UUID | None
    zone_id: uuid.UUID | None
    event_types: list[str]
    channel: str
    target: str
    cooldown_seconds: int
    schedule: dict | None
    is_enabled: bool
    last_triggered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleListResponse(BaseModel):
    rules: list[AlertRuleResponse]
    total: int


@router.get("", response_model=AlertRuleListResponse)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rules, total = await list_alert_rules(db)
    return AlertRuleListResponse(
        rules=[AlertRuleResponse.model_validate(r) for r in rules],
        total=total,
    )


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rule = await get_alert_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return AlertRuleResponse.model_validate(rule)


@router.post("", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    rule = await create_alert_rule(db, data.model_dump())
    return AlertRuleResponse.model_validate(rule)


@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert(
    rule_id: uuid.UUID,
    data: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    rule = await update_alert_rule(db, rule_id, data.model_dump(exclude_unset=True))
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return AlertRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    deleted = await delete_alert_rule(db, rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")

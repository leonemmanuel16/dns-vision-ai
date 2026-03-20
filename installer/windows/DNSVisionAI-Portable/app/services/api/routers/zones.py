import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user, require_operator
from models.user import User
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse, ZoneListResponse

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=ZoneListResponse)
async def get_zones(
    camera_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Zone)
    if camera_id:
        query = query.where(Zone.camera_id == camera_id)
    query = query.order_by(Zone.created_at.desc())

    result = await db.execute(query)
    zones = list(result.scalars().all())

    count_query = select(func.count(Zone.id))
    if camera_id:
        count_query = count_query.where(Zone.camera_id == camera_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return ZoneListResponse(
        zones=[ZoneResponse.model_validate(z) for z in zones],
        total=total,
    )


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return ZoneResponse.model_validate(zone)


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    data: ZoneCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    zone = Zone(**data.model_dump())
    db.add(zone)
    await db.flush()
    await db.refresh(zone)
    return ZoneResponse.model_validate(zone)


@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: uuid.UUID,
    data: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)

    await db.flush()
    await db.refresh(zone)
    return ZoneResponse.model_validate(zone)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    await db.delete(zone)
    await db.flush()

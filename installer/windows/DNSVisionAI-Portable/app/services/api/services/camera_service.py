import uuid
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.camera import Camera
from schemas.camera import CameraCreate, CameraUpdate

logger = structlog.get_logger()


async def list_cameras(db: AsyncSession) -> tuple[list[Camera], int]:
    result = await db.execute(select(Camera).order_by(Camera.name))
    cameras = list(result.scalars().all())
    count_result = await db.execute(select(func.count(Camera.id)))
    total = count_result.scalar()
    return cameras, total


async def get_camera(db: AsyncSession, camera_id: uuid.UUID) -> Camera | None:
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    return result.scalar_one_or_none()


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    camera = Camera(
        name=data.name,
        ip_address=data.ip_address,
        onvif_port=data.onvif_port,
        username=data.username,
        password_encrypted=data.password,
        location=data.location,
        is_enabled=data.is_enabled,
    )
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    logger.info("camera_created", name=data.name, ip=data.ip_address)
    return camera


async def update_camera(db: AsyncSession, camera_id: uuid.UUID, data: CameraUpdate) -> Camera | None:
    camera = await get_camera(db, camera_id)
    if camera is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_encrypted"] = update_data.pop("password")

    for field, value in update_data.items():
        setattr(camera, field, value)

    await db.flush()
    await db.refresh(camera)
    logger.info("camera_updated", camera_id=str(camera_id))
    return camera


async def delete_camera(db: AsyncSession, camera_id: uuid.UUID) -> bool:
    camera = await get_camera(db, camera_id)
    if camera is None:
        return False
    await db.delete(camera)
    await db.flush()
    logger.info("camera_deleted", camera_id=str(camera_id))
    return True

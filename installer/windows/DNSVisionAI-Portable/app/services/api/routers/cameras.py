import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user, require_operator
from models.user import User
from schemas.camera import CameraCreate, CameraUpdate, CameraResponse, CameraListResponse, PTZCommand
from services.camera_service import list_cameras, get_camera, create_camera, update_camera, delete_camera

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("", response_model=CameraListResponse)
async def get_cameras(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cameras, total = await list_cameras(db)
    return CameraListResponse(
        cameras=[CameraResponse.model_validate(c) for c in cameras],
        total=total,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera_by_id(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera = await get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return CameraResponse.model_validate(camera)


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def add_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    camera = await create_camera(db, data)
    return CameraResponse.model_validate(camera)


@router.put("/{camera_id}", response_model=CameraResponse)
async def modify_camera(
    camera_id: uuid.UUID,
    data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    camera = await update_camera(db, camera_id, data)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return CameraResponse.model_validate(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    deleted = await delete_camera(db, camera_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")


@router.post("/{camera_id}/ptz")
async def ptz_control(
    camera_id: uuid.UUID,
    command: PTZCommand,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_operator),
):
    camera = await get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    if not camera.has_ptz:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera does not support PTZ")

    # PTZ commands are forwarded to camera-manager via Redis
    import redis.asyncio as aioredis
    from config import get_settings
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url)
    await r.xadd("ptz_commands", {
        "camera_id": str(camera_id),
        "action": command.action,
        "pan": str(command.pan),
        "tilt": str(command.tilt),
        "zoom": str(command.zoom),
    })
    await r.aclose()
    return {"status": "ok", "message": f"PTZ {command.action} command sent"}

import io
import structlog
from minio import Minio
from minio.error import S3Error

from config import get_settings

logger = structlog.get_logger()
settings = get_settings()

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _ensure_bucket()
    return _client


def _ensure_bucket():
    client = _client
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)
        logger.info("minio_bucket_created", bucket=settings.minio_bucket)


def upload_file(object_name: str, data: bytes, content_type: str = "image/jpeg") -> str:
    client = get_minio_client()
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_name


def get_presigned_url(object_name: str, expires: int = 3600) -> str:
    from datetime import timedelta
    client = get_minio_client()
    try:
        return client.presigned_get_object(
            settings.minio_bucket,
            object_name,
            expires=timedelta(seconds=expires),
        )
    except S3Error:
        logger.warning("minio_presign_failed", object_name=object_name)
        return ""


def delete_file(object_name: str):
    client = get_minio_client()
    try:
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error:
        logger.warning("minio_delete_failed", object_name=object_name)

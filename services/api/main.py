import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import get_settings
from middleware.cors import setup_cors
from routers import auth, cameras, events, zones, alerts, dashboard, ws

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_starting", app=settings.app_name)
    # Ensure MinIO bucket exists on startup
    try:
        from utils.minio_client import get_minio_client
        get_minio_client()
        logger.info("minio_connected")
    except Exception as e:
        logger.warning("minio_connection_failed", error=str(e))
    yield
    logger.info("api_shutting_down")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered video analytics platform with ONVIF support",
    version="1.0.0",
    lifespan=lifespan,
)

setup_cors(app)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(cameras.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(zones.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ws.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "dns-vision-ai-api"}

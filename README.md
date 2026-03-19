# DNS Vision AI

**AI-powered video analytics platform that turns any ONVIF-compatible IP camera into an intelligent security system.**

Built by [Data Network Solutions](https://dnsit.com.mx) — IT infrastructure company in Monterrey, Mexico.

---

## Features

- **ONVIF Camera Auto-Discovery** — Automatically find and configure IP cameras on your network
- **Real-time AI Detection** — People, vehicles, and animals detected using YOLOv10
- **Live Video Dashboard** — Multi-camera grid view with WebRTC ultra-low latency
- **Event Recording** — Automatic clips and snapshots on detection events
- **Virtual Zones** — Draw ROI, tripwire, and perimeter zones per camera
- **Smart Alerts** — WhatsApp and webhook notifications with attached snapshots
- **PTZ Control** — Pan, tilt, and zoom control for supported cameras
- **RESTful API** — Full API with JWT authentication

## Quick Start

```bash
# Clone the repository
git clone https://github.com/leonemmanuel16/dns-vision-ai.git
cd dns-vision-ai

# Configure environment
cp .env.example .env
# Edit .env with your passwords and settings

# Start all services
docker compose up -d

# Access the dashboard
# From the server: http://localhost:3000
# From the network: http://SERVER_IP:3000

# Default login: admin / admin123
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Dashboard   │────▶│   FastAPI    │────▶│ PostgreSQL  │
│  (Next.js)   │     │   Backend    │     │  + pgvector │
└──────┬──────┘     └──────┬───────┘     └─────────────┘
       │                   │
       │              ┌────┴────┐         ┌─────────────┐
       │              │  Redis  │◀────────│  Detector   │
       │              │ Streams │         │  (YOLOv10)  │
       │              └─────────┘         └──────┬──────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   go2rtc    │◀────│   Camera     │     │    MinIO     │
│  (WebRTC)   │     │   Manager    │     │  (S3 Store) │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Frontend | Next.js 14, React, TailwindCSS, shadcn/ui |
| AI Detection | Ultralytics YOLOv10 (yolov10n) |
| Streaming | go2rtc (WebRTC + RTSP) |
| ONVIF | python-onvif-zeep |
| Database | PostgreSQL 16 + pgvector |
| Cache/Events | Redis 7 (Streams) |
| Storage | MinIO (S3-compatible) |
| Auth | JWT + bcrypt |
| Deployment | Docker Compose |
| OS | Ubuntu Server 24.04 LTS |

## API Documentation

API docs available at `http://SERVER_IP:8000/docs` (Swagger UI) when the system is running.

## System Requirements

- Ubuntu Server 24.04 LTS
- NVIDIA GPU (for AI detection) with CUDA drivers
- 16GB+ RAM recommended
- Docker & Docker Compose
- Network access to ONVIF cameras

## License

Proprietary — (c) 2026 Data Network Solutions. All rights reserved.

## Contact

info@dnsit.com.mx

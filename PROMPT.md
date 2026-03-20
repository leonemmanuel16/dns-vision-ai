# DNS Vision AI — Claude Code Build Prompt

## Prompt para Fase 1 (MVP)

---

### STEP ZERO — Create GitHub Repository

Before writing any code, create a **private** GitHub repository and work inside it. All code must be committed and pushed there.

```bash
# Create project directory
mkdir -p ~/dns-vision-ai
cd ~/dns-vision-ai

# Initialize git
git init
git branch -M main

# Create private repo on GitHub using the API
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dns-vision-ai",
    "description": "DNS Vision AI - AI-powered video analytics platform with ONVIF support",
    "private": true,
    "auto_init": false
  }'

# Connect and push
git remote add origin https://YOUR_GITHUB_TOKEN@github.com/leonemmanuel16/dns-vision-ai.git

# After each major component is built, commit and push:
git add -A
git commit -m "feat: description of what was built"
git push -u origin main
```

**GitHub Rules:**
- Repository: `leonemmanuel16/dns-vision-ai` (PRIVATE)
- Commit after each major component is completed (not one giant commit)
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Include a proper `.gitignore` for Python, Node.js, Docker, and env files
- NEVER commit `.env`, passwords, or tokens — only `.env.example`

---

You are building **DNS Vision AI**, an AI-powered video analytics platform that turns any ONVIF-compatible IP camera into an intelligent security system. This is a commercial product for **Data Network Solutions (DNS)**, an IT infrastructure company in Monterrey, Mexico.

### Project Overview

Build a self-hosted, Docker-based video analytics platform with these core capabilities:
1. **ONVIF camera auto-discovery and management**
2. **Real-time AI object detection** (people, vehicles, animals)
3. **Live video dashboard** with multi-camera grid view
4. **Event-based recording** with clips and snapshots
5. **WhatsApp/Webhook alerts** with attached snapshots
6. **RESTful API** with JWT authentication

### Tech Stack (mandatory)

| Layer | Technology |
|---|---|
| Language | Python 3.12+ (backend), TypeScript (frontend) |
| ONVIF | python-onvif-zeep |
| Streaming | go2rtc (pre-built Docker image: alexxit/go2rtc) |
| AI Detection | Ultralytics YOLOv10 (yolov10n for speed) |
| Backend API | FastAPI + uvicorn |
| Frontend | Next.js 14+ (App Router) + React + TailwindCSS + shadcn/ui |
| Database | PostgreSQL 16 with pgvector extension |
| Cache/Events | Redis 7 (Streams for event bus) |
| Object Storage | MinIO (S3-compatible, for clips/snapshots) |
| Video Player | go2rtc WebRTC + HLS.js fallback |
| Auth | JWT (access + refresh tokens) + bcrypt passwords |
| Deployment | Docker Compose |
| OS Target | Ubuntu Server 24.04 LTS |

### Project Structure

```
dns-vision-ai/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── README.md
│
├── services/
│   ├── camera-manager/          # ONVIF discovery & camera lifecycle
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py              # Entry point
│   │   ├── onvif_discovery.py   # WS-Discovery multicast
│   │   ├── onvif_client.py      # Camera ONVIF client (profiles, PTZ, snapshots)
│   │   ├── camera_registry.py   # Track discovered cameras in Redis
│   │   ├── health_monitor.py    # Periodic camera health checks
│   │   └── go2rtc_config.py     # Auto-generate go2rtc.yaml from discovered cameras
│   │
│   ├── detector/                # AI object detection
│   │   ├── Dockerfile           # NVIDIA CUDA base image
│   │   ├── requirements.txt
│   │   ├── main.py              # Entry point - pulls frames, runs detection
│   │   ├── detector.py          # YOLO inference wrapper
│   │   ├── frame_grabber.py     # Pull frames from go2rtc RTSP streams
│   │   ├── zone_manager.py      # Virtual zones/perimeters (line crossing, ROI)
│   │   ├── tracker.py           # Object tracking (ByteTrack / BotSORT)
│   │   ├── event_publisher.py   # Publish detection events to Redis Streams
│   │   └── models/
│   │       └── yolov10n.pt      # Pre-trained model (auto-download)
│   │
│   ├── api/                     # REST API backend
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings from env vars
│   │   ├── database.py          # SQLAlchemy + async postgres
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── camera.py
│   │   │   ├── event.py
│   │   │   ├── zone.py
│   │   │   └── alert_rule.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── camera.py
│   │   │   ├── event.py
│   │   │   └── zone.py
│   │   ├── routers/             # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Login, register, refresh token
│   │   │   ├── cameras.py       # CRUD cameras, discovery trigger, PTZ
│   │   │   ├── events.py        # List/search events, get clips
│   │   │   ├── zones.py         # CRUD virtual zones/perimeters
│   │   │   ├── alerts.py        # Alert rules (WhatsApp, webhook, email)
│   │   │   ├── dashboard.py     # Stats, counts, recent activity
│   │   │   └── ws.py            # WebSocket endpoint for live events
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── camera_service.py
│   │   │   ├── event_service.py
│   │   │   └── alert_service.py # Send alerts (WhatsApp via webhook, email)
│   │   ├── middleware/
│   │   │   ├── auth.py          # JWT verification middleware
│   │   │   └── cors.py
│   │   └── utils/
│   │       ├── security.py      # JWT encode/decode, password hash
│   │       └── minio_client.py  # MinIO upload/download helpers
│   │
│   └── dashboard/               # Frontend
│       ├── Dockerfile
│       ├── package.json
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx              # Redirect to /dashboard
│       │   │   ├── login/page.tsx
│       │   │   ├── dashboard/
│       │   │   │   ├── page.tsx          # Main dashboard (stats + recent events)
│       │   │   │   ├── layout.tsx        # Sidebar + header layout
│       │   │   │   ├── cameras/
│       │   │   │   │   ├── page.tsx      # Camera grid (live view)
│       │   │   │   │   └── [id]/page.tsx # Single camera view + PTZ
│       │   │   │   ├── events/
│       │   │   │   │   ├── page.tsx      # Event timeline with filters
│       │   │   │   │   └── [id]/page.tsx # Single event detail + clip
│       │   │   │   ├── zones/
│       │   │   │   │   └── page.tsx      # Zone/perimeter config
│       │   │   │   ├── alerts/
│       │   │   │   │   └── page.tsx      # Alert rules config
│       │   │   │   └── settings/
│       │   │   │       └── page.tsx      # System settings, users
│       │   │   └── api/                  # Next.js API routes (proxy to backend)
│       │   ├── components/
│       │   │   ├── ui/                   # shadcn/ui components
│       │   │   ├── VideoPlayer.tsx       # WebRTC player (go2rtc)
│       │   │   ├── CameraGrid.tsx        # Multi-camera grid (2x2, 3x3, 4x4)
│       │   │   ├── EventCard.tsx         # Event thumbnail + details
│       │   │   ├── EventTimeline.tsx     # Scrollable event timeline
│       │   │   ├── ZoneEditor.tsx        # Draw zones on camera view (canvas)
│       │   │   ├── PTZControls.tsx       # Pan/Tilt/Zoom buttons
│       │   │   ├── StatsCard.tsx         # Dashboard stat cards
│       │   │   ├── Sidebar.tsx           # Navigation sidebar
│       │   │   └── Header.tsx            # Top header with user menu
│       │   ├── lib/
│       │   │   ├── api.ts               # API client (fetch wrapper)
│       │   │   ├── auth.ts              # Auth context + JWT storage
│       │   │   └── websocket.ts         # WebSocket client for live events
│       │   └── hooks/
│       │       ├── useAuth.ts
│       │       ├── useCameras.ts
│       │       └── useEvents.ts
│       └── public/
│           └── logo.svg
│
├── config/
│   ├── go2rtc.yaml              # Auto-generated by camera-manager
│   └── nginx.conf               # Optional reverse proxy
│
├── scripts/
│   ├── init-db.sql              # Database schema + initial admin user
│   ├── setup.sh                 # First-time setup script
│   └── backup.sh                # Backup database + config
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md                   # API documentation
    ├── DEPLOYMENT.md            # Deployment guide
    └── SECURITY.md              # Security hardening guide
```

### Database Schema

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer', -- admin, operator, viewer
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cameras
CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    onvif_port INTEGER DEFAULT 80,
    username VARCHAR(100),
    password_encrypted VARCHAR(500),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    firmware VARCHAR(100),
    serial_number VARCHAR(100),
    mac_address VARCHAR(17),
    rtsp_main_stream TEXT,        -- high res for recording
    rtsp_sub_stream TEXT,         -- low res for detection
    onvif_profile_token VARCHAR(100),
    has_ptz BOOLEAN DEFAULT false,
    location VARCHAR(200),        -- friendly name: "Entrada Principal"
    is_enabled BOOLEAN DEFAULT true,
    is_online BOOLEAN DEFAULT true,
    last_seen_at TIMESTAMPTZ,
    config JSONB DEFAULT '{}',    -- extra config (fps, resolution, etc)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detection Events
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- person, vehicle, animal, license_plate, zone_crossing
    label VARCHAR(100),               -- "person", "car", "truck", plate number
    confidence FLOAT,
    bbox JSONB,                       -- {x1, y1, x2, y2}
    zone_id UUID REFERENCES zones(id),
    snapshot_path TEXT,               -- MinIO path to snapshot
    clip_path TEXT,                   -- MinIO path to video clip
    thumbnail_path TEXT,              -- MinIO path to thumbnail
    metadata JSONB DEFAULT '{}',      -- extra data (tracker_id, direction, etc)
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_camera_time ON events(camera_id, occurred_at DESC);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_occurred ON events(occurred_at DESC);

-- Virtual Zones
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    zone_type VARCHAR(30) NOT NULL,  -- roi, tripwire, perimeter
    points JSONB NOT NULL,           -- [{x, y}, ...] polygon points (normalized 0-1)
    direction VARCHAR(20),           -- in, out, both (for tripwire)
    detect_classes TEXT[] DEFAULT '{person,vehicle}',
    is_enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert Rules
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    camera_id UUID REFERENCES cameras(id),  -- NULL = all cameras
    zone_id UUID REFERENCES zones(id),      -- NULL = any zone
    event_types TEXT[] NOT NULL,             -- {person, vehicle, zone_crossing}
    channel VARCHAR(30) NOT NULL,            -- whatsapp, webhook, email
    target VARCHAR(500) NOT NULL,            -- phone number, URL, or email
    cooldown_seconds INTEGER DEFAULT 60,     -- don't re-alert within this window
    schedule JSONB,                          -- {start: "08:00", end: "18:00", days: [1,2,3,4,5]}
    is_enabled BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initial admin user (password: admin123 — CHANGE ON FIRST LOGIN)
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@dnsit.com.mx', '$2b$12$LJ3a5M2z5v5Q5v5Q5v5Que...', 'admin');
```

### Docker Compose

```yaml
version: '3.8'

services:
  go2rtc:
    image: alexxit/go2rtc:latest
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./config/go2rtc.yaml:/config/go2rtc.yaml

  camera-manager:
    build: ./services/camera-manager
    network_mode: host
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://localhost:6379
      - POSTGRES_URL=postgresql://vision:${DB_PASSWORD}@localhost:5432/visionai
      - DISCOVERY_INTERVAL=300
      - HEALTH_CHECK_INTERVAL=60
    depends_on: [redis, postgres]

  detector:
    build: ./services/detector
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://vision:${DB_PASSWORD}@postgres:5432/visionai
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_USER}
      - MINIO_SECRET_KEY=${MINIO_PASSWORD}
      - MODEL_NAME=yolov10n
      - DETECTION_FPS=5
      - CONFIDENCE_THRESHOLD=0.5
      - GO2RTC_URL=http://host.docker.internal:1984
    depends_on: [go2rtc, redis, postgres, minio]

  api:
    build: ./services/api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_URL=postgresql://vision:${DB_PASSWORD}@postgres:5432/visionai
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_USER}
      - MINIO_SECRET_KEY=${MINIO_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
      - JWT_EXPIRY_MINUTES=60
    depends_on: [postgres, redis, minio]

  dashboard:
    build: ./services/dashboard
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_GO2RTC_URL=http://localhost:1984
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
    depends_on: [api]

  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      - POSTGRES_DB=visionai
      - POSTGRES_USER=vision
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./data/db:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - ./data/clips:/data
    ports:
      - "9000:9000"
      - "9001:9001"
```

### Key Implementation Details

#### Camera Manager - ONVIF Discovery
```python
# Use WS-Discovery to find all ONVIF cameras on the network
# Steps:
# 1. Send multicast probe to 239.255.255.250:3702
# 2. Collect responses with camera endpoints
# 3. Connect to each camera with credentials
# 4. Get device info, stream URIs, capabilities
# 5. Auto-generate go2rtc.yaml with all streams
# 6. Store camera info in PostgreSQL
# 7. Publish camera_discovered events to Redis
# 8. Run health checks every 60 seconds
```

#### Detector - Frame Processing Pipeline
```python
# For each enabled camera:
# 1. Pull frames from go2rtc sub-stream (RTSP) at DETECTION_FPS
# 2. Run YOLO inference on GPU
# 3. Apply zone filtering (only events inside defined zones)
# 4. Track objects across frames (ByteTrack)
# 5. On new detection:
#    a. Save snapshot to MinIO
#    b. Start clip recording (10 sec before + 10 sec after)
#    c. Insert event into PostgreSQL
#    d. Publish event to Redis Streams
# 6. Event consumers (alert service) pick up events and send notifications
```

#### Dashboard - Live Video
```python
# Use go2rtc's built-in WebRTC for ultra-low latency live view
# Each camera card connects directly to:
#   http://go2rtc:1984/api/ws?src={camera_name}
# Fallback to HLS if WebRTC fails:
#   http://go2rtc:1984/api/stream.m3u8?src={camera_name}
```

### Design Requirements

1. **UI Design**: Modern, dark theme (like Verkada). Clean, professional. Use shadcn/ui components.
2. **Responsive**: Works on desktop (primary) and tablet. Mobile is secondary.
3. **Real-time**: WebSocket for live event notifications on dashboard.
4. **Performance**: Dashboard must handle 64 camera thumbnails without lag.
5. **Error handling**: Graceful camera disconnection handling, auto-reconnect.
6. **Logging**: Structured JSON logging in all services.
7. **Local Access**: Dashboard must be accessible via the server's local IP address (e.g. http://192.168.x.x:3000) from any browser on the same network. The server will have a keyboard, mouse, and monitor connected — the operator opens a browser locally and accesses the dashboard. No reverse proxy needed for MVP, just bind to 0.0.0.0.

### What NOT to include in MVP
- Facial recognition (Phase 2)
- License plate recognition (Phase 2)
- CLIP text search (Phase 2)
- Multi-tenant (Phase 3)
- Mobile app (Phase 3)
- Heatmaps (Phase 2)
- **Security hardening** (YubiKey, LUKS, kiosk mode, AppArmor, USB blocking) — Phase 2
- **SSL/HTTPS** — not needed for MVP, runs on local network only
- **Reverse proxy (nginx)** — not needed for MVP

### Environment Variables (.env.example)
```env
# Database
DB_PASSWORD=changeme_secure_password

# JWT
JWT_SECRET=changeme_random_64_char_string

# MinIO
MINIO_USER=minioadmin
MINIO_PASSWORD=changeme_minio_password

# ONVIF Default Credentials (for auto-discovery)
ONVIF_DEFAULT_USER=admin
ONVIF_DEFAULT_PASS=admin123

# Detection
DETECTION_FPS=5
CONFIDENCE_THRESHOLD=0.5
MODEL_NAME=yolov10n

# Alerts
WEBHOOK_URL=https://your-webhook-url
WHATSAPP_WEBHOOK_URL=https://your-whatsapp-api
```

### Build Instructions
The entire system must start with:
```bash
cp .env.example .env
# Edit .env with real values
docker compose up -d
# Open http://SERVER_IP:3000 from any browser on the local network
# Or http://localhost:3000 from the server itself
```

**Important:** All services must bind to `0.0.0.0` (not `127.0.0.1`) so the dashboard and API are accessible from any device on the local network. The server has a monitor, keyboard, and mouse — the operator opens a local browser (Chromium/Firefox) and navigates to `http://localhost:3000` or the server's IP.

### Priority Order
Build in this order:
1. Docker Compose + PostgreSQL schema + Redis
2. Camera Manager (ONVIF discovery + go2rtc config)
3. API (auth + cameras CRUD + events CRUD)
4. Detector (YOLO + event recording)
5. Dashboard (login + camera grid + events page)
6. Alerts (webhook + event-driven notifications)
7. Zones (virtual perimeters + zone editor UI)

Build production-quality code. Include error handling, logging, and documentation. Make it robust enough to run 24/7 unattended.

### .gitignore (create this first)
```gitignore
# Environment
.env
.env.local
.env.production

# Data volumes
data/
*.db

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Node
node_modules/
.next/
out/
dist/

# Docker
docker-compose.override.yml

# Models (large files)
services/detector/models/*.pt
services/detector/models/*.onnx

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# MinIO data
data/clips/
data/redis/
data/db/
```

### Git Workflow
After building each component, commit and push:

```bash
# After Step 1 (Docker + DB):
git add -A && git commit -m "feat: docker compose, database schema, redis, minio setup" && git push

# After Step 2 (Camera Manager):
git add -A && git commit -m "feat: ONVIF camera discovery and management service" && git push

# After Step 3 (API):
git add -A && git commit -m "feat: FastAPI backend with auth, cameras, events, zones endpoints" && git push

# After Step 4 (Detector):
git add -A && git commit -m "feat: YOLO AI detection engine with event recording" && git push

# After Step 5 (Dashboard):
git add -A && git commit -m "feat: Next.js dashboard with live view, events, zones" && git push

# After Step 6 (Alerts):
git add -A && git commit -m "feat: webhook and WhatsApp alert system" && git push

# After Step 7 (Zones):
git add -A && git commit -m "feat: virtual zones and perimeter detection" && git push

# Final:
git add -A && git commit -m "docs: README, deployment guide, API docs" && git push
```

### README.md
Include a professional README with:
- Project logo placeholder
- Description
- Features list
- Screenshots placeholder
- Quick start guide
- Architecture overview
- Tech stack
- API documentation link
- License: Proprietary — © 2026 Data Network Solutions
- Contact: info@dnsit.com.mx

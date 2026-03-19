#!/bin/bash
# DNS Vision AI - First-time Setup Script
set -e

echo "=========================================="
echo "  DNS Vision AI - Setup"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    exit 1
fi

# Check NVIDIA Docker runtime (optional)
if command -v nvidia-smi &> /dev/null; then
    echo "[OK] NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader
else
    echo "[WARN] No NVIDIA GPU detected. AI detection will use CPU (slower)."
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env

    # Generate random passwords
    DB_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
    JWT_SEC=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 64)
    MINIO_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)

    sed -i "s/changeme_secure_password/$DB_PASS/" .env
    sed -i "s/changeme_random_64_char_string/$JWT_SEC/" .env
    sed -i "s/changeme_minio_password/$MINIO_PASS/" .env

    echo "[OK] .env created with random passwords"
else
    echo "[OK] .env already exists"
fi

# Create data directories
mkdir -p data/db data/redis data/clips
echo "[OK] Data directories created"

# Pull images
echo "Pulling Docker images..."
docker compose pull
echo "[OK] Images pulled"

# Build services
echo "Building services..."
docker compose build
echo "[OK] Services built"

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "Start the system with: docker compose up -d"
echo "Access dashboard at:   http://localhost:3000"
echo "Default login:         admin / admin123"
echo ""
echo "IMPORTANT: Change the admin password after first login!"
echo ""

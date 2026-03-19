#!/bin/bash
# DNS Vision AI - Backup Script
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting backup to $BACKUP_DIR..."

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U vision visionai > "$BACKUP_DIR/database.sql"
echo "[OK] Database backed up"

# Backup configuration
echo "Backing up configuration..."
cp -r config/ "$BACKUP_DIR/config/"
cp .env "$BACKUP_DIR/.env" 2>/dev/null || true
echo "[OK] Configuration backed up"

# Compress
echo "Compressing backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "Backup complete: $BACKUP_DIR.tar.gz"

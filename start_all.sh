#!/bin/bash
# DNS Vision AI — Start All Services

export CAMERA_IP="192.168.8.26"
export CAMERA_USER="dns"
export CAMERA_PASS="admin12345"
export CAMERA_NAME="hikvision_principal"
export AZURE_KEY="8SB6MDrRYgBJWAfbybO26TJQydLNJAfkWkzX0DLMZGupoo6HR6bJJQQJ99CCACYeBjFXJ3w3AAAFACOGp3iM"
export AZURE_ENDPOINT="https://dnsvisionprodemo.cognitiveservices.azure.com/"
export EVENTS_DIR="/home/manny/dns-vision-ai/events"
export BANK_DIR="/home/manny/dns-vision-ai/image_bank"
export HEATMAP_DIR="/home/manny/dns-vision-ai/heatmaps"
export ZONES_FILE="/home/manny/dns-vision-ai/config/zones.json"
export ZONE_EDITOR_PORT="8888"

BASE="/home/manny/dns-vision-ai"

echo "🎯 DNS Vision AI — Starting services..."

# Kill existing
pkill -f "motion_detector_azure" 2>/dev/null
pkill -f "heatmap_generator" 2>/dev/null
pkill -f "zone_editor" 2>/dev/null
sleep 1

# Start detector
echo "👀 Starting motion detector..."
nohup python3 $BASE/services/motion_detector/motion_detector_azure.py > $BASE/events/detector.log 2>&1 &
echo "  PID: $!"

# Start heatmap generator
echo "🔥 Starting heatmap generator..."
nohup python3 $BASE/services/heatmap/heatmap_generator.py > $BASE/events/heatmap.log 2>&1 &
echo "  PID: $!"

# Start zone editor
echo "🎯 Starting zone editor..."
nohup python3 $BASE/services/zone_editor/zone_editor.py > $BASE/events/zone_editor.log 2>&1 &
echo "  PID: $!"

echo ""
echo "✅ All services started!"
echo "🌐 Zone Editor: http://192.168.5.215:8888"
echo "📋 Logs: $BASE/events/*.log"

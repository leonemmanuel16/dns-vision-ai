#!/bin/bash
# DNS Vision AI - Script de inicio actualizado (Marzo 2026)

echo "🚀 Iniciando DNS Vision AI 2.0..."

# Load config
export $(cat config/dns-vision.env | grep -v '^#' | xargs)

# Check directories
mkdir -p events/{snapshots,metadata,videos,azure,fisheye_panels}
mkdir -p image_bank/{personas,descartados,fisheye}
mkdir -p logs

echo "📡 Verificando cámaras..."
python3 config/camera-test.py

echo ""
echo "🎯 Servicios disponibles:"
echo "  1. Motion Detector Principal - services/motion_detector/motion_detector_azure.py"
echo "  2. Motion Detector Fisheye    - services/motion_detector/motion_detector_fisheye.py"
echo "  3. Zone Editor               - services/zone_editor/zone_editor.py (puerto 8888)"
echo "  4. Heatmap Generator         - services/heatmap/heatmap_generator.py"
echo ""

echo "💡 Para iniciar detector principal:"
echo "   python3 services/motion_detector/motion_detector_azure.py"
echo ""

echo "💡 Para iniciar fisheye:"
echo "   python3 services/motion_detector/motion_detector_fisheye.py"
echo ""

echo "✅ DNS Vision AI listo para usar"
echo "📊 Versión: $(grep DNS_VISION_VERSION config/dns-vision.env | cut -d'=' -f2)"
echo "🧠 YOLO: $(grep YOLO_MODEL config/dns-vision.env | cut -d'=' -f2)"
echo "🔧 Ultralytics: $(python3 -c 'import ultralytics; print(ultralytics.__version__)' 2>/dev/null || echo 'No instalado')"
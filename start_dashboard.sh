#!/bin/bash
# DNS Vision AI - Dashboard Startup Script

echo "🚀 INICIANDO DASHBOARD DNS VISION AI"
echo "===================================="

cd /home/manny/dns-vision-ai/services/dashboard

# Verificar si ya está corriendo
if pgrep -f "next dev" > /dev/null; then
    echo "⚡ Dashboard ya está corriendo"
    PID=$(pgrep -f "next dev")
    echo "   PID: $PID"
else
    echo "🔧 Iniciando dashboard..."
    nohup npm run dev > dashboard.log 2>&1 &
    echo "   PID: $!"
    sleep 3
fi

# Verificar puerto
echo ""
echo "🌐 ACCESO AL DASHBOARD:"
echo "   • URL: http://localhost:3001"
echo "   • Tema: 🌞 Claro (blanco)"
echo "   • Logo: ✅ DNS Logo"
echo ""

echo "📊 CARACTERÍSTICAS:"
echo "   ✅ Detección en tiempo real"
echo "   ✅ Vista de cámaras"
echo "   ✅ Historial de eventos" 
echo "   ✅ Configuración de zonas"
echo "   ✅ Panel de alertas"
echo ""

echo "💡 Para detener: pkill -f 'next dev'"
echo "📋 Log: tail -f dashboard.log"
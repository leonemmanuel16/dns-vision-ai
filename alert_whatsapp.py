#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def send_whatsapp_alert(message, phone="+5218186651436"):
    """Envía alerta por WhatsApp usando la API de OpenClaw"""
    try:
        # URL del sistema de mensajes OpenClaw
        url = "http://localhost:8000/message"  # Ajustar según configuración
        
        data = {
            "action": "send",
            "channel": "whatsapp", 
            "target": phone,
            "message": f"🚨 DNS Vision AI Alert\n\n{message}\n\nTiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Alerta enviada: {message}")
        else:
            print(f"❌ Error enviando alerta: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_whatsapp_alert("Sistema de alertas configurado correctamente")

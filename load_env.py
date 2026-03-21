#!/usr/bin/env python3
"""
Utilitad para cargar variables de entorno desde config/dns-vision.env
"""
import os
from pathlib import Path

def load_env_from_file(env_file_path="config/dns-vision.env"):
    """Carga variables de entorno desde archivo"""
    env_path = Path(env_file_path)
    if not env_path.exists():
        print(f"⚠️ Archivo {env_file_path} no encontrado")
        return False
    
    loaded = 0
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                loaded += 1
    
    print(f"✅ {loaded} variables cargadas desde {env_file_path}")
    return True

if __name__ == "__main__":
    load_env_from_file()
    print("\n📊 Variables principales:")
    for var in ["CAMERA_IP", "CAMERA_USER", "CAMERA_PASS", "FISHEYE_IP"]:
        print(f"  {var}: {os.environ.get(var, 'NO DEFINIDA')}")
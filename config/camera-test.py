#!/usr/bin/env python3
"""Test rápido de conectividad a cámaras"""
import requests
from requests.auth import HTTPDigestAuth
import time

def test_camera(ip, user, password, name):
    try:
        # Probar con autenticación digest
        url = f'http://{ip}/ISAPI/Streaming/channels/101/picture'
        resp = requests.get(url, auth=HTTPDigestAuth(user, password), timeout=5)
        if resp.status_code == 200:
            print(f'✅ {name} ({ip}): OK - {len(resp.content)} bytes')
            return True
        else:
            print(f'❌ {name}: Status {resp.status_code}')
            return False
    except Exception as e:
        print(f'❌ {name}: {str(e)[:40]}...')
        return False

if __name__ == "__main__":
    print("🧪 Probando cámaras DNS Vision AI...")
    test_camera('192.168.8.26', 'dns', 'admin12345', 'Principal')
    test_camera('192.168.8.64', 'dns', 'admin12345', 'Fisheye')

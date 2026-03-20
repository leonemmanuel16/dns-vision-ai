#!/usr/bin/env python3
"""
DNS Vision AI - Portable Windows Package Creator
Creates a portable ZIP package for Windows deployment without PyInstaller
"""

import os
import shutil
import zipfile
import json
from pathlib import Path
from datetime import datetime

# Configuration
APP_NAME = "DNS Vision AI"
APP_VERSION = "0.1.0"
COMPANY_NAME = "DNS Data Network Solutions"

def create_package_structure():
    """Create portable package structure"""
    pkg_dir = Path("DNSVisionAI-Portable")
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    
    # Create directories
    dirs = [
        pkg_dir,
        pkg_dir / "app",
        pkg_dir / "app" / "services",
        pkg_dir / "app" / "dashboard",
        pkg_dir / "app" / "config",
        pkg_dir / "data",
        pkg_dir / "data" / "events",
        pkg_dir / "data" / "config",
        pkg_dir / "scripts"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    print("✅ Package structure created")
    return pkg_dir

def copy_application_files(pkg_dir):
    """Copy application files to package"""
    
    # Copy services
    services_src = Path("../../services")
    if services_src.exists():
        shutil.copytree(services_src, pkg_dir / "app" / "services", dirs_exist_ok=True)
    
    # Copy config templates
    config_src = Path("../../config")
    if config_src.exists():
        shutil.copytree(config_src, pkg_dir / "app" / "config", dirs_exist_ok=True)
    
    # Copy dashboard (if built)
    dashboard_src = Path("../../dashboard")
    if dashboard_src.exists():
        shutil.copytree(dashboard_src, pkg_dir / "app" / "dashboard", dirs_exist_ok=True)
    
    print("✅ Application files copied")

def create_windows_launcher(pkg_dir):
    """Create Windows launcher script"""
    
    launcher_code = '''@echo off
title DNS Vision AI
echo.
echo  ██████╗ ███╗   ██╗███████╗    ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗
echo  ██╔══██╗████╗  ██║██╔════╝    ██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║
echo  ██║  ██║██╔██╗ ██║███████╗    ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║
echo  ██║  ██║██║╚██╗██║╚════██║    ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║
echo  ██████╔╝██║ ╚████║███████║     ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║
echo  ╚═════╝ ╚═╝  ╚═══╝╚══════╝      ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
echo.
echo  AI-Powered Video Analytics Platform v0.1.0
echo  by DNS Data Network Solutions
echo.

:: Set environment variables
set PYTHONPATH=%~dp0app
set EVENTS_DIR=%~dp0data\\events
set CONFIG_DIR=%~dp0data\\config
set LOGS_DIR=%~dp0data\\logs

:: Create data directories if they don't exist
if not exist "%EVENTS_DIR%" mkdir "%EVENTS_DIR%"
if not exist "%EVENTS_DIR%\\snapshots" mkdir "%EVENTS_DIR%\\snapshots"
if not exist "%EVENTS_DIR%\\metadata" mkdir "%EVENTS_DIR%\\metadata"
if not exist "%EVENTS_DIR%\\videos" mkdir "%EVENTS_DIR%\\videos"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo ⚡ Checking Python dependencies...

:: Install requirements if needed
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️ Some dependencies failed to install, but continuing...
)

echo.
echo 🎯 Starting DNS Vision AI services...
echo.

:: Start API server
echo 📡 Starting API server on port 8000...
start /min cmd /c "cd /d %~dp0app\\services\\api && python main.py > %LOGS_DIR%\\api.log 2>&1"

:: Wait a moment for API to start
timeout /t 3 /nobreak >nul

:: Start motion detector
echo 🔍 Starting motion detector...
start /min cmd /c "cd /d %~dp0 && python app\\services\\motion_detector\\motion_detector_azure.py > %LOGS_DIR%\\detector.log 2>&1"

:: Wait for services to initialize
echo ⏳ Initializing services...
timeout /t 5 /nobreak >nul

:: Open dashboard in browser
echo 🌐 Opening dashboard...
start http://localhost:3000
start http://localhost:8000/docs

echo.
echo ✅ DNS Vision AI is now running!
echo.
echo 📊 Dashboard: http://localhost:3000
echo 🔌 API Docs: http://localhost:8000/docs
echo 📁 Data Directory: %~dp0data
echo 📋 Logs Directory: %~dp0data\\logs
echo.
echo Press Ctrl+C to stop all services, or close this window.
echo.

:: Keep the window open and monitor
:monitor
timeout /t 30 /nobreak >nul
echo [%date% %time%] Services running... (Press Ctrl+C to stop)
goto monitor
'''
    
    with open(pkg_dir / "start.bat", "w", encoding="utf-8") as f:
        f.write(launcher_code)
    
    print("✅ Windows launcher created")

def create_python_requirements(pkg_dir):
    """Create requirements.txt for Windows"""
    
    requirements = [
        "# DNS Vision AI - Windows Requirements",
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "sqlalchemy==2.0.23",
        "pydantic==2.5.0",
        "python-multipart==0.0.6",
        "Pillow==10.0.1",
        "",
        "# Computer Vision",
        "opencv-python==4.8.1.78",
        "numpy==1.24.3",
        "",
        "# AI/ML - CPU optimized for wider compatibility",
        "ultralytics==8.0.196",
        "torch==2.1.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu",
        "torchvision==0.16.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu",
        "",
        "# Network & HTTP",
        "requests==2.31.0",
        "urllib3==2.0.7",
        "websockets==12.0",
        "",
        "# Optional GPU support (user can upgrade manually)",
        "# torch==2.1.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118",
        "# torchvision==0.16.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118"
    ]
    
    with open(pkg_dir / "requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print("✅ Requirements file created")

def create_configuration_files(pkg_dir):
    """Create default configuration files"""
    
    # Default .env configuration
    env_config = {
        "# DNS Vision AI Configuration",
        "",
        "# Directories",
        "EVENTS_DIR=data/events",
        "CONFIG_DIR=data/config", 
        "LOGS_DIR=data/logs",
        "",
        "# API Settings",
        "API_HOST=0.0.0.0",
        "API_PORT=8000",
        "",
        "# Motion Detection", 
        "MOTION_THRESHOLD=8000",
        "COOLDOWN_SECONDS=15",
        "CHECK_INTERVAL=1.5",
        "",
        "# YOLO Configuration",
        "YOLO_MODEL=yolov8n.pt",
        "YOLO_CONF_THRESHOLD=0.5",
        "YOLO_DEVICE=cpu",
        "",
        "# Alerts (disabled by default)",
        "SEND_MOTION_FRAME_WHATSAPP=false",
        "USE_AZURE_VALIDATION=false",
        "ALERT_ONLY_IF_AZURE_PERSON=true",
        "",
        "# Azure Computer Vision (optional)",
        "AZURE_KEY=",
        "AZURE_ENDPOINT="
    }
    
    with open(pkg_dir / "data" / "config" / ".env", "w") as f:
        f.write("\n".join(env_config))
    
    # Simple camera configuration template
    camera_config = """# DNS Vision AI - Camera Configuration
# 
# Add your cameras here:
# 
# Format: CAMERA_<NAME>_IP=192.168.1.100
#         CAMERA_<NAME>_USER=username  
#         CAMERA_<NAME>_PASS=password
#         CAMERA_<NAME>_RTSP=rtsp://username:password@192.168.1.100:554/stream1
#
# Example:
# CAMERA_FRONT_DOOR_IP=192.168.1.100
# CAMERA_FRONT_DOOR_USER=admin
# CAMERA_FRONT_DOOR_PASS=admin12345
# CAMERA_FRONT_DOOR_RTSP=rtsp://admin:admin12345@192.168.1.100:554/stream1

"""
    
    with open(pkg_dir / "data" / "config" / "cameras.env", "w") as f:
        f.write(camera_config)
    
    print("✅ Configuration files created")

def create_readme(pkg_dir):
    """Create README with installation instructions"""
    
    readme_content = f"""# DNS Vision AI v{APP_VERSION} - Portable Edition

AI-powered video analytics platform for Windows.

## 🚀 Quick Start

1. **Extract** this package to a folder (e.g., `C:\\DNSVisionAI`)
2. **Double-click** `start.bat` to run
3. **Open browser** to http://localhost:3000 (dashboard)
4. **Configure cameras** in `data\\config\\cameras.env`

## 📋 Requirements

- **Windows 10/11** (64-bit)
- **Python 3.8+** installed with pip
- **4GB RAM** minimum, 8GB recommended
- **Internet connection** for dependency installation

### Python Installation
If you don't have Python:
1. Download from https://python.org/downloads/
2. **Check "Add Python to PATH"** during installation
3. Restart your computer
4. Run `start.bat` again

## ⚙️ Configuration

### Adding Cameras
Edit `data\\config\\cameras.env`:
```
CAMERA_FRONT_DOOR_IP=192.168.1.100
CAMERA_FRONT_DOOR_USER=admin  
CAMERA_FRONT_DOOR_PASS=password123
```

### Motion Detection Settings
Edit `data\\config\\.env`:
- `MOTION_THRESHOLD=8000` (lower = more sensitive)
- `COOLDOWN_SECONDS=15` (time between alerts)

### GPU Acceleration (Optional)
For NVIDIA GPUs:
```cmd
pip uninstall torch torchvision
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
```

## 🎛️ Usage

### Dashboard
- **URL:** http://localhost:3000
- **Features:** Live view, events, configuration

### API Documentation  
- **URL:** http://localhost:8000/docs
- **Features:** REST API, webhooks, integrations

### Logs & Data
- **Events:** `data\\events\\`
- **Logs:** `data\\logs\\`  
- **Configuration:** `data\\config\\`

## 🔧 Troubleshooting

### Common Issues

**"Python is not installed"**
- Install Python from python.org
- Make sure "Add to PATH" was checked

**"Module not found errors"**  
- Run: `pip install -r requirements.txt`
- Check internet connection

**"Port already in use"**
- Close other applications using ports 3000, 8000
- Or change ports in `data\\config\\.env`

**High CPU usage**
- Increase `MOTION_THRESHOLD` in config
- Reduce camera resolution
- Add GPU acceleration

### Getting Help

- **Documentation:** https://github.com/leonemmanuel16/dns-vision-ai
- **Issues:** Create GitHub issue
- **Commercial Support:** contact@dnsit.com.mx

## 📁 Directory Structure

```
DNSVisionAI-Portable/
├── start.bat              # Main launcher
├── requirements.txt       # Python dependencies  
├── app/                   # Application code
│   ├── services/          # Backend services
│   └── config/            # Default config
├── data/                  # User data
│   ├── events/            # Motion events
│   ├── config/            # User configuration
│   └── logs/              # Application logs
└── README.md              # This file
```

## 🔒 Security Notes

- Change default camera passwords
- Run on trusted networks only
- Consider firewall rules for production
- Regular security updates recommended

## ⚡ Performance Tips

- **CPU:** Intel Core i5+ or AMD Ryzen 5+ recommended
- **RAM:** 8GB+ for multiple cameras  
- **Storage:** SSD recommended for event storage
- **Network:** Gigabit Ethernet for HD cameras

---

**DNS Vision AI v{APP_VERSION}**  
© 2026 DNS Data Network Solutions  
https://dnsit.com.mx
"""
    
    with open(pkg_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README created")

def create_package_info(pkg_dir):
    """Create package information file"""
    
    package_info = {
        "name": APP_NAME,
        "version": APP_VERSION,
        "company": COMPANY_NAME,
        "build_date": datetime.now().isoformat(),
        "platform": "Windows",
        "type": "portable",
        "python_version": "3.8+",
        "dependencies": [
            "fastapi",
            "opencv-python", 
            "ultralytics",
            "torch",
            "numpy"
        ],
        "services": [
            "API Server (port 8000)",
            "Motion Detector", 
            "Dashboard (port 3000)"
        ]
    }
    
    with open(pkg_dir / "package.json", "w") as f:
        json.dump(package_info, f, indent=2)
    
    print("✅ Package info created")

def create_zip_package(pkg_dir):
    """Create final ZIP package"""
    
    zip_name = f"DNSVisionAI-Portable-v{APP_VERSION}-Windows.zip"
    
    print(f"📦 Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(pkg_dir):
            for file in files:
                file_path = Path(root) / file
                arc_name = file_path.relative_to(pkg_dir.parent)
                zipf.write(file_path, arc_name)
                
    # Get file size
    size_mb = Path(zip_name).stat().st_size / (1024 * 1024)
    
    print(f"✅ Package created: {zip_name} ({size_mb:.1f} MB)")
    return zip_name

def main():
    """Main packaging process"""
    print(f"🎯 Creating {APP_NAME} v{APP_VERSION} Portable Package")
    print("=" * 60)
    
    # Create package
    pkg_dir = create_package_structure()
    copy_application_files(pkg_dir)
    create_windows_launcher(pkg_dir)
    create_python_requirements(pkg_dir)
    create_configuration_files(pkg_dir)
    create_readme(pkg_dir)
    create_package_info(pkg_dir)
    
    # Create ZIP
    zip_file = create_zip_package(pkg_dir)
    
    print("=" * 60)
    print(f"✅ {APP_NAME} portable package completed!")
    print(f"📦 File: {zip_file}")
    print(f"📁 Extract and run 'start.bat' on Windows")
    print(f"🌐 Dashboard: http://localhost:3000")
    print(f"🔌 API: http://localhost:8000")
    
    return 0

if __name__ == "__main__":
    exit(main())
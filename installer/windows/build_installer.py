#!/usr/bin/env python3
"""
DNS Vision AI - Windows Installer Builder
Creates a standalone .exe installer for Windows deployment
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

# Configuration
APP_NAME = "DNS Vision AI"
APP_VERSION = "0.1.0"
COMPANY_NAME = "DNS Data Network Solutions"
INSTALLER_NAME = f"DNSVisionAI-Setup-v{APP_VERSION}.exe"

def create_build_structure():
    """Create build directory structure"""
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    dirs = [
        "build/app",
        "build/app/services",
        "build/app/dashboard", 
        "build/app/config",
        "build/app/models",
        "build/scripts",
        "build/resources"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    print("✅ Build structure created")

def copy_backend_files():
    """Copy Python backend files"""
    backend_files = [
        "../../services/api",
        "../../services/motion_detector", 
        "../../services/camera-manager",
        "../../config",
        "../../requirements.txt"
    ]
    
    for src in backend_files:
        src_path = Path(src)
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, f"build/app/{src_path.name}", dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, "build/app/")
    
    print("✅ Backend files copied")

def create_main_launcher():
    """Create main application launcher"""
    launcher_code = '''
import sys
import os
import subprocess
import threading
import time
from pathlib import Path
import uvicorn
from fastapi import FastAPI

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

class DNSVisionAI:
    def __init__(self):
        self.api_process = None
        self.detector_process = None
        
    def start_api(self):
        """Start FastAPI backend"""
        os.chdir(app_dir / "services" / "api")
        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info"
        )
        server = uvicorn.Server(config)
        server.run()
        
    def start_detector(self):
        """Start motion detector"""
        detector_script = app_dir / "services" / "motion_detector" / "motion_detector_azure.py"
        subprocess.run([sys.executable, str(detector_script)])
        
    def start_dashboard(self):
        """Start Next.js dashboard"""
        dashboard_dir = app_dir / "dashboard"
        os.chdir(dashboard_dir)
        subprocess.run(["npm", "run", "start"])
        
    def run(self):
        """Run all services"""
        print("🎯 Starting DNS Vision AI...")
        
        # Start API in background thread
        api_thread = threading.Thread(target=self.start_api)
        api_thread.daemon = True
        api_thread.start()
        
        # Start detector in background thread  
        detector_thread = threading.Thread(target=self.start_detector)
        detector_thread.daemon = True
        detector_thread.start()
        
        print("✅ DNS Vision AI started successfully!")
        print("📊 Dashboard: http://localhost:3000")
        print("🔌 API: http://localhost:8000")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n⛔ Stopping DNS Vision AI...")

if __name__ == "__main__":
    app = DNSVisionAI()
    app.run()
'''
    
    with open("build/dns_vision_ai.py", "w") as f:
        f.write(launcher_code)
    
    print("✅ Main launcher created")

def create_windows_service():
    """Create Windows service wrapper"""
    service_code = '''
import win32serviceutil
import win32service
import win32event
import subprocess
import sys
from pathlib import Path

class DNSVisionAIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DNSVisionAI"
    _svc_display_name_ = "DNS Vision AI Service"
    _svc_description_ = "AI-powered video analytics platform"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        app_dir = Path(__file__).parent
        launcher = app_dir / "dns_vision_ai.py"
        self.process = subprocess.Popen([sys.executable, str(launcher)])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DNSVisionAIService)
'''
    
    with open("build/dns_vision_service.py", "w") as f:
        f.write(service_code)
    
    print("✅ Windows service created")

def create_requirements():
    """Create consolidated requirements.txt"""
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "opencv-python==4.8.1.78",
        "numpy==1.24.3",
        "pillow==10.0.1",
        "sqlalchemy==2.0.23",
        "asyncpg==0.29.0",
        "redis==5.0.1",
        "minio==7.1.17",
        "ultralytics==8.0.196",  # YOLOv8
        "torch==2.1.0",
        "torchvision==0.16.0",
        "pywin32==306",  # Windows services
        "requests==2.31.0",
        "python-multipart==0.0.6"
    ]
    
    with open("build/requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print("✅ Requirements file created")

def create_install_script():
    """Create installation script"""
    install_script = '''
@echo off
echo 🎯 Installing DNS Vision AI...

:: Create installation directory
set INSTALL_DIR=%ProgramFiles%\\DNS Vision AI
mkdir "%INSTALL_DIR%" 2>nul

:: Copy application files
echo Copying application files...
xcopy /E /I /Y app "%INSTALL_DIR%\\app\\"
copy dns_vision_ai.py "%INSTALL_DIR%\\"
copy dns_vision_service.py "%INSTALL_DIR%\\"
copy requirements.txt "%INSTALL_DIR%\\"

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r "%INSTALL_DIR%\\requirements.txt"

:: Install and start Windows service
echo Installing Windows service...
python "%INSTALL_DIR%\\dns_vision_service.py" install
python "%INSTALL_DIR%\\dns_vision_service.py" start

:: Create desktop shortcuts
echo Creating shortcuts...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\\Desktop\\DNS Vision AI Dashboard.lnk'); $Shortcut.TargetPath = 'http://localhost:3000'; $Shortcut.Save()"

echo ✅ Installation completed!
echo 📊 Dashboard: http://localhost:3000
echo 🔌 API: http://localhost:8000
pause
'''
    
    with open("build/scripts/install.bat", "w") as f:
        f.write(install_script)
    
    print("✅ Install script created")

def create_inno_setup_script():
    """Create Inno Setup configuration"""
    inno_script = f'''
[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
AppPublisher={COMPANY_NAME}
AppPublisherURL=https://dnsit.com.mx
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir=dist
OutputBaseFilename={INSTALLER_NAME.replace('.exe', '')}
SetupIconFile=resources\\icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "app\\*"; DestDir: "{{app}}\\app"; Flags: recursesubdirs createallsubdirs
Source: "dns_vision_ai.py"; DestDir: "{{app}}"
Source: "dns_vision_service.py"; DestDir: "{{app}}"  
Source: "requirements.txt"; DestDir: "{{app}}"
Source: "scripts\\*"; DestDir: "{{app}}\\scripts"

[Icons]
Name: "{{group}}\\{APP_NAME} Dashboard"; Filename: "http://localhost:3000"
Name: "{{group}}\\{APP_NAME} API"; Filename: "http://localhost:8000"
Name: "{{commondesktop}}\\{APP_NAME} Dashboard"; Filename: "http://localhost:3000"

[Run]
Filename: "pip"; Parameters: "install -r ""{{app}}\\requirements.txt"""; StatusMsg: "Installing Python dependencies..."
Filename: "python"; Parameters: """{{app}}\\dns_vision_service.py"" install"; StatusMsg: "Installing Windows service..."
Filename: "python"; Parameters: """{{app}}\\dns_vision_service.py"" start"; StatusMsg: "Starting service..."

[UninstallRun]
Filename: "python"; Parameters: """{{app}}\\dns_vision_service.py"" stop"; RunOnceId: "StopService"
Filename: "python"; Parameters: """{{app}}\\dns_vision_service.py"" remove"; RunOnceId: "RemoveService"
'''
    
    with open("build/dns_vision_ai.iss", "w") as f:
        f.write(inno_script)
    
    print("✅ Inno Setup script created")

def build_executable():
    """Build standalone executable using PyInstaller"""
    print("🔨 Building standalone executable...")
    
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed", 
        "--name", "DNSVisionAI",
        "--add-data", "build/app;app",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "cv2",
        "--hidden-import", "ultralytics",
        "build/dns_vision_ai.py"
    ]
    
    try:
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("✅ Executable built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def create_installer():
    """Create installer using Inno Setup"""
    print("📦 Creating installer...")
    
    # Check if Inno Setup is available
    inno_setup_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not Path(inno_setup_path).exists():
        print("⚠️ Inno Setup not found. Creating portable version instead.")
        create_portable_package()
        return
    
    try:
        subprocess.run([inno_setup_path, "build/dns_vision_ai.iss"], check=True)
        print(f"✅ Installer created: {INSTALLER_NAME}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installer creation failed: {e}")
        create_portable_package()

def create_portable_package():
    """Create portable ZIP package"""
    print("📦 Creating portable package...")
    
    import zipfile
    
    zip_name = f"DNSVisionAI-Portable-v{APP_VERSION}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all build files
        for root, dirs, files in os.walk("build"):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to("build")
                zipf.write(file_path, arcname)
    
    print(f"✅ Portable package created: {zip_name}")

def main():
    """Main build process"""
    print(f"🎯 Building {APP_NAME} v{APP_VERSION} Windows Installer")
    print("=" * 60)
    
    # Create build structure
    create_build_structure()
    
    # Copy files
    copy_backend_files()
    
    # Create application components
    create_main_launcher()
    create_windows_service()
    create_requirements()
    create_install_script()
    create_inno_setup_script()
    
    # Build executable
    if build_executable():
        create_installer()
    else:
        print("❌ Build failed")
        return 1
    
    print("=" * 60)
    print(f"✅ {APP_NAME} installer build completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
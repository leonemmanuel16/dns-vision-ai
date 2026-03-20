#!/usr/bin/env python3
"""
DNS Vision AI - Windows Configuration
Sets up environment and configuration for Windows deployment
"""

import os
import json
import winreg
from pathlib import Path
import tempfile

class WindowsConfig:
    def __init__(self):
        self.install_dir = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "DNS Vision AI"
        self.data_dir = Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / "DNS Vision AI"
        self.user_dir = Path(os.path.expanduser('~')) / "DNS Vision AI"
        
    def create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.data_dir / "events",
            self.data_dir / "events" / "snapshots", 
            self.data_dir / "events" / "metadata",
            self.data_dir / "events" / "videos",
            self.data_dir / "events" / "azure",
            self.data_dir / "image_bank",
            self.data_dir / "image_bank" / "personas",
            self.data_dir / "image_bank" / "descartados",
            self.data_dir / "config",
            self.data_dir / "logs",
            self.user_dir / "exports"
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
        print("✅ Directories created")
        
    def create_default_config(self):
        """Create default configuration files"""
        # Default environment configuration
        env_config = {
            "EVENTS_DIR": str(self.data_dir / "events"),
            "BANK_DIR": str(self.data_dir / "image_bank"),
            "CONFIG_DIR": str(self.data_dir / "config"),
            "LOGS_DIR": str(self.data_dir / "logs"),
            
            # API Configuration
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "API_WORKERS": "1",
            
            # Dashboard Configuration
            "DASHBOARD_PORT": "3000",
            
            # Database (SQLite for Windows by default)
            "DATABASE_URL": f"sqlite:///{self.data_dir}/dns_vision.db",
            
            # Redis (embedded/local)
            "REDIS_URL": "redis://localhost:6379",
            
            # Motion Detection
            "MOTION_THRESHOLD": "8000",
            "COOLDOWN_SECONDS": "15",
            "CHECK_INTERVAL": "1.5",
            "FRAMES_PER_EVENT": "5",
            
            # YOLO Configuration
            "YOLO_MODEL": "yolov8n.pt",
            "YOLO_CONF_THRESHOLD": "0.5",
            "YOLO_DEVICE": "cpu",  # Default to CPU, detect GPU later
            
            # Azure (optional)
            "AZURE_KEY": "",
            "AZURE_ENDPOINT": "",
            
            # Alerts
            "SEND_MOTION_FRAME_WHATSAPP": "false",
            "USE_AZURE_VALIDATION": "false",
            "ALERT_ONLY_IF_AZURE_PERSON": "true"
        }
        
        # Save to .env file
        env_file = self.data_dir / "config" / ".env"
        with open(env_file, "w") as f:
            for key, value in env_config.items():
                f.write(f"{key}={value}\n")
                
        # Camera configuration template
        cameras_config = {
            "api": {
                "listen": ":1984"
            },
            "rtsp": {
                "listen": ":8554"
            },
            "webrtc": {
                "listen": ":8555"
            },
            "streams": {
                "example_camera": [
                    "rtsp://username:password@192.168.1.100:554/stream1"
                ]
            }
        }
        
        camera_file = self.data_dir / "config" / "cameras.yaml"
        with open(camera_file, "w") as f:
            import yaml
            yaml.dump(cameras_config, f, default_flow_style=False)
            
        print("✅ Default configuration created")
        
    def setup_windows_registry(self):
        """Setup Windows registry entries"""
        try:
            # Create registry key for application
            key_path = r"SOFTWARE\DNS Data Network Solutions\DNS Vision AI"
            
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, str(self.install_dir))
                winreg.SetValueEx(key, "DataPath", 0, winreg.REG_SZ, str(self.data_dir))
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, "0.1.0")
                
            print("✅ Registry entries created")
            
        except Exception as e:
            print(f"⚠️ Registry setup failed: {e}")
            
    def setup_firewall_rules(self):
        """Setup Windows Firewall rules"""
        import subprocess
        
        rules = [
            ("DNS Vision AI API", "8000"),
            ("DNS Vision AI Dashboard", "3000"),
            ("DNS Vision AI go2rtc", "1984"),
            ("DNS Vision AI RTSP", "8554"),
            ("DNS Vision AI WebRTC", "8555")
        ]
        
        for name, port in rules:
            try:
                cmd = [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={name}",
                    "dir=in",
                    "action=allow",
                    "protocol=TCP",
                    f"localport={port}"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✅ Firewall rule added: {name} (port {port})")
            except subprocess.CalledProcessError:
                print(f"⚠️ Failed to add firewall rule: {name}")
                
    def detect_gpu(self):
        """Detect available GPU and update configuration"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"✅ NVIDIA GPU detected: {gpu_name}")
                
                # Update YOLO device to GPU
                env_file = self.data_dir / "config" / ".env"
                if env_file.exists():
                    with open(env_file, "r") as f:
                        content = f.read()
                    
                    content = content.replace("YOLO_DEVICE=cpu", "YOLO_DEVICE=0")
                    
                    with open(env_file, "w") as f:
                        f.write(content)
                        
                    print("✅ Configuration updated for GPU acceleration")
                    
        except ImportError:
            print("⚠️ PyTorch not available for GPU detection")
        except Exception as e:
            print(f"⚠️ GPU detection failed: {e}")
            
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts"""
        try:
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            
            # Dashboard shortcut
            shortcut = shell.CreateShortCut(str(Path(desktop) / "DNS Vision AI Dashboard.lnk"))
            shortcut.Targetpath = "http://localhost:3000"
            shortcut.IconLocation = str(self.install_dir / "resources" / "icon.ico")
            shortcut.Description = "DNS Vision AI Dashboard"
            shortcut.save()
            
            # API Documentation shortcut
            shortcut = shell.CreateShortCut(str(Path(desktop) / "DNS Vision AI API.lnk"))
            shortcut.Targetpath = "http://localhost:8000/docs"
            shortcut.IconLocation = str(self.install_dir / "resources" / "icon.ico")
            shortcut.Description = "DNS Vision AI API Documentation"
            shortcut.save()
            
            print("✅ Desktop shortcuts created")
            
        except Exception as e:
            print(f"⚠️ Shortcut creation failed: {e}")
            
    def configure_system_service(self):
        """Configure and start Windows service"""
        try:
            service_script = self.install_dir / "dns_vision_service.py"
            
            if service_script.exists():
                import subprocess
                
                # Install service
                result = subprocess.run([
                    "python", str(service_script), "install"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Windows service installed")
                    
                    # Start service
                    result = subprocess.run([
                        "python", str(service_script), "start"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ Windows service started")
                    else:
                        print(f"⚠️ Service start failed: {result.stderr}")
                else:
                    print(f"⚠️ Service install failed: {result.stderr}")
                    
        except Exception as e:
            print(f"⚠️ Service configuration failed: {e}")
            
    def run_setup(self):
        """Run complete Windows setup"""
        print("🎯 Configuring DNS Vision AI for Windows...")
        print("=" * 50)
        
        self.create_directories()
        self.create_default_config()
        self.setup_windows_registry()
        self.setup_firewall_rules()
        self.detect_gpu()
        self.create_desktop_shortcuts()
        self.configure_system_service()
        
        print("=" * 50)
        print("✅ Windows configuration completed!")
        print(f"📊 Dashboard: http://localhost:3000")
        print(f"🔌 API: http://localhost:8000")
        print(f"📁 Data Directory: {self.data_dir}")

if __name__ == "__main__":
    config = WindowsConfig()
    config.run_setup()
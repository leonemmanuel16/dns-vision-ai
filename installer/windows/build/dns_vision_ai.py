
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
            print("\n⛔ Stopping DNS Vision AI...")

if __name__ == "__main__":
    app = DNSVisionAI()
    app.run()

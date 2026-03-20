
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

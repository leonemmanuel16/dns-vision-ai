
[Setup]
AppName=DNS Vision AI
AppVersion=0.1.0
AppPublisher=DNS Data Network Solutions
AppPublisherURL=https://dnsit.com.mx
DefaultDirName={autopf}\DNS Vision AI
DefaultGroupName=DNS Vision AI
OutputDir=dist
OutputBaseFilename=DNSVisionAI-Setup-v0.1.0
SetupIconFile=resources\icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "app\*"; DestDir: "{app}\app"; Flags: recursesubdirs createallsubdirs
Source: "dns_vision_ai.py"; DestDir: "{app}"
Source: "dns_vision_service.py"; DestDir: "{app}"  
Source: "requirements.txt"; DestDir: "{app}"
Source: "scripts\*"; DestDir: "{app}\scripts"

[Icons]
Name: "{group}\DNS Vision AI Dashboard"; Filename: "http://localhost:3000"
Name: "{group}\DNS Vision AI API"; Filename: "http://localhost:8000"
Name: "{commondesktop}\DNS Vision AI Dashboard"; Filename: "http://localhost:3000"

[Run]
Filename: "pip"; Parameters: "install -r ""{app}\requirements.txt"""; StatusMsg: "Installing Python dependencies..."
Filename: "python"; Parameters: """{app}\dns_vision_service.py"" install"; StatusMsg: "Installing Windows service..."
Filename: "python"; Parameters: """{app}\dns_vision_service.py"" start"; StatusMsg: "Starting service..."

[UninstallRun]
Filename: "python"; Parameters: """{app}\dns_vision_service.py"" stop"; RunOnceId: "StopService"
Filename: "python"; Parameters: """{app}\dns_vision_service.py"" remove"; RunOnceId: "RemoveService"

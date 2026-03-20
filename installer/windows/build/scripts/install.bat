
@echo off
echo 🎯 Installing DNS Vision AI...

:: Create installation directory
set INSTALL_DIR=%ProgramFiles%\DNS Vision AI
mkdir "%INSTALL_DIR%" 2>nul

:: Copy application files
echo Copying application files...
xcopy /E /I /Y app "%INSTALL_DIR%\app\"
copy dns_vision_ai.py "%INSTALL_DIR%\"
copy dns_vision_service.py "%INSTALL_DIR%\"
copy requirements.txt "%INSTALL_DIR%\"

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r "%INSTALL_DIR%\requirements.txt"

:: Install and start Windows service
echo Installing Windows service...
python "%INSTALL_DIR%\dns_vision_service.py" install
python "%INSTALL_DIR%\dns_vision_service.py" start

:: Create desktop shortcuts
echo Creating shortcuts...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\DNS Vision AI Dashboard.lnk'); $Shortcut.TargetPath = 'http://localhost:3000'; $Shortcut.Save()"

echo ✅ Installation completed!
echo 📊 Dashboard: http://localhost:3000
echo 🔌 API: http://localhost:8000
pause

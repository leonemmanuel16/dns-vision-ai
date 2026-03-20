@echo off
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
set EVENTS_DIR=%~dp0data\events
set CONFIG_DIR=%~dp0data\config
set LOGS_DIR=%~dp0data\logs

:: Create data directories if they don't exist
if not exist "%EVENTS_DIR%" mkdir "%EVENTS_DIR%"
if not exist "%EVENTS_DIR%\snapshots" mkdir "%EVENTS_DIR%\snapshots"
if not exist "%EVENTS_DIR%\metadata" mkdir "%EVENTS_DIR%\metadata"
if not exist "%EVENTS_DIR%\videos" mkdir "%EVENTS_DIR%\videos"
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
start /min cmd /c "cd /d %~dp0app\services\api && python main.py > %LOGS_DIR%\api.log 2>&1"

:: Wait a moment for API to start
timeout /t 3 /nobreak >nul

:: Start motion detector
echo 🔍 Starting motion detector...
start /min cmd /c "cd /d %~dp0 && python app\services\motion_detector\motion_detector_azure.py > %LOGS_DIR%\detector.log 2>&1"

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
echo 📋 Logs Directory: %~dp0data\logs
echo.
echo Press Ctrl+C to stop all services, or close this window.
echo.

:: Keep the window open and monitor
:monitor
timeout /t 30 /nobreak >nul
echo [%date% %time%] Services running... (Press Ctrl+C to stop)
goto monitor

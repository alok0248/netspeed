@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo [%date% %time%] Starting NetSpeed overlay... >> "%~dp0netspeed.log"
start "" pythonw.exe -u -m netspeed_tracker.main >> "%~dp0netspeed.log" 2>&1
timeout /t 2 >nul
if not errorlevel 1 (
    echo [%date% %time%] NetSpeed started successfully >> "%~dp0netspeed.log"
) else (
    echo [%date% %time%] Failed to start NetSpeed >> "%~dp0netspeed.log"
)

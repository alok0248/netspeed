
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
cd netspeed_tracker
python main.py
pause

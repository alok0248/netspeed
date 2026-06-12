@echo off
echo ========================================
echo Welcome to NetSpeed Tracker!
echo Setting everything up for you...
echo ========================================
echo.

cd /d "%~dp0"

:: Check if venv already exists
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment already exists. Skipping venv creation.
) else (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment! Make sure Python is installed.
        pause
        exit /b 1
    )
)

:: Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete! Now launching the app...
echo ========================================
echo.

:: Run the app
call run.bat

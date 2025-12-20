@echo off
echo ================================================
echo CivicFix Backend - Quick Start (Fixed)
echo ================================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it
    pause
    exit /b 1
)

REM Start the backend with optimized settings
echo Starting CivicFix backend...
python quick_start_fixed.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Backend failed to start. Check the error above.
    pause
)
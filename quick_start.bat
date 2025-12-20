@echo off
echo ========================================
echo CivicFix Backend - Quick Start
echo ========================================
echo.
echo Starting backend with SQLite database...
echo This bypasses AWS/Firebase for faster startup
echo.

:: Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

:: Set environment for quick start
set DATABASE_URL=sqlite:///civicfix.db
set AWS_ACCESS_KEY_ID=
set AWS_SECRET_ACCESS_KEY=
set FIREBASE_SERVICE_ACCOUNT_PATH=

:: Start the backend
python quick_start.py

pause
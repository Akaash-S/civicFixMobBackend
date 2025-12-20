@echo off
echo ========================================
echo Starting CivicFix Backend Server
echo ========================================

:: Check if virtual environment exists
if not exist venv (
    echo Error: Virtual environment not found!
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if .env file exists
if not exist .env (
    echo Warning: .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please configure your .env file before starting the server
    pause
    exit /b 1
)

:: Start the backend
echo Starting Flask server...
echo Server will be available at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python run.py

pause
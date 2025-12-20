@echo off
echo ========================================
echo CivicFix Database Initialization
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
    echo Error: .env file not found
    echo Please configure your database settings in .env file
    pause
    exit /b 1
)

:: Initialize database
echo Initializing database...
python init_database.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Database initialization completed!
    echo ========================================
    echo.
    echo You can now start the backend with:
    echo start_backend.bat
) else (
    echo.
    echo Database initialization failed!
    echo Please check your database configuration in .env file
)

pause
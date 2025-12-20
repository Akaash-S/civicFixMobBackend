# CivicFix Backend Startup Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting CivicFix Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_windows.ps1 first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Blue
    Copy-Item ".env.example" ".env"
    Write-Host "Please configure your .env file before starting the server" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the backend
Write-Host "Starting Flask server..." -ForegroundColor Green
Write-Host "Server will be available at http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python run.py
} catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
@echo off
REM CivicFix Backend Production Deployment Script for Windows
REM This script handles the complete production deployment process

setlocal enabledelayedexpansion

echo ==========================================
echo CivicFix Backend - Production Deployment
echo ==========================================

REM Configuration
set APP_NAME=civicfix-backend
set DOCKER_IMAGE=civicfix/backend
set DOCKER_TAG=latest
set CONTAINER_NAME=civicfix-backend-prod

REM Check prerequisites
echo [INFO] Checking prerequisites...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if production environment file exists
if not exist ".env.production" (
    echo [ERROR] Production environment file (.env.production) not found.
    echo [INFO] Please create .env.production with production settings.
    exit /b 1
)

REM Check if service account file exists
if not exist "service-account.json" (
    echo [ERROR] Firebase service account file (service-account.json) not found.
    exit /b 1
)

echo [INFO] Prerequisites check passed ✓

REM Build Docker image
echo [INFO] Building Docker image...
docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)
echo [INFO] Docker image built successfully ✓

REM Stop existing container
echo [INFO] Stopping existing container...
docker ps -q -f name=%CONTAINER_NAME% >nul 2>&1
if not errorlevel 1 (
    docker stop %CONTAINER_NAME%
    docker rm %CONTAINER_NAME%
    echo [INFO] Existing container stopped and removed ✓
) else (
    echo [INFO] No existing container found
)

REM Run database migrations
echo [INFO] Running database migrations...
docker run --rm --env-file .env.production %DOCKER_IMAGE%:%DOCKER_TAG% python -c "from app import create_app; from app.config import config; from app.extensions import db; app, _ = create_app(config['production']); app.app_context().push(); db.create_all(); print('Database migrations completed')"
if errorlevel 1 (
    echo [ERROR] Database migrations failed
    exit /b 1
)
echo [INFO] Database migrations completed ✓

REM Start production container
echo [INFO] Starting production container...
docker run -d --name %CONTAINER_NAME% --env-file .env.production -p 5000:5000 --restart unless-stopped --health-cmd="curl -f http://localhost:5000/health || exit 1" --health-interval=30s --health-timeout=10s --health-retries=3 %DOCKER_IMAGE%:%DOCKER_TAG%
if errorlevel 1 (
    echo [ERROR] Failed to start production container
    exit /b 1
)
echo [INFO] Production container started successfully ✓

REM Wait for health check
echo [INFO] Waiting for application to be healthy...
set /a counter=0
:healthcheck
set /a counter+=1
if %counter% gtr 30 (
    echo [ERROR] Application failed to become healthy
    docker logs %CONTAINER_NAME%
    exit /b 1
)

docker exec %CONTAINER_NAME% curl -f http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [INFO] Waiting for health check... (%counter%/30)
    timeout /t 2 >nul
    goto healthcheck
)

echo [INFO] Application is healthy ✓

REM Show deployment status
echo [INFO] Deployment Status:
echo ====================

echo Container Status:
docker ps -f name=%CONTAINER_NAME% --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Health Check:
curl -s http://localhost:5000/health

echo.
echo Recent Logs:
docker logs --tail 10 %CONTAINER_NAME%

echo.
echo [INFO] 🎉 Production deployment completed successfully!
echo [INFO] Application is running at: http://localhost:5000
echo [INFO] Health check: http://localhost:5000/health

pause
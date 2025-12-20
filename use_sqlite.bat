@echo off
echo Switching to SQLite for development...

:: Backup current .env
if exist .env (
    copy .env .env.backup >nul
    echo Backed up .env to .env.backup
)

:: Create new .env with SQLite
(
echo FLASK_APP=run.py
echo FLASK_ENV=development
echo SECRET_KEY=655547171e7d249d329c1b1a61ba82082cb48beabdd733d14cb20feb92ae613521f4602c6fbcecb90af05fb05624926cc157417f0f4416c311462373a551e51f
echo.
echo # Database - SQLite for development
echo DATABASE_URL=sqlite:///civicfix.db
echo.
echo # AWS Configuration ^(optional for development^)
echo AWS_ACCESS_KEY_ID=AKIAUT7VVE5BGNNI4A63
echo AWS_SECRET_ACCESS_KEY=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
echo AWS_REGION=ap-south-1
echo S3_BUCKET_NAME=civicfix-media-uploads
echo.
echo # Firebase Configuration ^(optional for development^)
echo FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
echo FIREBASE_PROJECT_ID=meeting-assistant-92613
echo.
echo # Redis ^(optional for development^)
echo REDIS_URL=redis://localhost:6379/0
echo.
echo # File Upload Settings
echo MAX_CONTENT_LENGTH=16777216
echo ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov
echo.
echo # API Settings
echo API_VERSION=v1
echo CORS_ORIGINS=*
echo.
echo # Socket.IO
echo SOCKETIO_ASYNC_MODE=threading
) > .env

echo.
echo SUCCESS: Switched to SQLite database
echo Database file: civicfix.db
echo.
echo Next steps:
echo 1. Initialize database: python init_database.py
echo 2. Start backend: start_backend.bat
echo.
pause
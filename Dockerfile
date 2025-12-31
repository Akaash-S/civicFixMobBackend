# CivicFix Backend - Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    SKIP_VALIDATION=true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies individually to avoid conflicts
RUN pip install --upgrade pip

# Core Flask packages
RUN pip install Flask==3.0.0
RUN pip install Flask-SQLAlchemy==3.1.1
RUN pip install Flask-CORS==4.0.0

# Database
RUN pip install psycopg2-binary==2.9.9

# AWS (let it resolve dependencies automatically)
RUN pip install boto3

# Authentication
RUN pip install PyJWT

# Utilities
RUN pip install python-dotenv
RUN pip install requests
RUN pip install gunicorn

# Optional packages (install if possible, continue if not)
RUN pip install firebase-admin || echo "Firebase admin not installed"

# Copy application files
COPY app.py .
COPY startup.sh .

# Copy utility scripts
COPY validate_aws_setup.py .
COPY migrate_database.py .
COPY test_docker_startup.py .

# Copy test files
COPY test_auth_quick.py .
COPY test_user_sync.py .

# Copy environment file
COPY .env ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x startup.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Use startup script as entrypoint
CMD ["./startup.sh"]
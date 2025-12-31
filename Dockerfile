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

# Copy requirements first for better Docker layer caching
COPY requirements-clean.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY startup.sh .

# Copy utility scripts (optional but useful for debugging)
COPY validate_aws_setup.py .
COPY migrate_database.py .
COPY test_docker_startup.py .

# Copy test files (optional)
COPY test_auth_quick.py .
COPY test_user_sync.py .

# Copy migration files (if they exist)
COPY add_*.py ./
COPY create_*.py ./
COPY migrate_*.py ./

# Copy environment file (will be overridden by docker-compose)
COPY .env* ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x startup.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE $PORT

# Health check - simple and reliable
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Use startup script as entrypoint
CMD ["./startup.sh"]
# ================================
# CivicFix Backend - Production Dockerfile
# Simplified build for better reliability
# ================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="CivicFix Team"
LABEL version="1.0.0"
LABEL description="CivicFix Backend API Server"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    FLASK_ENV=production \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Create directories and set permissions
RUN mkdir -p logs temp uploads && \
    chown -R appuser:appgroup /app && \
    chmod +x docker-entrypoint.sh && \
    chmod -R 777 logs temp uploads

# Switch to non-root user
USER appuser

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Entrypoint and command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:application"]
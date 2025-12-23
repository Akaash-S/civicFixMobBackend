# ================================
# CivicFix Backend - Production Dockerfile
# ================================

# Use Python 3.11 slim image for optimal size and security
FROM python:3.11-slim

# Metadata
LABEL maintainer="CivicFix Team"
LABEL version="1.0.0"
LABEL description="CivicFix Backend API Server"

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_ENV=production \
    PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies
    gcc \
    g++ \
    make \
    # PostgreSQL client library
    libpq-dev \
    # SSL/TLS support
    ca-certificates \
    # Health check utilities
    curl \
    # Process management
    procps \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create application user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    # Clean up pip cache
    pip cache purge

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p logs temp uploads && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app && \
    chmod -R 777 logs temp uploads

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE $PORT

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Set up entrypoint script
COPY --chown=appuser:appgroup docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Use entrypoint for initialization
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:application"]
# CivicFix Backend - Supabase Authentication + AWS Infrastructure Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-clean.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and utilities
COPY app.py .
COPY validate_aws_setup.py .
COPY migrate_database.py .

# Copy environment files (optional - can be overridden by docker-compose)
COPY .env* ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE $PORT

# Health check with longer timeout for AWS services
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Startup script that validates AWS setup before starting the app
COPY --chown=appuser:appuser startup.sh .
RUN chmod +x startup.sh

# Run the application with validation
CMD ["./startup.sh"]
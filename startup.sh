#!/bin/bash
# CivicFix Backend - Production Startup Script
# Robust startup with proper error handling and logging

set -e

echo "🚀 CivicFix Backend - Production Startup"
echo "========================================"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Basic environment check
log "🔍 Checking environment..."

# Check Python
if command_exists python; then
    log "✅ Python: $(python --version)"
else
    log "❌ Python not found"
    exit 1
fi

# Check required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL" "SUPABASE_JWT_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    else
        log "✅ $var is set"
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    log "❌ Missing required environment variables: ${missing_vars[*]}"
    if [ "$SKIP_VALIDATION" != "true" ]; then
        exit 1
    else
        log "⚠️ Continuing despite missing variables (SKIP_VALIDATION=true)"
    fi
fi

# Optional validation
if [ "$SKIP_VALIDATION" = "false" ]; then
    log "🔍 Running comprehensive validation..."
    if [ -f "validate_aws_setup.py" ]; then
        python validate_aws_setup.py
        if [ $? -eq 0 ]; then
            log "✅ Validation passed!"
        else
            log "❌ Validation failed!"
            exit 1
        fi
    else
        log "⚠️ Validation script not found"
    fi
else
    log "⚠️ Skipping validation (SKIP_VALIDATION=${SKIP_VALIDATION:-true})"
fi

# Optional database migration
if [ "$RUN_MIGRATION" = "true" ]; then
    log "🔄 Running database migration..."
    if [ -f "migrate_database.py" ]; then
        python migrate_database.py || log "⚠️ Migration failed or not needed"
    else
        log "⚠️ Migration script not found"
    fi
else
    log "⚠️ Skipping migration (RUN_MIGRATION=${RUN_MIGRATION:-false})"
fi

# Test basic imports
log "🧪 Testing basic imports..."
python -c "
import flask
import psycopg2
import boto3
import jwt
print('✅ All basic imports successful')
" || {
    log "❌ Basic import test failed"
    if [ "$SKIP_VALIDATION" != "true" ]; then
        exit 1
    fi
}

# Start the application
log "🎯 Starting CivicFix Backend..."
log "   Port: ${PORT:-5000}"
log "   Environment: ${FLASK_ENV:-production}"
log "   Skip Validation: ${SKIP_VALIDATION:-true}"

# Use exec to replace the shell process
exec python app.py
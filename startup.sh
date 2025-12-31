#!/bin/bash
# CivicFix Backend - Simplified Startup Script for Docker
# Skips validation by default in containerized environment

set -e

echo "🚀 CivicFix Backend - Starting..."

# Skip validation in Docker by default (can be overridden with SKIP_VALIDATION=false)
if [ "$SKIP_VALIDATION" = "false" ]; then
    echo "🔍 Running validation (SKIP_VALIDATION=false)..."
    python validate_aws_setup.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Validation failed."
        exit 1
    fi
    
    echo "✅ Validation passed!"
else
    echo "⚠️ Skipping validation (default for Docker deployment)"
fi

# Run database migration if needed
if [ "$RUN_MIGRATION" = "true" ]; then
    echo "🔄 Running database migration..."
    python migrate_database.py || echo "⚠️ Migration failed or not needed"
fi

# Start the application
echo "🎯 Starting CivicFix Backend..."
exec python app.py
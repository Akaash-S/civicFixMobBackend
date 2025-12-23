#!/bin/bash
# CivicFix Backend - Docker Startup Script
# Validates AWS setup before starting the application

set -e

echo "🚀 CivicFix Backend - Starting with AWS validation..."

# Run AWS validation (optional - can be skipped with SKIP_VALIDATION=true)
if [ "$SKIP_VALIDATION" != "true" ]; then
    echo "🔍 Validating AWS setup..."
    python validate_aws_setup.py
    
    if [ $? -ne 0 ]; then
        echo "❌ AWS validation failed. Set SKIP_VALIDATION=true to bypass."
        exit 1
    fi
    
    echo "✅ AWS validation passed!"
else
    echo "⚠️ Skipping AWS validation (SKIP_VALIDATION=true)"
fi

# Run database migration if needed
if [ "$RUN_MIGRATION" = "true" ]; then
    echo "🔄 Running database migration..."
    python migrate_database.py || echo "⚠️ Migration failed or not needed"
fi

# Start the application
echo "🎯 Starting CivicFix Backend..."
exec python app.py
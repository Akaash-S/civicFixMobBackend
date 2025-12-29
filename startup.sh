#!/bin/bash
# CivicFix Backend - Perfect Authentication System Startup Script
# Validates Supabase + AWS setup and authentication system before starting

set -e

echo "🚀 CivicFix Backend - Starting with Perfect Authentication System..."

# Run comprehensive validation (optional - can be skipped with SKIP_VALIDATION=true)
if [ "$SKIP_VALIDATION" != "true" ]; then
    echo "🔍 Validating Supabase + AWS setup..."
    python validate_aws_setup.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Supabase + AWS validation failed. Set SKIP_VALIDATION=true to bypass."
        exit 1
    fi
    
    echo "✅ Supabase + AWS validation passed!"
else
    echo "⚠️ Skipping Supabase + AWS validation (SKIP_VALIDATION=true)"
fi

# Run database migration if needed
if [ "$RUN_MIGRATION" = "true" ]; then
    echo "🔄 Running database migration..."
    python migrate_database.py || echo "⚠️ Migration failed or not needed"
fi

# Validate authentication system after app starts (background process)
if [ "$SKIP_AUTH_TEST" != "true" ]; then
    echo "🔐 Authentication validation will run after startup..."
    (
        sleep 30  # Wait for app to fully start
        echo "🧪 Running authentication system validation..."
        python test_auth_quick.py || echo "⚠️ Authentication test failed - check logs"
    ) &
else
    echo "⚠️ Skipping authentication validation (SKIP_AUTH_TEST=true)"
fi

# Start the application
echo "🎯 Starting CivicFix Backend with Perfect Authentication..."
exec python app.py
#!/usr/bin/env bash
# CivicFix Backend - Render Build Script

set -o errexit  # Exit on error

echo "🚀 Starting CivicFix Backend Build Process"
echo "=========================================="

# Upgrade pip and build tools
echo "🔧 Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

# Install system dependencies that might be needed
echo "📦 Installing Python dependencies..."

# Install dependencies with better error handling
pip install --no-cache-dir -r requirements.txt

# Verify critical imports work
echo "✅ Verifying critical dependencies..."
python -c "
try:
    import flask
    import sqlalchemy
    import gunicorn
    print('✅ Core dependencies verified')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "✅ Build completed successfully!"
echo "🌐 Ready to start the application..."
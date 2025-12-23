#!/usr/bin/env bash
# CivicFix Backend - Render Build Script with Fallback

set -o errexit  # Exit on error

echo "🚀 Starting CivicFix Backend Build Process (with fallback)"
echo "========================================================"

# Upgrade pip and build tools
echo "🔧 Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

# Try main requirements first
echo "📦 Attempting to install full requirements..."
if pip install --no-cache-dir -r requirements.txt; then
    echo "✅ Full requirements installed successfully!"
else
    echo "⚠️ Full requirements failed, trying minimal requirements..."
    
    if pip install --no-cache-dir -r requirements-minimal.txt; then
        echo "✅ Minimal requirements installed successfully!"
        echo "⚠️ Some features may be limited (no image processing, Firebase, AWS)"
    else
        echo "❌ Even minimal requirements failed!"
        exit 1
    fi
fi

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
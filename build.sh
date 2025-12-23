#!/usr/bin/env bash
# CivicFix Backend - Render Build Script

set -o errexit  # Exit on error

echo "🚀 Starting CivicFix Backend Build Process"
echo "=========================================="

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completed successfully!"
echo "🌐 Ready to start the application..."
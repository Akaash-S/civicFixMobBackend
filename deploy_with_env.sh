#!/bin/bash

# CivicFix Backend Deployment Script with Environment Variables
# This script helps deploy the backend with proper environment configuration

echo "🚀 CivicFix Backend Deployment Script"
echo "======================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your configuration"
    exit 1
fi

echo "✅ .env file found"

# Load environment variables from .env
export $(cat .env | grep -v '^#' | xargs)

# Check critical environment variables
echo "🔍 Checking environment variables..."

if [ -z "$SUPABASE_JWT_SECRET" ]; then
    echo "❌ SUPABASE_JWT_SECRET not found in .env"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found in .env"
    exit 1
fi

echo "✅ Critical environment variables found"
echo "   SUPABASE_JWT_SECRET: ${SUPABASE_JWT_SECRET:0:20}..."
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-clean.txt

# Run the application with environment variables
echo "🚀 Starting CivicFix Backend..."
echo "   Make sure to set these environment variables on your server:"
echo "   SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET"
echo ""

# Start the application
python app.py
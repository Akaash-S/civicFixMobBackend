#!/bin/bash

# Deploy Authentication Fix to EC2
# This script updates the backend with the JWT algorithm fix

echo "🚀 Deploying Authentication Fix to EC2"
echo "======================================"

# Server details
SERVER_IP="3.110.42.224"
SERVER_USER="ubuntu"
PROJECT_DIR="/home/ubuntu/civicFix"

echo "📋 Deployment Steps:"
echo "1. Copy updated app.py to server"
echo "2. Ensure SUPABASE_JWT_SECRET is in server .env"
echo "3. Restart the backend service"
echo ""

# Step 1: Copy updated app.py
echo "📁 Copying updated app.py..."
scp app.py ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}/backend/

# Step 2: Ensure environment variable is set
echo "🔧 Checking server environment..."
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /home/ubuntu/civicFix/backend

# Check if SUPABASE_JWT_SECRET exists in .env
if grep -q "SUPABASE_JWT_SECRET" .env; then
    echo "✅ SUPABASE_JWT_SECRET found in .env"
    grep "SUPABASE_JWT_SECRET" .env
else
    echo "❌ SUPABASE_JWT_SECRET not found in .env"
    echo "Adding SUPABASE_JWT_SECRET to .env..."
    echo "SUPABASE_JWT_SECRET=sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE" >> .env
    echo "✅ Added SUPABASE_JWT_SECRET to .env"
fi

# Show current .env content (masked)
echo ""
echo "📄 Current .env file (masked):"
cat .env | sed 's/=.*/=***MASKED***/'
EOF

# Step 3: Restart backend service
echo ""
echo "🔄 Restarting backend service..."
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd /home/ubuntu/civicFix/backend

# Stop existing containers
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Wait a moment for startup
sleep 10

# Check status
docker-compose ps
docker-compose logs --tail=20
EOF

echo ""
echo "✅ Deployment complete!"
echo "🧪 Test the authentication with:"
echo "   python test_server_jwt_secret.py"
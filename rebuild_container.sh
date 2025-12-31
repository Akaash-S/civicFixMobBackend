#!/bin/bash

echo "========================================"
echo "CivicFix Backend - Container Rebuild"
echo "========================================"
echo
echo "Fixing bcrypt error by rebuilding container..."
echo

echo "Step 1: Stopping current container..."
docker-compose down

echo
echo "Step 2: Rebuilding container with no cache..."
docker-compose build --no-cache backend

echo
echo "Step 3: Starting new container..."
docker-compose up -d backend

echo
echo "Step 4: Waiting for startup..."
sleep 30

echo
echo "Step 5: Testing health endpoint..."
curl -f http://localhost:5000/health

echo
echo "Step 6: Checking container status..."
docker-compose ps

echo
echo "Step 7: Checking recent logs..."
docker-compose logs --tail=10 backend

echo
echo "========================================"
echo "Container rebuild complete!"
echo "========================================"
echo
echo "The bcrypt error should now be fixed."
echo "Test the mobile app onboarding flow."
echo
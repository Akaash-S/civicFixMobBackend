#!/bin/bash

# CivicFix Backend - Resilient Docker Deployment
# This script deploys the backend with graceful service failures

set -e

echo "🚀 CivicFix Backend - Resilient Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    log_warn ".env.production not found, creating from template..."
    cp .env.example .env.production
    
    # Set production environment
    sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env.production
    
    log_warn "Please edit .env.production with your actual credentials"
    log_info "Firebase credentials should be set as FIREBASE_SERVICE_ACCOUNT_JSON in .env.production"
fi

# Stop existing containers
log_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Clean up
log_info "Cleaning up Docker resources..."
docker system prune -f

# Create logs directory
mkdir -p logs
chmod 777 logs

# Build and start services
log_info "Building and starting services..."

# Start backend application
log_info "Starting backend application..."
docker-compose up -d civicfix-backend

# Wait for backend to start
log_info "Waiting for backend to initialize..."
sleep 10

# Check backend health
log_info "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        log_info "✅ Backend is healthy!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "Backend health check failed after 30 attempts"
        log_info "Checking logs..."
        docker-compose logs --tail=20 civicfix-backend
        exit 1
    fi
    
    log_info "Waiting for backend... ($i/30)"
    sleep 2
done

# Start Nginx
log_info "Starting Nginx reverse proxy..."
docker-compose up -d nginx || {
    log_warn "Nginx failed to start - backend still accessible on port 5000"
}

# Show final status
log_info "Deployment Status:"
echo "==================="

# Show running containers
docker-compose ps

echo ""

# Test endpoints
log_info "Testing endpoints..."
echo "Health Check:"
curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "Health check failed"

echo ""
echo "Service URLs:"
echo "  - Backend: http://localhost:5000"
echo "  - Health:  http://localhost:5000/health"
echo "  - Nginx:   http://localhost (if running)"

# Show service status
echo ""
log_info "Service Status Summary:"
backend_status=$(docker inspect civicfix-backend-prod --format='{{.State.Status}}' 2>/dev/null || echo "not found")
nginx_status=$(docker inspect civicfix-nginx --format='{{.State.Status}}' 2>/dev/null || echo "not found")

echo "  Backend: $backend_status"
echo "  Nginx:   $nginx_status"

if [ "$backend_status" = "running" ]; then
    log_info "🎉 Deployment completed successfully!"
    log_info "Backend is running and ready to accept requests"
else
    log_error "❌ Backend deployment failed"
    log_info "Check logs with: docker-compose logs civicfix-backend"
    exit 1
fi
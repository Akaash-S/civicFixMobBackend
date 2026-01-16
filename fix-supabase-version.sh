#!/bin/bash

# Fix Supabase Version Compatibility Issue
# This script rebuilds the Docker container with correct package versions

set -e

echo "🔧 Fixing Supabase Version Compatibility"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found!"
    exit 1
fi

print_info "Stopping current containers..."
docker-compose down

print_success "Containers stopped"
echo ""

print_info "Removing old images to force rebuild..."
docker-compose rm -f backend
docker rmi civicfix-backend 2>/dev/null || true

print_success "Old images removed"
echo ""

print_info "Rebuilding with correct package versions..."
print_info "This will install:"
print_info "  - supabase==2.3.0"
print_info "  - storage3==0.7.0"
print_info "  - httpx==0.24.1"
print_info "  - gotrue==1.3.0"
print_info "  - postgrest==0.13.2"
print_info "  - realtime==1.0.5"
echo ""

docker-compose build --no-cache backend

print_success "Rebuild completed"
echo ""

print_info "Starting services..."
docker-compose up -d

print_success "Services started"
echo ""

print_info "Waiting for services to be ready..."
sleep 10

# Check health
print_info "Checking health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Backend is healthy!"
    echo ""
    print_info "Health check response:"
    curl -s http://localhost/health | python3 -m json.tool
else
    print_warning "Backend health check failed"
    print_info "Checking logs..."
    docker-compose logs --tail=50 backend
fi

echo ""
print_success "Fix completed!"
print_info "View logs: docker-compose logs -f backend"

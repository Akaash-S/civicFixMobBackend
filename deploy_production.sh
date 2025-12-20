#!/bin/bash

# CivicFix Backend Production Deployment Script
# This script handles the complete production deployment process

set -e  # Exit on any error

echo "=========================================="
echo "CivicFix Backend - Production Deployment"
echo "=========================================="

# Configuration
APP_NAME="civicfix-backend"
DOCKER_IMAGE="civicfix/backend"
DOCKER_TAG="latest"
CONTAINER_NAME="civicfix-backend-prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if production environment file exists
    if [ ! -f ".env.production" ]; then
        log_error "Production environment file (.env.production) not found."
        log_info "Please create .env.production with production settings."
        exit 1
    fi
    
    # Check if service account file exists
    if [ ! -f "service-account.json" ]; then
        log_error "Firebase service account file (service-account.json) not found."
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
    
    if [ $? -eq 0 ]; then
        log_info "Docker image built successfully ✓"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Stop existing container
stop_existing() {
    log_info "Stopping existing container..."
    
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        docker stop ${CONTAINER_NAME}
        docker rm ${CONTAINER_NAME}
        log_info "Existing container stopped and removed ✓"
    else
        log_info "No existing container found"
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    docker run --rm \
        --env-file .env.production \
        ${DOCKER_IMAGE}:${DOCKER_TAG} \
        python -c "
from app import create_app
from app.config import config
from app.extensions import db
app, _ = create_app(config['production'])
with app.app_context():
    db.create_all()
    print('Database migrations completed')
"
    
    if [ $? -eq 0 ]; then
        log_info "Database migrations completed ✓"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Start production container
start_container() {
    log_info "Starting production container..."
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        --env-file .env.production \
        -p 5000:5000 \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:5000/health || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        ${DOCKER_IMAGE}:${DOCKER_TAG}
    
    if [ $? -eq 0 ]; then
        log_info "Production container started successfully ✓"
        log_info "Container ID: $(docker ps -q -f name=${CONTAINER_NAME})"
    else
        log_error "Failed to start production container"
        exit 1
    fi
}

# Wait for health check
wait_for_health() {
    log_info "Waiting for application to be healthy..."
    
    for i in {1..30}; do
        if docker exec ${CONTAINER_NAME} curl -f http://localhost:5000/health > /dev/null 2>&1; then
            log_info "Application is healthy ✓"
            return 0
        fi
        
        log_info "Waiting for health check... ($i/30)"
        sleep 2
    done
    
    log_error "Application failed to become healthy"
    docker logs ${CONTAINER_NAME}
    exit 1
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo "===================="
    
    # Container status
    echo "Container Status:"
    docker ps -f name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    
    # Health check
    echo "Health Check:"
    curl -s http://localhost:5000/health | python -m json.tool || echo "Health check failed"
    
    echo ""
    
    # Logs (last 10 lines)
    echo "Recent Logs:"
    docker logs --tail 10 ${CONTAINER_NAME}
}

# Cleanup function
cleanup() {
    log_warn "Deployment interrupted. Cleaning up..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Main deployment process
main() {
    log_info "Starting production deployment process..."
    
    check_prerequisites
    build_image
    stop_existing
    run_migrations
    start_container
    wait_for_health
    show_status
    
    log_info "🎉 Production deployment completed successfully!"
    log_info "Application is running at: http://localhost:5000"
    log_info "Health check: http://localhost:5000/health"
    
    # Remove trap since deployment succeeded
    trap - EXIT
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping production container..."
        docker stop ${CONTAINER_NAME}
        docker rm ${CONTAINER_NAME}
        log_info "Production container stopped ✓"
        ;;
    "logs")
        log_info "Showing container logs..."
        docker logs -f ${CONTAINER_NAME}
        ;;
    "status")
        show_status
        ;;
    "restart")
        log_info "Restarting production container..."
        docker restart ${CONTAINER_NAME}
        wait_for_health
        log_info "Production container restarted ✓"
        ;;
    *)
        echo "Usage: $0 {deploy|stop|logs|status|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  stop     - Stop the production container"
        echo "  logs     - Show container logs"
        echo "  status   - Show deployment status"
        echo "  restart  - Restart the production container"
        exit 1
        ;;
esac
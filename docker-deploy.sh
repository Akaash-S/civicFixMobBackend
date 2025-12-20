#!/bin/bash

# CivicFix Backend - Docker Deployment Script for EC2
# This script handles Docker-based deployment on AWS EC2

set -e  # Exit on any error

echo "=========================================="
echo "CivicFix Backend - Docker Deployment"
echo "=========================================="

# Configuration
APP_NAME="civicfix-backend"
DOCKER_IMAGE="civicfix/backend"
DOCKER_TAG="latest"
CONTAINER_NAME="civicfix-backend-prod"
NETWORK_NAME="civicfix-network"

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

# Setup directories and permissions
setup_directories() {
    log_info "Setting up directories and permissions..."
    
    # Create local logs directory
    mkdir -p logs
    chmod 777 logs
    
    # Create system logs directory
    sudo mkdir -p /var/log/civicfix
    sudo chmod 777 /var/log/civicfix
    
    # Set proper permissions for service account file
    if [ -f "service-account.json" ]; then
        chmod 644 service-account.json
    fi
    
    # Set proper permissions for environment file
    if [ -f ".env.production" ]; then
        chmod 600 .env.production
    fi
    
    log_info "Directories and permissions set up ✓"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        log_info "Docker installed. Please log out and back in, then run this script again."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Starting Docker..."
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    
    # Create logs directory with proper permissions
    log_info "Setting up logs directory..."
    mkdir -p logs
    chmod 777 logs
    
    # Check if production environment file exists
    if [ ! -f ".env.production" ]; then
        log_error "Production environment file (.env.production) not found."
        log_info "Creating from template..."
        cp .env.example .env.production
        log_warn "Please edit .env.production with your production settings before continuing."
        log_warn "IMPORTANT: Never commit .env.production to version control!"
        exit 1
    fi
    
    # Check if service account file exists
    if [ ! -f "service-account.json" ]; then
        log_error "Firebase service account file (service-account.json) not found."
        log_info "Please add your Firebase service account JSON file."
        log_warn "IMPORTANT: Never commit service-account.json to version control!"
        exit 1
    fi
    
    # Validate that .env.production doesn't contain placeholder values
    if grep -q "your-" .env.production; then
        log_error "Production environment file contains placeholder values."
        log_info "Please replace all 'your-*' placeholders with actual values in .env.production"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Create Docker network
create_network() {
    log_info "Creating Docker network..."
    
    if ! docker network ls | grep -q ${NETWORK_NAME}; then
        docker network create ${NETWORK_NAME}
        log_info "Docker network '${NETWORK_NAME}' created ✓"
    else
        log_info "Docker network '${NETWORK_NAME}' already exists ✓"
    fi
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    # Clean up any existing containers and images
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} 2>/dev/null || true
    
    # Build with build args for production
    docker build \
        --no-cache \
        --build-arg FLASK_ENV=production \
        --build-arg PORT=5000 \
        -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
        .
    
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
        --network ${NETWORK_NAME} \
        ${DOCKER_IMAGE}:${DOCKER_TAG} \
        python -c "
from app import create_app
from app.config import config
from app.extensions import db
import os
os.environ['FLASK_ENV'] = 'production'
app, _ = create_app(config['production'])
with app.app_context():
    db.create_all()
    print('Database migrations completed')
"
    
    if [ $? -eq 0 ]; then
        log_info "Database migrations completed ✓"
    else
        log_warn "Database migrations failed (may be normal if DB is not accessible from container)"
    fi
}

# Start production container
start_container() {
    log_info "Starting production container..."
    
    # Ensure logs directory exists with proper permissions
    mkdir -p logs
    chmod 777 logs
    
    # Create host logs directory for volume mounting
    sudo mkdir -p /var/log/civicfix
    sudo chmod 777 /var/log/civicfix
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        --env-file .env.production \
        --network ${NETWORK_NAME} \
        -p 5000:5000 \
        --restart unless-stopped \
        --memory="512m" \
        --cpus="1.0" \
        --health-cmd="curl -f http://localhost:5000/health || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        --health-start-period=40s \
        -v /var/log/civicfix:/app/logs:rw \
        -v $(pwd)/service-account.json:/app/service-account.json:ro \
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
    log_info "Container logs:"
    docker logs ${CONTAINER_NAME}
    exit 1
}

# Setup reverse proxy (Nginx)
setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."
    
    # Create Nginx configuration
    sudo mkdir -p /etc/nginx/sites-available
    sudo mkdir -p /etc/nginx/sites-enabled
    
    cat > /tmp/civicfix-nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Proxy to backend
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:5000/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /var/www/civicfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    sudo mv /tmp/civicfix-nginx.conf /etc/nginx/sites-available/civicfix
    sudo ln -sf /etc/nginx/sites-available/civicfix /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Install and start Nginx if not already installed
    if ! command -v nginx &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y nginx
    fi
    
    # Test and reload Nginx
    sudo nginx -t && sudo systemctl reload nginx
    sudo systemctl enable nginx
    
    log_info "Nginx reverse proxy configured ✓"
}

# Setup systemd service for container management
setup_systemd() {
    log_info "Setting up systemd service..."
    
    cat > /tmp/civicfix-backend.service << EOF
[Unit]
Description=CivicFix Backend Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start ${CONTAINER_NAME}
ExecStop=/usr/bin/docker stop ${CONTAINER_NAME}
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/civicfix-backend.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable civicfix-backend.service
    
    log_info "Systemd service configured ✓"
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
    curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "Health check failed"
    
    echo ""
    
    # Resource usage
    echo "Resource Usage:"
    docker stats ${CONTAINER_NAME} --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    
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
    log_info "Starting Docker deployment process..."
    
    setup_directories
    check_prerequisites
    create_network
    build_image
    stop_existing
    run_migrations
    start_container
    wait_for_health
    setup_nginx
    setup_systemd
    show_status
    
    log_info "🎉 Docker deployment completed successfully!"
    log_info "Application is running at:"
    log_info "  - Local: http://localhost:5000"
    log_info "  - Public: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-ec2-ip')"
    log_info "Health check: http://localhost/health"
    log_info "Logs: /var/log/civicfix/ and docker logs ${CONTAINER_NAME}"
    
    # Remove trap since deployment succeeded
    trap - EXIT
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping Docker container..."
        docker stop ${CONTAINER_NAME}
        sudo systemctl stop civicfix-backend
        log_info "Container stopped ✓"
        ;;
    "start")
        log_info "Starting Docker container..."
        docker start ${CONTAINER_NAME}
        sudo systemctl start civicfix-backend
        log_info "Container started ✓"
        ;;
    "restart")
        log_info "Restarting Docker container..."
        docker restart ${CONTAINER_NAME}
        wait_for_health
        log_info "Container restarted ✓"
        ;;
    "logs")
        log_info "Showing container logs..."
        echo "=== Container Logs ==="
        docker logs -f ${CONTAINER_NAME}
        echo ""
        echo "=== File Logs (if available) ==="
        if [ -d "/var/log/civicfix" ]; then
            tail -f /var/log/civicfix/*.log 2>/dev/null || echo "No file logs available"
        else
            echo "File logs directory not found"
        fi
        ;;
    "status")
        show_status
        ;;
    "update")
        log_info "Updating application..."
        build_image
        stop_existing
        start_container
        wait_for_health
        log_info "Application updated ✓"
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|logs|status|update}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  start    - Start the container"
        echo "  stop     - Stop the container"
        echo "  restart  - Restart the container"
        echo "  logs     - Show container logs"
        echo "  status   - Show deployment status"
        echo "  update   - Update and redeploy"
        exit 1
        ;;
esac
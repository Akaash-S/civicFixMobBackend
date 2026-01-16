#!/bin/bash

# CivicFix Backend Deployment Script for Google Compute Engine
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 CivicFix Backend Deployment"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file with required configuration"
    print_info "You can copy .env.example and update the values"
    exit 1
fi

print_success ".env file found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    print_info "Please install Docker first:"
    print_info "  curl -fsSL https://get.docker.com -o get-docker.sh"
    print_info "  sudo sh get-docker.sh"
    exit 1
fi

print_success "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    print_info "Please install Docker Compose first:"
    print_info "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    print_info "  sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

print_success "Docker Compose is installed"
echo ""

# Ask for deployment action
echo "Select deployment action:"
echo "1) Fresh deployment (build and start)"
echo "2) Update deployment (rebuild and restart)"
echo "3) Restart services"
echo "4) Stop services"
echo "5) View logs"
echo "6) Check status"
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        print_info "Starting fresh deployment..."
        echo ""
        
        # Stop any existing containers
        print_info "Stopping existing containers..."
        docker-compose down 2>/dev/null || true
        
        # Build images
        print_info "Building Docker images..."
        docker-compose build
        print_success "Images built successfully"
        
        # Start services
        print_info "Starting services..."
        docker-compose up -d
        print_success "Services started"
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 10
        
        # Check health
        print_info "Checking health..."
        if curl -f http://localhost/health > /dev/null 2>&1; then
            print_success "Backend is healthy!"
        else
            print_warning "Backend health check failed. Check logs with: docker-compose logs -f"
        fi
        
        echo ""
        print_success "Deployment completed!"
        print_info "View logs: docker-compose logs -f"
        print_info "Check status: docker-compose ps"
        ;;
        
    2)
        print_info "Updating deployment..."
        echo ""
        
        # Pull latest changes if using git
        if [ -d .git ]; then
            print_info "Pulling latest changes..."
            git pull
        fi
        
        # Stop services
        print_info "Stopping services..."
        docker-compose down
        
        # Rebuild images
        print_info "Rebuilding Docker images..."
        docker-compose build
        print_success "Images rebuilt successfully"
        
        # Start services
        print_info "Starting services..."
        docker-compose up -d
        print_success "Services started"
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 10
        
        # Check health
        print_info "Checking health..."
        if curl -f http://localhost/health > /dev/null 2>&1; then
            print_success "Backend is healthy!"
        else
            print_warning "Backend health check failed. Check logs with: docker-compose logs -f"
        fi
        
        echo ""
        print_success "Update completed!"
        ;;
        
    3)
        print_info "Restarting services..."
        docker-compose restart
        print_success "Services restarted"
        
        # Wait and check health
        sleep 5
        if curl -f http://localhost/health > /dev/null 2>&1; then
            print_success "Backend is healthy!"
        else
            print_warning "Backend health check failed. Check logs with: docker-compose logs -f"
        fi
        ;;
        
    4)
        print_info "Stopping services..."
        docker-compose down
        print_success "Services stopped"
        ;;
        
    5)
        print_info "Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
        
    6)
        print_info "Checking status..."
        echo ""
        docker-compose ps
        echo ""
        
        # Check health
        if curl -f http://localhost/health > /dev/null 2>&1; then
            print_success "Backend is healthy!"
            echo ""
            print_info "Health check response:"
            curl -s http://localhost/health | python3 -m json.tool
        else
            print_error "Backend is not responding!"
            print_info "Check logs with: docker-compose logs -f"
        fi
        ;;
        
    *)
        print_error "Invalid choice!"
        exit 1
        ;;
esac

echo ""
print_info "Deployment script completed"

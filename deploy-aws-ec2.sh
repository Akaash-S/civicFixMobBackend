#!/bin/bash
# CivicFix Backend - AWS EC2 Docker Deployment Script

set -e

echo "🚀 CivicFix Backend - AWS EC2 Docker Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on Ubuntu
check_system() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine OS. This script is designed for Ubuntu."
        exit 1
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "This script is designed for Ubuntu. Detected: $ID"
        exit 1
    fi
    
    log_info "✅ Running on Ubuntu $VERSION_ID"
}

# Update system packages
update_system() {
    log_step "Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    log_info "✅ System packages updated"
}

# Install Docker
install_docker() {
    log_step "Installing Docker..."
    
    # Remove old versions
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install dependencies
    sudo apt install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_info "✅ Docker installed successfully"
}

# Install Docker Compose
install_docker_compose() {
    log_step "Installing Docker Compose..."
    
    # Docker Compose is now included with Docker, but let's ensure we have the latest
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink for docker-compose plugin
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_info "✅ Docker Compose installed successfully"
}

# Setup application directory
setup_app_directory() {
    log_step "Setting up application directory..."
    
    APP_DIR="/opt/civicfix"
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    log_info "✅ Application directory created: $APP_DIR"
}

# Setup firewall
setup_firewall() {
    log_step "Configuring firewall..."
    
    # Install UFW if not installed
    sudo apt install -y ufw
    
    # Reset firewall rules
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    sudo ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow application port (for direct access)
    sudo ufw allow 5000/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    log_info "✅ Firewall configured"
}

# Create environment file
create_env_file() {
    log_step "Creating environment file..."
    
    if [[ ! -f .env ]]; then
        cp .env-clean .env
        log_warn "⚠️ Created .env from template. Please update with your actual values:"
        log_warn "   - SECRET_KEY: Generate a secure secret key"
        log_warn "   - DB_PASSWORD: Set a strong database password"
        log_warn "   - FIREBASE_SERVICE_ACCOUNT_B64: Your Base64-encoded Firebase credentials"
        log_warn "   - FIREBASE_PROJECT_ID: Your Firebase project ID"
    else
        log_info "✅ Environment file already exists"
    fi
}

# Deploy application
deploy_application() {
    log_step "Deploying CivicFix Backend..."
    
    # Stop existing containers
    docker-compose -f docker-compose-clean.yml down 2>/dev/null || true
    
    # Remove old images
    docker system prune -f
    
    # Build and start services
    docker-compose -f docker-compose-clean.yml up -d --build
    
    log_info "✅ Application deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_step "Verifying deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Check container status
    log_info "Container Status:"
    docker-compose -f docker-compose-clean.yml ps
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_info "✅ Health check passed"
    else
        log_warn "⚠️ Health check failed - checking direct backend connection..."
        if curl -f http://localhost:5000/health > /dev/null 2>&1; then
            log_info "✅ Backend is running (Nginx may need configuration)"
        else
            log_error "❌ Backend health check failed"
            return 1
        fi
    fi
    
    # Show logs
    log_info "Recent logs:"
    docker-compose -f docker-compose-clean.yml logs --tail=10
}

# Show deployment summary
show_summary() {
    log_step "Deployment Summary"
    echo "=================="
    echo ""
    echo "🎉 CivicFix Backend deployed successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose -f docker-compose-clean.yml ps
    echo ""
    echo "🌐 Access URLs:"
    echo "  - API: http://$(curl -s ifconfig.me)/api/v1/"
    echo "  - Health: http://$(curl -s ifconfig.me)/health"
    echo "  - Direct Backend: http://$(curl -s ifconfig.me):5000/"
    echo ""
    echo "🔧 Management Commands:"
    echo "  - View logs: docker-compose -f docker-compose-clean.yml logs -f"
    echo "  - Restart: docker-compose -f docker-compose-clean.yml restart"
    echo "  - Stop: docker-compose -f docker-compose-clean.yml down"
    echo "  - Update: git pull && docker-compose -f docker-compose-clean.yml up -d --build"
    echo ""
    echo "📁 Application Directory: /opt/civicfix"
    echo "📄 Environment File: .env"
    echo ""
    echo "⚠️ Next Steps:"
    echo "  1. Update .env file with your actual credentials"
    echo "  2. Restart services: docker-compose -f docker-compose-clean.yml restart"
    echo "  3. Test your API endpoints"
    echo "  4. Configure SSL certificate (optional)"
    echo ""
}

# Main deployment function
main() {
    log_info "Starting CivicFix Backend deployment on AWS EC2..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed"
    else
        check_system
        update_system
        install_docker
        install_docker_compose
        
        log_warn "Docker installed. Please log out and log back in, then run this script again."
        log_warn "Or run: newgrp docker"
        exit 0
    fi
    
    # Setup and deploy
    setup_app_directory
    setup_firewall
    create_env_file
    deploy_application
    verify_deployment
    show_summary
    
    log_info "🎉 Deployment completed successfully!"
}

# Handle interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
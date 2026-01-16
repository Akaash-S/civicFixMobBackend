#!/bin/bash

# CivicFix Backend - GCE Instance Setup Script
# This script installs Docker Compose and prepares the instance for deployment

set -e  # Exit on error

echo "🚀 CivicFix Backend - GCE Setup"
echo "================================"
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

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script is designed for Linux systems (GCE instances)"
    exit 1
fi

print_info "Setting up GCE instance for CivicFix backend..."
echo ""

# Step 1: Update system
print_info "Step 1: Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
print_success "System updated"
echo ""

# Step 2: Check if Docker is installed
print_info "Step 2: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    print_success "Docker installed"
    print_warning "You need to log out and back in for docker group changes to take effect"
else
    print_success "Docker is already installed"
fi
echo ""

# Step 3: Install Docker Compose
print_info "Step 3: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    # Get latest version
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    
    print_info "Installing Docker Compose ${DOCKER_COMPOSE_VERSION}..."
    
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Verify installation
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose installed: $(docker-compose --version)"
    else
        print_error "Docker Compose installation failed"
        exit 1
    fi
else
    print_success "Docker Compose is already installed: $(docker-compose --version)"
fi
echo ""

# Step 4: Install additional tools
print_info "Step 4: Installing additional tools..."
sudo apt-get install -y -qq curl wget git nano
print_success "Additional tools installed"
echo ""

# Step 5: Configure firewall (if ufw is available)
print_info "Step 5: Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow 22/tcp  # SSH
    sudo ufw allow 80/tcp  # HTTP
    sudo ufw allow 443/tcp # HTTPS
    print_success "Firewall configured"
else
    print_warning "UFW not available, skipping firewall configuration"
    print_info "Make sure GCE firewall rules allow ports 80 and 443"
fi
echo ""

# Step 6: Create necessary directories
print_info "Step 6: Creating directories..."
mkdir -p ~/backend
mkdir -p /etc/letsencrypt
mkdir -p /var/www/certbot
print_success "Directories created"
echo ""

# Step 7: Set permissions
print_info "Step 7: Setting permissions..."
if [ -f .env ]; then
    chmod 600 .env
    print_success ".env file secured (chmod 600)"
fi
if [ -f deploy.sh ]; then
    chmod +x deploy.sh
    print_success "deploy.sh made executable"
fi
echo ""

# Step 8: Display system information
print_info "Step 8: System information..."
echo "  OS: $(lsb_release -d | cut -f2)"
echo "  Kernel: $(uname -r)"
echo "  Docker: $(docker --version)"
echo "  Docker Compose: $(docker-compose --version)"
echo "  Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $2}')"
echo ""

# Step 9: Check if .env file exists
print_info "Step 9: Checking configuration..."
if [ -f .env ]; then
    print_success ".env file found"
    
    # Check required variables
    required_vars=("SECRET_KEY" "DATABASE_URL" "SUPABASE_URL" "SUPABASE_KEY" "SUPABASE_JWT_SECRET")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required environment variables are set"
    else
        print_warning "Missing environment variables: ${missing_vars[*]}"
        print_info "Please update .env file before deploying"
    fi
else
    print_warning ".env file not found"
    print_info "Please create .env file with required configuration"
    print_info "You can copy .env.example and update the values"
fi
echo ""

# Final summary
echo "================================"
print_success "GCE instance setup completed!"
echo "================================"
echo ""

print_info "Next steps:"
echo "  1. If Docker was just installed, log out and back in:"
echo "     exit"
echo "     gcloud compute ssh your-instance"
echo ""
echo "  2. Configure .env file (if not done):"
echo "     nano .env"
echo ""
echo "  3. Run deployment script:"
echo "     ./deploy.sh"
echo ""
echo "  4. Verify deployment:"
echo "     curl http://localhost/health"
echo ""

# Check if user needs to log out
if groups | grep -q docker; then
    print_success "You're already in the docker group. Ready to deploy!"
else
    print_warning "You need to log out and back in for docker group changes to take effect"
    print_info "After logging back in, run: ./deploy.sh"
fi

echo ""
print_info "Setup script completed"

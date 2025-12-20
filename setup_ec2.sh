#!/bin/bash

# CivicFix Backend - EC2 Initial Setup Script
# This script sets up a fresh EC2 instance for CivicFix deployment

set -e

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

# Check if running as ubuntu user
check_user() {
    if [ "$USER" != "ubuntu" ]; then
        log_error "This script should be run as the ubuntu user"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_step "Updating system packages..."
    
    sudo apt update
    sudo apt upgrade -y
    
    log_info "System packages updated"
}

# Install required packages
install_packages() {
    log_step "Installing required packages..."
    
    # Install Python and development tools
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        curl \
        wget \
        unzip \
        nginx \
        redis-server \
        postgresql-client \
        htop \
        tree \
        vim \
        certbot \
        python3-certbot-nginx
    
    log_info "Required packages installed"
}

# Install Docker (optional)
install_docker() {
    log_step "Installing Docker..."
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add ubuntu user to docker group
    sudo usermod -aG docker ubuntu
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    rm get-docker.sh
    
    log_info "Docker installed successfully"
}

# Setup application directory
setup_app_directory() {
    log_step "Setting up application directory..."
    
    # Create application directory
    sudo mkdir -p /opt/civicfix
    sudo chown ubuntu:ubuntu /opt/civicfix
    
    # Create logs directory
    mkdir -p /opt/civicfix/logs
    mkdir -p /opt/civicfix/backups
    
    log_info "Application directory created: /opt/civicfix"
}

# Configure Redis
configure_redis() {
    log_step "Configuring Redis..."
    
    # Backup original config
    sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # Configure Redis for production
    sudo tee -a /etc/redis/redis.conf > /dev/null <<EOF

# CivicFix Production Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    
    # Start and enable Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    log_info "Redis configured and started"
}

# Setup firewall
setup_firewall() {
    log_step "Configuring firewall..."
    
    # Install and configure UFW
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow application port (for direct access during setup)
    sudo ufw allow 5000/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    log_info "Firewall configured"
}

# Create systemd service template
create_service_template() {
    log_step "Creating systemd service template..."
    
    sudo tee /etc/systemd/system/civicfix-backend.service > /dev/null <<EOF
[Unit]
Description=CivicFix Backend API
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/civicfix
Environment=PATH=/opt/civicfix/venv/bin
EnvironmentFile=/opt/civicfix/.env.production
ExecStart=/opt/civicfix/venv/bin/gunicorn --config gunicorn.conf.py run:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/civicfix/logs

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    
    log_info "Systemd service template created"
}

# Configure Nginx template
configure_nginx() {
    log_step "Configuring Nginx..."
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Create CivicFix site configuration
    sudo tee /etc/nginx/sites-available/civicfix-backend > /dev/null <<'EOF'
# CivicFix Backend Nginx Configuration

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

# Upstream backend
upstream civicfix_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    server_name _;  # Replace with your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logging
    access_log /var/log/nginx/civicfix_access.log;
    error_log /var/log/nginx/civicfix_error.log;

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://civicfix_backend;
        access_log off;
    }

    # Authentication endpoints (stricter rate limiting)
    location /api/v1/auth {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://civicfix_backend;
        include /etc/nginx/proxy_params;
    }

    # API endpoints (standard rate limiting)
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://civicfix_backend;
        include /etc/nginx/proxy_params;
    }

    # Socket.IO endpoints
    location /socket.io/ {
        proxy_pass http://civicfix_backend;
        include /etc/nginx/proxy_params;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # All other requests
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://civicfix_backend;
        include /etc/nginx/proxy_params;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/civicfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Create proxy params
    sudo tee /etc/nginx/proxy_params > /dev/null <<EOF
proxy_set_header Host \$host;
proxy_set_header X-Real-IP \$remote_addr;
proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto \$scheme;
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
proxy_buffering off;
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/civicfix-backend /etc/nginx/sites-enabled/

    # Test Nginx configuration
    sudo nginx -t

    # Start and enable Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx

    log_info "Nginx configured successfully"
}

# Setup log rotation
setup_log_rotation() {
    log_step "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/civicfix-backend > /dev/null <<EOF
/opt/civicfix/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload civicfix-backend > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/civicfix_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_info "Log rotation configured"
}

# Create monitoring scripts
create_monitoring_scripts() {
    log_step "Creating monitoring scripts..."
    
    # Create system monitoring script
    tee /opt/civicfix/monitor_system.sh > /dev/null <<'EOF'
#!/bin/bash

# System monitoring script for CivicFix
echo "=== System Status - $(date) ==="

# System resources
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

# Service status
echo "Backend Service: $(systemctl is-active civicfix-backend)"
echo "Nginx Service: $(systemctl is-active nginx)"
echo "Redis Service: $(systemctl is-active redis-server)"

# Application health
if curl -f -s http://localhost:5000/health > /dev/null; then
    echo "Application Health: ✅ Healthy"
else
    echo "Application Health: ❌ Unhealthy"
fi

echo "================================"
EOF

    chmod +x /opt/civicfix/monitor_system.sh
    
    log_info "Monitoring scripts created"
}

# Setup automatic security updates
setup_auto_updates() {
    log_step "Setting up automatic security updates..."
    
    sudo apt install -y unattended-upgrades
    
    # Configure automatic updates
    sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

    # Enable automatic updates
    sudo systemctl enable unattended-upgrades
    sudo systemctl start unattended-upgrades
    
    log_info "Automatic security updates configured"
}

# Show setup summary
show_summary() {
    log_step "Setup Summary"
    
    echo "=========================================="
    echo "🎉 EC2 Setup Completed Successfully!"
    echo "=========================================="
    echo ""
    echo "📋 What's been configured:"
    echo "  ✅ System packages updated"
    echo "  ✅ Python 3 and development tools installed"
    echo "  ✅ Nginx web server configured"
    echo "  ✅ Redis server installed and configured"
    echo "  ✅ Docker installed (optional)"
    echo "  ✅ Firewall configured (UFW)"
    echo "  ✅ Systemd service template created"
    echo "  ✅ Log rotation configured"
    echo "  ✅ Monitoring scripts created"
    echo "  ✅ Automatic security updates enabled"
    echo ""
    echo "📁 Application directory: /opt/civicfix"
    echo "🔧 Service name: civicfix-backend"
    echo "🌐 Nginx configuration: /etc/nginx/sites-available/civicfix-backend"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Clone your CivicFix repository to /opt/civicfix"
    echo "  2. Configure .env.production file"
    echo "  3. Upload Firebase service account file"
    echo "  4. Run deployment script: ./deploy_ec2.sh"
    echo ""
    echo "📖 Full deployment guide: AWS_EC2_DEPLOYMENT_GUIDE.md"
    echo "=========================================="
}

# Main setup function
main() {
    echo "=========================================="
    echo "🚀 CivicFix Backend - EC2 Setup"
    echo "=========================================="
    echo "Setting up EC2 instance for CivicFix deployment..."
    echo ""
    
    # Check prerequisites
    check_user
    
    # Run setup steps
    update_system
    install_packages
    install_docker
    setup_app_directory
    configure_redis
    setup_firewall
    create_service_template
    configure_nginx
    setup_log_rotation
    create_monitoring_scripts
    setup_auto_updates
    
    # Show summary
    show_summary
    
    log_info "🎉 EC2 setup completed successfully!"
    log_warn "Please reboot the instance to ensure all changes take effect"
}

# Handle interruption
trap 'log_error "Setup interrupted"; exit 1' INT TERM

# Run main function
main "$@"
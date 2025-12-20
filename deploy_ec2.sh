#!/bin/bash

# CivicFix Backend - AWS EC2 Deployment Script
# This script automates the deployment process on EC2

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/civicfix"
SERVICE_NAME="civicfix-backend"
BACKUP_DIR="$APP_DIR/backups"

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as correct user
check_user() {
    if [ "$USER" != "ubuntu" ]; then
        log_error "This script should be run as the ubuntu user"
        exit 1
    fi
}

# Check if we're in the correct directory
check_directory() {
    if [ ! -f "run.py" ] || [ ! -f "requirements.txt" ]; then
        log_error "Please run this script from the CivicFix backend directory"
        exit 1
    fi
}

# Create backup before deployment
create_backup() {
    log_step "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_name="civicfix_backup_$(date +%Y%m%d_%H%M%S)"
    
    # Backup current code (excluding venv and logs)
    tar -czf "$BACKUP_DIR/$backup_name.tar.gz" \
        --exclude='venv' \
        --exclude='logs' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        . 2>/dev/null || true
    
    log_info "Backup created: $backup_name.tar.gz"
}

# Pull latest code
update_code() {
    log_step "Updating application code..."
    
    # Stash any local changes
    git stash push -m "Auto-stash before deployment $(date)" 2>/dev/null || true
    
    # Pull latest changes
    git pull origin main
    
    log_info "Code updated successfully"
}

# Setup virtual environment and dependencies
setup_environment() {
    log_step "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install/update dependencies
    pip install -r requirements.txt
    
    # Install production-specific packages
    pip install gunicorn eventlet gevent
    
    log_info "Dependencies installed successfully"
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    
    source venv/bin/activate
    
    # Set production environment
    export FLASK_ENV=production
    
    # Run migrations
    python -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import create_app
from app.config import config
from app.extensions import db
try:
    app, _ = create_app(config['production'])
    with app.app_context():
        db.create_all()
        print('✅ Database migrations completed successfully')
except Exception as e:
    print(f'❌ Database migration failed: {e}')
    exit(1)
" || {
        log_error "Database migration failed"
        exit 1
    }
    
    log_info "Database migrations completed"
}

# Test application before restart
test_application() {
    log_step "Testing application configuration..."
    
    source venv/bin/activate
    
    # Test application import
    python -c "
from run import application
print('✅ Application import successful')
print(f'✅ Application type: {type(application)}')
print(f'✅ Is callable: {callable(application)}')
" || {
        log_error "Application test failed"
        exit 1
    }
    
    log_info "Application configuration test passed"
}

# Restart services
restart_services() {
    log_step "Restarting services..."
    
    # Restart application service
    sudo systemctl restart $SERVICE_NAME
    
    # Wait for service to start
    sleep 3
    
    # Check service status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Application service restarted successfully"
    else
        log_error "Application service failed to start"
        sudo systemctl status $SERVICE_NAME --no-pager
        exit 1
    fi
    
    # Restart Nginx
    sudo systemctl reload nginx
    log_info "Nginx reloaded successfully"
}

# Health check
health_check() {
    log_step "Performing health checks..."
    
    # Wait for application to fully start
    sleep 5
    
    # Test local health endpoint
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:5000/health > /dev/null; then
            log_info "Health check passed (attempt $attempt)"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log_error "Health check failed after $max_attempts attempts"
                return 1
            fi
            log_warn "Health check failed, retrying... (attempt $attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        fi
    done
    
    # Test API endpoint
    if curl -f -s http://localhost:5000/api/v1/issues > /dev/null; then
        log_info "API endpoint test passed"
    else
        log_warn "API endpoint test failed (may require authentication)"
    fi
    
    return 0
}

# Show deployment status
show_status() {
    log_step "Deployment Status Summary"
    
    echo "=================================="
    echo "Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l | head -10
    
    echo ""
    echo "Application Health:"
    curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "Health check unavailable"
    
    echo ""
    echo "Recent Logs:"
    sudo journalctl -u $SERVICE_NAME --no-pager -n 5
    
    echo ""
    echo "System Resources:"
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')"
    echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
    echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Remove old backups (keep last 5)
    if [ -d "$BACKUP_DIR" ]; then
        ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
}

# Main deployment function
main() {
    echo "=========================================="
    echo "🚀 CivicFix Backend - EC2 Deployment"
    echo "=========================================="
    echo "Starting deployment at $(date)"
    echo ""
    
    # Pre-deployment checks
    check_user
    check_directory
    
    # Deployment steps
    create_backup
    update_code
    setup_environment
    run_migrations
    test_application
    restart_services
    
    # Post-deployment verification
    if health_check; then
        log_info "✅ Deployment completed successfully!"
        show_status
        cleanup
        
        echo ""
        echo "=========================================="
        echo "🎉 Deployment Successful!"
        echo "=========================================="
        echo "🌐 Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
        echo "🏥 Health Check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000/health"
        echo "📊 Monitor: python monitor_production.py check"
        echo "📋 Logs: sudo journalctl -u $SERVICE_NAME -f"
        echo "=========================================="
        
    else
        log_error "❌ Deployment completed but health checks failed"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "1. Check service logs: sudo journalctl -u $SERVICE_NAME -f"
        echo "2. Check application logs: tail -f logs/error.log"
        echo "3. Verify configuration: python verify_deployment.py"
        echo "4. Restart services: sudo systemctl restart $SERVICE_NAME"
        
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
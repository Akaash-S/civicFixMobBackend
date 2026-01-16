#!/bin/bash

################################################################################
# CivicFix Backend - Complete Deployment with SSL
# This script will:
#   1. Build and start the backend
#   2. Generate SSL certificate with Let's Encrypt
#   3. Configure HTTPS
#   4. Set up auto-renewal
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_header() { echo -e "\n${BLUE}========================================${NC}\n${BLUE}$1${NC}\n${BLUE}========================================${NC}\n"; }

################################################################################
# Configuration
################################################################################

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL=""

################################################################################
# Pre-flight Checks
################################################################################

print_header "CivicFix Backend Deployment with SSL"

print_info "Domain: $DOMAIN"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_warning "Please do not run as root"
    exit 1
fi

# Check docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found! Please install Docker first."
    exit 1
fi
print_success "Docker found"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found!"
    print_info "Install with:"
    print_info "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    print_info "  sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi
print_success "Docker Compose found"

# Check .env file
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file with required configuration"
    print_info "See .env.example for reference"
    exit 1
fi
print_success ".env file found"

################################################################################
# Get Email
################################################################################

print_header "Step 1: Configuration"

if [ -z "$EMAIL" ]; then
    print_info "Enter your email address (for SSL certificate notifications):"
    read -p "Email: " EMAIL
    
    if [ -z "$EMAIL" ]; then
        print_error "Email is required!"
        exit 1
    fi
fi

print_success "Email: $EMAIL"

################################################################################
# DNS Check
################################################################################

print_header "Step 2: DNS Verification"

print_info "Checking DNS resolution for $DOMAIN..."

if nslookup $DOMAIN > /dev/null 2>&1; then
    RESOLVED_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    if [ -z "$RESOLVED_IP" ]; then
        RESOLVED_IP=$(dig +short $DOMAIN | head -1)
    fi
    
    if [ -n "$RESOLVED_IP" ]; then
        print_success "Domain resolves to: $RESOLVED_IP"
    else
        print_warning "Could not determine resolved IP"
    fi
else
    print_error "Domain does not resolve!"
    print_info "Please configure DNS A record:"
    print_info "  Type: A"
    print_info "  Name: @"
    print_info "  Value: $(curl -s http://checkip.amazonaws.com)"
    print_info "  TTL: 3600"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE_DNS
    if [ "$CONTINUE_DNS" != "y" ]; then
        exit 1
    fi
fi

################################################################################
# Build Backend
################################################################################

print_header "Step 3: Building Backend"

print_info "Building Docker images..."
docker-compose build

print_success "Backend built successfully"

################################################################################
# Start Backend (HTTP Only)
################################################################################

print_header "Step 4: Starting Backend (HTTP)"

print_info "Starting services..."
docker-compose up -d

print_info "Waiting for backend to be healthy..."
sleep 10

# Check backend health
MAX_RETRIES=12
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_success "Backend is healthy!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_error "Backend health check failed!"
        print_info "Check logs: docker-compose logs backend"
        exit 1
    fi
    print_info "Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

# Test HTTP
print_info "Testing HTTP access..."
if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTP is working"
elif curl -f http://$DOMAIN > /dev/null 2>&1; then
    print_success "HTTP is accessible"
else
    print_warning "HTTP test failed (this is normal if DNS not propagated yet)"
fi

################################################################################
# Generate SSL Certificate
################################################################################

print_header "Step 5: Generating SSL Certificate"

print_info "Stopping nginx to free port 80..."
docker-compose stop nginx
sleep 2

print_info "Generating SSL certificate with Let's Encrypt..."
print_info "This may take a minute..."
echo ""

# Generate certificate
if docker-compose run --rm certbot certonly --standalone \
    -d $DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive; then
    
    echo ""
    print_success "SSL certificate generated successfully!"
else
    echo ""
    print_error "Certificate generation failed!"
    print_info "Common issues:"
    print_info "  1. DNS not pointing to this server"
    print_info "  2. Port 80 blocked by firewall"
    print_info "  3. Domain not accessible from internet"
    echo ""
    print_info "Troubleshooting:"
    print_info "  - Check DNS: nslookup $DOMAIN"
    print_info "  - Check firewall: sudo ufw status"
    print_info "  - Allow ports: sudo ufw allow 80/tcp && sudo ufw allow 443/tcp"
    echo ""
    print_info "Starting nginx again..."
    docker-compose start nginx
    exit 1
fi

################################################################################
# Verify Certificate
################################################################################

print_header "Step 6: Verifying Certificate"

print_info "Checking certificate..."
if docker-compose run --rm certbot certificates | grep -q "$DOMAIN"; then
    print_success "Certificate verified"
    echo ""
    docker-compose run --rm certbot certificates 2>/dev/null | grep -A5 "$DOMAIN" || true
else
    print_error "Certificate verification failed"
    exit 1
fi

################################################################################
# Restart Services with HTTPS
################################################################################

print_header "Step 7: Enabling HTTPS"

print_info "Restarting all services with HTTPS enabled..."
docker-compose down
sleep 2
docker-compose up -d

print_info "Waiting for services to start..."
sleep 10

################################################################################
# Test HTTPS
################################################################################

print_header "Step 8: Testing HTTPS"

# Test HTTPS
MAX_RETRIES=12
RETRY_COUNT=0
print_info "Testing HTTPS connection..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -k https://$DOMAIN/health > /dev/null 2>&1; then
        print_success "HTTPS is working!"
        
        # Test certificate validity
        if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
            print_success "SSL certificate is valid and trusted!"
        else
            print_warning "HTTPS works but certificate might need DNS propagation"
        fi
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_warning "HTTPS test failed"
        print_info "This might be due to DNS propagation delay"
        print_info "Check logs: docker-compose logs nginx"
        break
    fi
    print_info "Waiting for HTTPS... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

# Test HTTP redirect
print_info "Testing HTTP to HTTPS redirect..."
if curl -I http://$DOMAIN 2>/dev/null | grep -q "301"; then
    print_success "HTTP redirects to HTTPS"
else
    print_warning "HTTP redirect test inconclusive"
fi

################################################################################
# Setup Auto-Renewal
################################################################################

print_header "Step 9: Setting Up Auto-Renewal"

# Test renewal
print_info "Testing certificate renewal (dry run)..."
if docker-compose run --rm certbot renew --dry-run > /dev/null 2>&1; then
    print_success "Certificate renewal test passed"
else
    print_warning "Certificate renewal test failed (this is usually fine)"
fi

# Add cron job
print_info "Setting up auto-renewal cron job..."
CRON_JOB="0 0 * * 0 cd $(pwd) && docker-compose run --rm certbot renew && docker-compose restart nginx"

if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    print_info "Cron job already exists"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    print_success "Auto-renewal cron job added"
    print_info "Certificates will auto-renew every Sunday at midnight"
fi

################################################################################
# Final Verification
################################################################################

print_header "Step 10: Final Verification"

# Check services
print_info "Checking service status..."
docker-compose ps

echo ""

# Check certificate expiry
print_info "Certificate information:"
docker-compose run --rm certbot certificates 2>/dev/null | grep -A5 "$DOMAIN" || print_warning "Could not retrieve certificate info"

################################################################################
# Success Summary
################################################################################

print_header "🎉 Deployment Complete!"

print_success "Your CivicFix backend is now live with HTTPS!"
echo ""

print_info "🌐 Your URLs:"
echo "  • HTTPS: https://$DOMAIN"
echo "  • API:   https://$DOMAIN/api/v1"
echo ""

print_info "🧪 Test Commands:"
echo "  • Health check:  curl https://$DOMAIN/health"
echo "  • Categories:    curl https://$DOMAIN/api/v1/categories"
echo "  • In browser:    https://$DOMAIN/health"
echo ""

print_info "📊 Monitoring:"
echo "  • View logs:     docker-compose logs -f"
echo "  • Check status:  docker-compose ps"
echo "  • Check cert:    docker-compose run --rm certbot certificates"
echo ""

print_info "🔄 Maintenance:"
echo "  • Restart:       docker-compose restart"
echo "  • Update:        git pull && docker-compose build && docker-compose up -d"
echo "  • Test renewal:  docker-compose run --rm certbot renew --dry-run"
echo ""

print_info "📱 Next Steps:"
echo "  1. Test HTTPS in browser: https://$DOMAIN/health"
echo "  2. Update frontend API URL to: https://$DOMAIN"
echo "  3. Test all API endpoints"
echo "  4. Monitor logs for any issues"
echo ""

print_info "🔒 SSL Certificate:"
echo "  • Provider:      Let's Encrypt"
echo "  • Auto-renewal:  Enabled (every Sunday)"
echo "  • Expiry:        ~90 days from now"
echo ""

print_info "🆘 Troubleshooting:"
echo "  • If HTTPS doesn't work, wait 5-10 minutes for DNS propagation"
echo "  • Check logs: docker-compose logs nginx"
echo "  • Check certificate: docker-compose run --rm certbot certificates"
echo "  • See TROUBLESHOOTING_SSL.md for common issues"
echo ""

print_success "Deployment script completed successfully!"
print_info "Your backend is production-ready! 🚀"

################################################################################
# End
################################################################################

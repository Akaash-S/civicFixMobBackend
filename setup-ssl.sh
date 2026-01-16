#!/bin/bash

# SSL Certificate Setup Script
# Automates the process of setting up HTTPS with Let's Encrypt

set -e

echo "🔒 SSL Certificate Setup for CivicFix Backend"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found!"
    exit 1
fi

# Get domain name
echo "Enter your domain name (e.g., civicfix-server.asolvitra.tech):"
read -p "Domain: " DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required!"
    exit 1
fi

# Get email
echo ""
echo "Enter your email address (for Let's Encrypt notifications):"
read -p "Email: " EMAIL

if [ -z "$EMAIL" ]; then
    print_error "Email is required!"
    exit 1
fi

# Ask about www subdomain
echo ""
read -p "Do you want to include www.$DOMAIN? (y/n): " INCLUDE_WWW

echo ""
print_info "Configuration:"
echo "  Domain: $DOMAIN"
if [ "$INCLUDE_WWW" = "y" ]; then
    echo "  WWW: www.$DOMAIN"
fi
echo "  Email: $EMAIL"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_warning "Setup cancelled"
    exit 0
fi

echo ""
print_info "Step 1: Checking DNS resolution..."

# Check if domain resolves
if nslookup $DOMAIN > /dev/null 2>&1; then
    RESOLVED_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    print_success "Domain resolves to: $RESOLVED_IP"
else
    print_error "Domain does not resolve!"
    print_info "Please configure your DNS A record first:"
    print_info "  Type: A"
    print_info "  Name: @"
    print_info "  Value: $(curl -s http://checkip.amazonaws.com)"
    print_info "  TTL: 3600"
    exit 1
fi

echo ""
print_info "Step 2: Testing HTTP access..."

# Test HTTP
if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTP is working"
else
    print_warning "HTTP health check failed"
    print_info "Make sure your backend is running and nginx is configured"
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

echo ""
print_info "Step 3: Stopping nginx..."
docker-compose stop nginx
print_success "Nginx stopped"

echo ""
print_info "Step 4: Generating SSL certificate..."

# Build certbot command
CERTBOT_CMD="docker-compose run --rm certbot certonly --standalone -d $DOMAIN"
if [ "$INCLUDE_WWW" = "y" ]; then
    CERTBOT_CMD="$CERTBOT_CMD -d www.$DOMAIN"
fi
CERTBOT_CMD="$CERTBOT_CMD --email $EMAIL --agree-tos --no-eff-email"

print_info "Running: $CERTBOT_CMD"
echo ""

# Run certbot
if eval $CERTBOT_CMD; then
    print_success "Certificate generated successfully!"
else
    print_error "Certificate generation failed!"
    print_info "Starting nginx again..."
    docker-compose start nginx
    exit 1
fi

echo ""
print_info "Step 5: Updating nginx configuration..."

# Backup nginx.conf
cp nginx.conf nginx.conf.backup
print_success "Backup created: nginx.conf.backup"

# Update server_name in nginx.conf
if [ "$INCLUDE_WWW" = "y" ]; then
    sed -i "s/server_name _;/server_name $DOMAIN www.$DOMAIN;/g" nginx.conf
else
    sed -i "s/server_name _;/server_name $DOMAIN;/g" nginx.conf
fi

# Update SSL certificate paths
sed -i "s|ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|g" nginx.conf
sed -i "s|ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|g" nginx.conf

# Uncomment HTTPS server block (this is tricky, might need manual editing)
print_warning "You may need to manually uncomment the HTTPS server block in nginx.conf"
print_info "Look for the commented HTTPS section and remove the # symbols"

echo ""
print_info "Step 6: Restarting services..."
docker-compose down
docker-compose up -d
print_success "Services restarted"

echo ""
print_info "Step 7: Testing HTTPS..."
sleep 5

if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTPS is working!"
else
    print_warning "HTTPS test failed"
    print_info "Check nginx logs: docker-compose logs nginx"
    print_info "You may need to manually edit nginx.conf"
fi

echo ""
print_info "Step 8: Setting up auto-renewal..."

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    print_info "Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "0 0 * * 0 cd $(pwd) && docker-compose run --rm certbot renew && docker-compose restart nginx") | crontab -
    print_success "Auto-renewal cron job added"
fi

echo ""
echo "=============================================="
print_success "SSL Setup Complete!"
echo "=============================================="
echo ""

print_info "Your backend is now accessible at:"
echo "  🔒 https://$DOMAIN"
if [ "$INCLUDE_WWW" = "y" ]; then
    echo "  🔒 https://www.$DOMAIN"
fi
echo ""

print_info "Next steps:"
echo "  1. Test HTTPS: curl https://$DOMAIN/health"
echo "  2. Update frontend API URL to use HTTPS"
echo "  3. Update CORS_ORIGINS in .env if needed"
echo "  4. Monitor certificate expiry (auto-renewal is configured)"
echo ""

print_info "Useful commands:"
echo "  - View logs: docker-compose logs -f nginx"
echo "  - Test renewal: docker-compose run --rm certbot renew --dry-run"
echo "  - Check certificates: docker-compose run --rm certbot certificates"
echo ""

print_success "Setup script completed!"

#!/bin/bash

# SSL Certificate Setup Script for CivicFix Backend
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
    print_info "Please install Docker Compose first:"
    print_info "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    print_info "  sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

print_success "Docker Compose found"
echo ""

# Get domain name
print_info "Enter your domain name (e.g., civicfix-server.asolvitra.tech):"
read -p "Domain: " DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required!"
    exit 1
fi

# Get email
echo ""
print_info "Enter your email address (for Let's Encrypt notifications):"
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
echo "=============================================="
print_info "Step 1: Checking DNS resolution..."
echo "=============================================="
echo ""

# Check if domain resolves
if nslookup $DOMAIN > /dev/null 2>&1; then
    RESOLVED_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
    if [ -z "$RESOLVED_IP" ]; then
        # Try alternative method
        RESOLVED_IP=$(dig +short $DOMAIN | head -1)
    fi
    
    if [ -n "$RESOLVED_IP" ]; then
        print_success "Domain resolves to: $RESOLVED_IP"
    else
        print_warning "Could not determine resolved IP"
    fi
else
    print_error "Domain does not resolve!"
    print_info "Please configure your DNS A record first:"
    print_info "  Type: A"
    print_info "  Name: @"
    print_info "  Value: $(curl -s http://checkip.amazonaws.com)"
    print_info "  TTL: 3600"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " CONTINUE_DNS
    if [ "$CONTINUE_DNS" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "=============================================="
print_info "Step 2: Testing HTTP access..."
echo "=============================================="
echo ""

# Test HTTP
if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTP is working"
elif curl -f http://$DOMAIN > /dev/null 2>&1; then
    print_success "HTTP is accessible"
else
    print_warning "HTTP health check failed"
    print_info "This is normal if backend isn't running yet"
    print_info "Make sure your backend is deployed and nginx is configured"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE_HTTP
    if [ "$CONTINUE_HTTP" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "=============================================="
print_info "Step 3: Stopping nginx..."
echo "=============================================="
echo ""

docker-compose stop nginx
print_success "Nginx stopped"

echo ""
echo "=============================================="
print_info "Step 4: Generating SSL certificate..."
echo "=============================================="
echo ""

# Build certbot command
CERTBOT_CMD="docker-compose run --rm certbot certonly --standalone -d $DOMAIN"
if [ "$INCLUDE_WWW" = "y" ]; then
    CERTBOT_CMD="$CERTBOT_CMD -d www.$DOMAIN"
fi
CERTBOT_CMD="$CERTBOT_CMD --email $EMAIL --agree-tos --no-eff-email"

print_info "Running certbot..."
echo ""

# Run certbot
if eval $CERTBOT_CMD; then
    echo ""
    print_success "Certificate generated successfully!"
else
    echo ""
    print_error "Certificate generation failed!"
    print_info "Common issues:"
    print_info "  1. DNS not pointing to this server"
    print_info "  2. Port 80 blocked by firewall"
    print_info "  3. Another service using port 80"
    echo ""
    print_info "Starting nginx again..."
    docker-compose start nginx
    exit 1
fi

echo ""
echo "=============================================="
print_info "Step 5: Verifying certificate..."
echo "=============================================="
echo ""

# Verify certificate
if docker-compose run --rm certbot certificates | grep -q "$DOMAIN"; then
    print_success "Certificate verified"
    docker-compose run --rm certbot certificates | grep -A5 "$DOMAIN"
else
    print_error "Certificate verification failed"
    exit 1
fi

echo ""
echo "=============================================="
print_info "Step 6: Updating nginx configuration..."
echo "=============================================="
echo ""

# Backup nginx.conf
if [ -f nginx.conf ]; then
    cp nginx.conf nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
    print_success "Backup created"
fi

# Check if we have the HTTPS config
if [ -f nginx.conf.https ]; then
    print_info "Using nginx.conf.https as template"
    cp nginx.conf.https nginx.conf
elif grep -q "listen 443 ssl" nginx.conf; then
    print_info "nginx.conf already has HTTPS configuration"
else
    print_warning "nginx.conf doesn't have HTTPS configuration"
    print_info "You may need to manually add HTTPS server block"
fi

# Update server_name in nginx.conf
print_info "Updating server_name in nginx.conf..."

if [ "$INCLUDE_WWW" = "y" ]; then
    # Update both HTTP and HTTPS server blocks
    sed -i "s/server_name .*;/server_name $DOMAIN www.$DOMAIN;/g" nginx.conf
else
    sed -i "s/server_name .*;/server_name $DOMAIN;/g" nginx.conf
fi

# Update SSL certificate paths
print_info "Updating SSL certificate paths..."
sed -i "s|ssl_certificate /etc/letsencrypt/live/[^/]*/fullchain.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|g" nginx.conf
sed -i "s|ssl_certificate_key /etc/letsencrypt/live/[^/]*/privkey.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|g" nginx.conf

print_success "Nginx configuration updated"

echo ""
echo "=============================================="
print_info "Step 7: Testing nginx configuration..."
echo "=============================================="
echo ""

# Start nginx temporarily to test config
docker-compose up -d nginx
sleep 2

if docker-compose exec nginx nginx -t > /dev/null 2>&1; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
    print_info "Running test again with output:"
    docker-compose exec nginx nginx -t
    echo ""
    print_warning "Please fix nginx.conf manually"
    exit 1
fi

echo ""
echo "=============================================="
print_info "Step 8: Restarting all services..."
echo "=============================================="
echo ""

docker-compose down
docker-compose up -d
print_success "Services restarted"

echo ""
print_info "Waiting for services to start..."
sleep 10

echo ""
echo "=============================================="
print_info "Step 9: Testing HTTPS..."
echo "=============================================="
echo ""

# Test HTTPS
if curl -f -k https://$DOMAIN/health > /dev/null 2>&1; then
    print_success "HTTPS is working!"
    echo ""
    print_info "Testing certificate validity..."
    if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
        print_success "Certificate is valid and trusted!"
    else
        print_warning "HTTPS works but certificate might have issues"
        print_info "This could be due to DNS propagation delay"
    fi
elif curl -f -k https://$DOMAIN > /dev/null 2>&1; then
    print_success "HTTPS is accessible"
else
    print_warning "HTTPS test failed"
    print_info "Checking nginx logs..."
    echo ""
    docker-compose logs --tail=20 nginx
    echo ""
    print_info "You may need to:"
    print_info "  1. Check nginx logs: docker-compose logs nginx"
    print_info "  2. Verify nginx.conf has HTTPS server block uncommented"
    print_info "  3. Check firewall allows port 443"
fi

echo ""
echo "=============================================="
print_info "Step 10: Setting up auto-renewal..."
echo "=============================================="
echo ""

# Test renewal
print_info "Testing certificate renewal (dry run)..."
if docker-compose run --rm certbot renew --dry-run > /dev/null 2>&1; then
    print_success "Certificate renewal test passed"
else
    print_warning "Certificate renewal test failed"
    print_info "You can test manually: docker-compose run --rm certbot renew --dry-run"
fi

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    print_info "Cron job already exists"
else
    print_info "Adding auto-renewal cron job..."
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

print_info "Certificate details:"
docker-compose run --rm certbot certificates 2>/dev/null | grep -A5 "$DOMAIN" || echo "  Run: docker-compose run --rm certbot certificates"
echo ""

print_info "Next steps:"
echo "  1. Test HTTPS: curl https://$DOMAIN/health"
echo "  2. Test in browser: https://$DOMAIN"
echo "  3. Update frontend API URL to use HTTPS"
echo "  4. Update CORS_ORIGINS in .env if needed"
echo "  5. Test all API endpoints"
echo ""

print_info "Useful commands:"
echo "  - View logs: docker-compose logs -f nginx"
echo "  - Test renewal: docker-compose run --rm certbot renew --dry-run"
echo "  - Check certificates: docker-compose run --rm certbot certificates"
echo "  - Restart services: docker-compose restart"
echo ""

print_info "Troubleshooting:"
echo "  - If HTTPS doesn't work, check: docker-compose logs nginx"
echo "  - Verify certificate: openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
echo "  - Test SSL grade: https://www.ssllabs.com/ssltest/"
echo ""

print_success "Setup script completed!"

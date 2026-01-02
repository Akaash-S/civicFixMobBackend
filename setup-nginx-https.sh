#!/bin/bash

# CivicFix HTTPS Setup Script with Nginx + Let's Encrypt
# This script manages SSL certificates for civicfix-server.asolvitra.tech

set -e

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL="admin@asolvitra.tech"  # Change this to your email
COMPOSE_FILE="docker-compose.yml"

echo "🔒 CivicFix HTTPS Setup with Nginx + Let's Encrypt"
echo "=================================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Function to check if containers are running
check_containers() {
    if ! docker-compose ps | grep -q "civicfix-backend.*Up"; then
        echo "❌ Backend container is not running!"
        echo "Please start the stack first: docker-compose up -d"
        exit 1
    fi
    
    if ! docker-compose ps | grep -q "civicfix-nginx.*Up"; then
        echo "❌ Nginx container is not running!"
        echo "Please start the stack first: docker-compose up -d"
        exit 1
    fi
    
    if ! docker-compose ps | grep -q "civicfix-certbot.*Up"; then
        echo "❌ Certbot container is not running!"
        echo "Please start the stack first: docker-compose up -d"
        exit 1
    fi
}

# Function to generate initial certificates
generate_certificates() {
    echo "📋 Generating SSL certificates for $DOMAIN..."
    echo ""
    
    # Run certbot to generate certificates using webroot method
    docker-compose exec certbot certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d $DOMAIN
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificates generated successfully!"
        echo ""
        echo "📁 Certificate files are stored in Docker volumes:"
        echo "   - Certificates: letsencrypt-certs"
        echo "   - Webroot: letsencrypt-webroot"
        echo "   - Logs: letsencrypt-logs"
        echo ""
        echo "🔧 Next step: Enable HTTPS in Nginx configuration"
        echo "   Run: $0 enable-https"
        echo ""
    else
        echo "❌ Certificate generation failed!"
        echo "Please check the logs and try again."
        exit 1
    fi
}

# Function to enable HTTPS in Nginx
enable_https() {
    echo "🔧 Enabling HTTPS in Nginx configuration..."
    echo ""
    
    # Check if certificates exist
    if ! docker-compose exec certbot test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem; then
        echo "❌ SSL certificates not found!"
        echo "Please generate certificates first: $0 generate"
        exit 1
    fi
    
    # Create backup of current nginx.conf
    cp nginx.conf nginx.conf.backup
    
    # Uncomment HTTPS server block in nginx.conf
    sed -i 's/^    # server {/    server {/g' nginx.conf
    sed -i 's/^    #     /    /g' nginx.conf
    sed -i 's/^    # }/    }/g' nginx.conf
    
    echo "✅ HTTPS server block enabled in nginx.conf"
    echo ""
    echo "🔄 Reloading Nginx configuration..."
    docker-compose exec nginx nginx -s reload
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx reloaded successfully!"
        echo ""
        echo "🎉 HTTPS is now enabled!"
        echo "   Test: https://$DOMAIN/health"
        echo ""
    else
        echo "❌ Nginx reload failed!"
        echo "Restoring backup configuration..."
        cp nginx.conf.backup nginx.conf
        exit 1
    fi
}

# Function to renew certificates
renew_certificates() {
    echo "🔄 Renewing SSL certificates..."
    echo ""
    
    docker-compose exec certbot certbot renew --quiet
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificates renewed successfully!"
        echo "🔄 Reloading Nginx to use new certificates..."
        docker-compose exec nginx nginx -s reload
    else
        echo "❌ Certificate renewal failed!"
        echo "Please check the logs for details."
        exit 1
    fi
}

# Function to check certificate status
check_certificates() {
    echo "📋 Checking certificate status..."
    echo ""
    
    docker-compose exec certbot certbot certificates
}

# Function to test certificate setup
test_setup() {
    echo "🧪 Testing certificate setup..."
    echo ""
    
    # Test if webroot is accessible
    echo "Testing webroot accessibility..."
    docker-compose exec nginx ls -la /var/www/certbot/
    
    # Test if certificates exist
    echo ""
    echo "Checking certificate files..."
    docker-compose exec certbot ls -la /etc/letsencrypt/live/$DOMAIN/ || echo "No certificates found yet"
    
    # Test HTTP access
    echo ""
    echo "Testing HTTP access..."
    curl -I http://$DOMAIN/health || echo "HTTP test failed"
    
    # Test HTTPS access (if certificates exist)
    if docker-compose exec certbot test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem; then
        echo ""
        echo "Testing HTTPS access..."
        curl -I https://$DOMAIN/health || echo "HTTPS test failed"
    fi
}

# Main menu
case "${1:-menu}" in
    "generate"|"new")
        check_containers
        generate_certificates
        ;;
    "enable-https"|"enable")
        check_containers
        enable_https
        ;;
    "renew")
        check_containers
        renew_certificates
        ;;
    "check"|"status")
        check_containers
        check_certificates
        ;;
    "test")
        check_containers
        test_setup
        ;;
    "menu"|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  generate      Generate new SSL certificates"
        echo "  enable-https  Enable HTTPS in Nginx (after generating certificates)"
        echo "  renew         Renew existing certificates"
        echo "  check         Check certificate status"
        echo "  test          Test certificate setup"
        echo ""
        echo "Typical workflow:"
        echo "  1. $0 generate      # Generate certificates"
        echo "  2. $0 enable-https  # Enable HTTPS in Nginx"
        echo "  3. $0 test          # Test the setup"
        echo ""
        ;;
esac
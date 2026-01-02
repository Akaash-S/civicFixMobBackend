#!/bin/bash

# CivicFix HTTPS Setup Script with Let's Encrypt
# This script manages SSL certificates for civicfix-server.asolvitra.tech

set -e

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL="admin@asolvitra.tech"  # Change this to your email
COMPOSE_FILE="docker-compose.yml"

echo "🔒 CivicFix HTTPS Setup with Let's Encrypt"
echo "=========================================="
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
    
    # Create webroot directory if it doesn't exist
    docker-compose exec backend mkdir -p /app/static/.well-known/acme-challenge
    
    # Run certbot to generate certificates
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
    else
        echo "❌ Certificate generation failed!"
        echo "Please check the logs and try again."
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
test_certificates() {
    echo "🧪 Testing certificate setup..."
    echo ""
    
    # Test if webroot is accessible
    echo "Testing webroot accessibility..."
    docker-compose exec backend ls -la /app/static/.well-known/
    
    # Test if certificates exist
    echo ""
    echo "Checking certificate files..."
    docker-compose exec certbot ls -la /etc/letsencrypt/live/$DOMAIN/ || echo "No certificates found yet"
}

# Function to show certificate information
show_certificate_info() {
    echo "📜 Certificate Information"
    echo "========================"
    echo ""
    
    if docker-compose exec certbot test -d /etc/letsencrypt/live/$DOMAIN; then
        echo "Certificate files location: /etc/letsencrypt/live/$DOMAIN/"
        echo ""
        docker-compose exec certbot openssl x509 -in /etc/letsencrypt/live/$DOMAIN/cert.pem -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
    else
        echo "No certificates found for $DOMAIN"
    fi
}

# Function to setup cron job for auto-renewal
setup_auto_renewal() {
    echo "⏰ Setting up automatic certificate renewal..."
    echo ""
    
    # Create renewal script
    cat > /tmp/certbot-renewal.sh << 'EOF'
#!/bin/bash
cd /path/to/your/backend/directory
docker-compose exec certbot certbot renew --quiet
if [ $? -eq 0 ]; then
    echo "$(date): Certificates renewed successfully" >> /var/log/certbot-renewal.log
else
    echo "$(date): Certificate renewal failed" >> /var/log/certbot-renewal.log
fi
EOF
    
    echo "📝 Renewal script created at /tmp/certbot-renewal.sh"
    echo ""
    echo "To setup automatic renewal, add this to your crontab:"
    echo "0 12 * * * /tmp/certbot-renewal.sh"
    echo ""
    echo "Run: crontab -e"
    echo "Then add the above line to run renewal check daily at noon."
}

# Main menu
case "${1:-menu}" in
    "generate"|"new")
        check_containers
        generate_certificates
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
        test_certificates
        ;;
    "info")
        check_containers
        show_certificate_info
        ;;
    "auto-renewal"|"cron")
        setup_auto_renewal
        ;;
    "menu"|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  generate     Generate new SSL certificates"
        echo "  renew        Renew existing certificates"
        echo "  check        Check certificate status"
        echo "  test         Test certificate setup"
        echo "  info         Show certificate information"
        echo "  auto-renewal Setup automatic renewal cron job"
        echo ""
        echo "Examples:"
        echo "  $0 generate    # First time certificate generation"
        echo "  $0 renew       # Renew certificates"
        echo "  $0 check       # Check certificate status"
        echo ""
        ;;
esac
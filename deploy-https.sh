#!/bin/bash

# CivicFix HTTPS Deployment Script
# Complete deployment with Let's Encrypt SSL certificates

set -e

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL="admin@asolvitra.tech"

echo "🚀 CivicFix HTTPS Deployment"
echo "============================"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Step 1: Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Step 2: Build and start the new stack
echo "🏗️ Building and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Step 3: Wait for backend to be healthy
echo "⏳ Waiting for backend to be healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose exec backend curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Backend failed to start within $timeout seconds"
    echo "Checking logs..."
    docker-compose logs backend
    exit 1
fi

# Step 4: Generate SSL certificates
echo "🔒 Generating SSL certificates..."
./setup-https.sh generate

# Step 5: Show deployment status
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "✅ Services Status:"
docker-compose ps

echo ""
echo "✅ Backend Health:"
docker-compose exec backend curl -s http://localhost:5000/health | python3 -m json.tool || echo "Health check failed"

echo ""
echo "✅ Certificate Status:"
docker-compose exec certbot certbot certificates || echo "No certificates found"

echo ""
echo "📋 Next Steps:"
echo "1. Configure your reverse proxy to forward traffic to 127.0.0.1:5000"
echo "2. Point your domain $DOMAIN to this server's IP address"
echo "3. Test HTTPS access: https://$DOMAIN/health"
echo "4. Set up automatic certificate renewal (see HTTPS-SETUP.md)"
echo ""
echo "📚 Documentation: See HTTPS-SETUP.md for detailed configuration"
echo ""
echo "🔧 Management Commands:"
echo "  ./setup-https.sh check    # Check certificate status"
echo "  ./setup-https.sh renew    # Renew certificates"
echo "  ./setup-https.sh info     # Show certificate info"
echo ""
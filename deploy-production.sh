#!/bin/bash

# CivicFix Production Deployment Script
# Complete HTTPS setup with Nginx reverse proxy and Let's Encrypt

set -e

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL="admin@asolvitra.tech"

echo "🚀 CivicFix Production Deployment"
echo "================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check if domain resolves to this server
    echo "Checking DNS resolution for $DOMAIN..."
    if ! nslookup $DOMAIN > /dev/null 2>&1; then
        echo "⚠️  Warning: DNS resolution failed for $DOMAIN"
        echo "   Make sure the domain points to this server's IP address"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ DNS resolution successful"
    fi
    
    # Check if ports are available
    echo "Checking if ports 80 and 443 are available..."
    if netstat -tuln | grep -q ":80 "; then
        echo "❌ Port 80 is already in use!"
        echo "   Please stop any services using port 80"
        exit 1
    fi
    if netstat -tuln | grep -q ":443 "; then
        echo "❌ Port 443 is already in use!"
        echo "   Please stop any services using port 443"
        exit 1
    fi
    echo "✅ Ports 80 and 443 are available"
    
    echo ""
}

# Function to deploy the stack
deploy_stack() {
    echo "🏗️ Deploying the stack..."
    
    # Stop any existing containers
    echo "Stopping existing containers..."
    docker-compose down || true
    
    # Build and start containers
    echo "Building and starting containers..."
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for backend to be healthy
    echo "⏳ Waiting for backend to be healthy..."
    timeout=120
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker-compose exec backend curl -f http://localhost:5000/health > /dev/null 2>&1; then
            echo "✅ Backend is healthy!"
            break
        fi
        echo "Waiting... ($counter/$timeout seconds)"
        sleep 5
        counter=$((counter + 5))
    done
    
    if [ $counter -ge $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        echo "Checking logs..."
        docker-compose logs backend
        exit 1
    fi
    
    # Wait for Nginx to be healthy
    echo "⏳ Waiting for Nginx to be healthy..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            echo "✅ Nginx is healthy!"
            break
        fi
        echo "Waiting... ($counter/$timeout seconds)"
        sleep 5
        counter=$((counter + 5))
    done
    
    if [ $counter -ge $timeout ]; then
        echo "❌ Nginx failed to start within $timeout seconds"
        echo "Checking logs..."
        docker-compose logs nginx
        exit 1
    fi
    
    echo ""
}

# Function to test HTTP access
test_http() {
    echo "🧪 Testing HTTP access..."
    
    # Test local access
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Local HTTP access working"
    else
        echo "❌ Local HTTP access failed"
        return 1
    fi
    
    # Test domain access (if DNS is configured)
    if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
        echo "✅ Domain HTTP access working"
    else
        echo "⚠️  Domain HTTP access failed (check DNS configuration)"
    fi
    
    echo ""
}

# Function to generate SSL certificates
generate_ssl() {
    echo "🔒 Generating SSL certificates..."
    
    # Make setup script executable
    chmod +x setup-nginx-https.sh
    
    # Generate certificates
    if ./setup-nginx-https.sh generate; then
        echo "✅ SSL certificates generated successfully!"
    else
        echo "❌ SSL certificate generation failed!"
        echo "Please check the logs and try again."
        exit 1
    fi
    
    echo ""
}

# Function to enable HTTPS
enable_https() {
    echo "🔐 Enabling HTTPS..."
    
    if ./setup-nginx-https.sh enable-https; then
        echo "✅ HTTPS enabled successfully!"
    else
        echo "❌ Failed to enable HTTPS!"
        exit 1
    fi
    
    echo ""
}

# Function to test HTTPS access
test_https() {
    echo "🧪 Testing HTTPS access..."
    
    # Test HTTPS access
    if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
        echo "✅ HTTPS access working"
    else
        echo "❌ HTTPS access failed"
        return 1
    fi
    
    # Test HTTP redirect
    if curl -I http://$DOMAIN/ 2>/dev/null | grep -q "301"; then
        echo "✅ HTTP to HTTPS redirect working"
    else
        echo "⚠️  HTTP to HTTPS redirect may not be working"
    fi
    
    echo ""
}

# Function to show deployment summary
show_summary() {
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    
    echo "✅ Services Status:"
    docker-compose ps
    echo ""
    
    echo "✅ Backend Health:"
    curl -s https://$DOMAIN/health | python3 -m json.tool 2>/dev/null || echo "Health check via HTTPS failed"
    echo ""
    
    echo "✅ Certificate Status:"
    ./setup-nginx-https.sh check
    echo ""
    
    echo "📋 Access URLs:"
    echo "   • HTTPS: https://$DOMAIN"
    echo "   • Health Check: https://$DOMAIN/health"
    echo "   • API Base: https://$DOMAIN/api/v1/"
    echo ""
    
    echo "🔧 Management Commands:"
    echo "   • Check certificates: ./setup-nginx-https.sh check"
    echo "   • Renew certificates: ./setup-nginx-https.sh renew"
    echo "   • View logs: docker-compose logs [service]"
    echo "   • Restart services: docker-compose restart [service]"
    echo ""
    
    echo "📚 Documentation:"
    echo "   • Setup Guide: NGINX-HTTPS-GUIDE.md"
    echo "   • Troubleshooting: See guide for common issues"
    echo ""
    
    echo "⏰ Next Steps:"
    echo "   1. Set up automatic certificate renewal (cron job)"
    echo "   2. Configure monitoring and alerting"
    echo "   3. Set up log rotation"
    echo "   4. Configure backup strategy"
    echo ""
}

# Main deployment flow
main() {
    case "${1:-full}" in
        "full"|"")
            check_prerequisites
            deploy_stack
            test_http
            generate_ssl
            enable_https
            test_https
            show_summary
            ;;
        "stack-only")
            deploy_stack
            test_http
            echo "Stack deployed. Run '$0 ssl-only' to add HTTPS."
            ;;
        "ssl-only")
            generate_ssl
            enable_https
            test_https
            show_summary
            ;;
        "test")
            test_http
            test_https
            ;;
        *)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  full        Complete deployment (default)"
            echo "  stack-only  Deploy stack without SSL"
            echo "  ssl-only    Add SSL to existing stack"
            echo "  test        Test current deployment"
            echo ""
            echo "Examples:"
            echo "  $0          # Full deployment"
            echo "  $0 full     # Full deployment"
            echo "  $0 test     # Test current setup"
            echo ""
            ;;
    esac
}

# Run main function
main "$@"
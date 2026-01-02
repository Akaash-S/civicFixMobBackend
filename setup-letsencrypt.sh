#!/bin/bash
# setup-letsencrypt.sh
# Automated script to handle the Nginx/Certbot chicken-and-egg problem

DOMAIN="civicfix-server.asolvitra.tech"
EMAIL="admin@asolvitra.tech" # Replace with valid email
RSA_KEY_SIZE=4096
DATA_PATH="./certbot"

if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
    echo "✅ Certificates already exist for $DOMAIN"
    exit 0
fi

echo "🚀 Starting Let's Encrypt Setup for $DOMAIN"

# 1. Start Nginx with temporary HTTP configuration
echo "1️⃣  Starting temporary Nginx..."
docker compose stop nginx
# Create temp config enabled for ACME challenge only
cat > nginx-temp.conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / {
        return 200 'Waiting for certificates...';
        add_header Content-Type text/plain;
    }
}
EOF

# Modify docker-compose to use temp config temporarily
# actually, simpler to just run a temp nginx container
docker run -d \
    --name temp-nginx \
    -p 80:80 \
    -v $(pwd)/nginx-temp.conf:/etc/nginx/conf.d/default.conf \
    -v /var/www/certbot:/var/www/certbot \
    nginx:alpine

echo "⏳ Waiting for Nginx to start..."
sleep 5

# 2. Request Certificate
echo "2️⃣  Requesting Certificate..."
docker compose run --rm certbot certonly --webroot \
    --webroot-path /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# 3. Cleanup
echo "3️⃣  Cleaning up..."
docker stop temp-nginx
docker rm temp-nginx
rm nginx-temp.conf

# 4. Start Production Nginx
echo "4️⃣  Starting Production Nginx..."
docker compose up -d nginx

echo "✅ Setup Complete! HTTPS should be active."

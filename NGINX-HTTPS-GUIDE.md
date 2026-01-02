# CivicFix Production HTTPS Setup Guide

Complete guide for setting up production-ready HTTPS with Docker-based Nginx reverse proxy and Let's Encrypt SSL certificates.

## 🏗️ Architecture Overview

```
Internet (80/443) → Nginx Container → Flask Backend Container (5000)
                         ↓
                    Certbot Container (SSL Management)
```

### Components
- **Nginx**: Reverse proxy with SSL termination (ports 80/443)
- **Flask Backend**: Private API server (port 5000, Docker network only)
- **Certbot**: SSL certificate management (Let's Encrypt)

## 📋 Prerequisites

1. **Domain Setup**: `civicfix-server.asolvitra.tech` must point to your server's IP
2. **Firewall**: Ports 80 and 443 must be open
3. **Docker**: Docker and docker-compose installed
4. **Email**: Valid email for Let's Encrypt registration

## 🚀 Step-by-Step Deployment

### Step 1: Start HTTP-Only Stack

```bash
# Start all services (HTTP only initially)
docker-compose up -d

# Check if all containers are running
docker-compose ps
```

**Expected output:**
```
Name                   State    Ports
civicfix-backend       Up       5000/tcp
civicfix-nginx         Up       0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
civicfix-certbot       Up
```

### Step 2: Test HTTP Access

```bash
# Test health endpoint via HTTP
curl http://civicfix-server.asolvitra.tech/health

# Should return JSON with status: "healthy"
```

### Step 3: Generate SSL Certificates

```bash
# Make script executable
chmod +x setup-nginx-https.sh

# Generate Let's Encrypt certificates
./setup-nginx-https.sh generate
```

**What happens:**
1. Certbot requests certificate from Let's Encrypt
2. Let's Encrypt sends ACME challenge to `/.well-known/acme-challenge/`
3. Nginx serves challenge files from webroot volume
4. Let's Encrypt validates domain ownership
5. Certificate issued and stored in Docker volume

### Step 4: Enable HTTPS in Nginx

```bash
# Enable HTTPS configuration
./setup-nginx-https.sh enable-https
```

**What happens:**
1. Script uncomments HTTPS server block in `nginx.conf`
2. Nginx configuration reloaded
3. HTTPS now available on port 443

### Step 5: Test HTTPS Access

```bash
# Test HTTPS endpoint
curl https://civicfix-server.asolvitra.tech/health

# Test HTTP redirect
curl -I http://civicfix-server.asolvitra.tech/
# Should return: 301 Moved Permanently
```

## 🔧 Configuration Details

### Docker Compose Services

#### Backend Service
```yaml
backend:
  expose:
    - "5000"  # Docker network only, NOT host ports
  networks:
    - civicfix-network
```
- **Security**: Not exposed to host, only accessible via Docker network
- **Communication**: Nginx proxies requests to `backend:5000`

#### Nginx Service
```yaml
nginx:
  ports:
    - "80:80"    # HTTP (redirects to HTTPS)
    - "443:443"  # HTTPS (SSL termination)
  volumes:
    - letsencrypt-certs:/etc/letsencrypt:ro
    - letsencrypt-webroot:/var/www/certbot:ro
```
- **Public Access**: Only Nginx exposed to internet
- **SSL Termination**: Handles HTTPS, forwards HTTP to Flask
- **Certificate Access**: Read-only access to Let's Encrypt certificates

#### Certbot Service
```yaml
certbot:
  volumes:
    - letsencrypt-certs:/etc/letsencrypt
    - letsencrypt-webroot:/var/www/certbot
```
- **Certificate Storage**: Persistent volumes for certificates
- **Webroot Method**: Uses shared volume for ACME challenges

### Nginx Configuration Flow

#### HTTP Server (Port 80)
```nginx
server {
    listen 80;
    
    # Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Health check (monitoring)
    location /health {
        proxy_pass http://backend;
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

#### HTTPS Server (Port 443)
```nginx
server {
    listen 443 ssl http2;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/civicfix-server.asolvitra.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/civicfix-server.asolvitra.tech/privkey.pem;
    
    # Proxy all requests to Flask
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        # ... other headers
    }
}
```

## 🔄 Certificate Management

### Manual Renewal
```bash
# Renew certificates
./setup-nginx-https.sh renew

# Check certificate status
./setup-nginx-https.sh check
```

### Automatic Renewal Setup
```bash
# Add to crontab (runs daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * cd /path/to/backend && ./setup-nginx-https.sh renew >> /var/log/certbot-renewal.log 2>&1
```

### Certificate Storage
```
Docker Volume: letsencrypt-certs
├── /etc/letsencrypt/live/civicfix-server.asolvitra.tech/
│   ├── cert.pem          # Certificate only
│   ├── chain.pem         # Certificate chain
│   ├── fullchain.pem     # Certificate + chain (use this)
│   └── privkey.pem       # Private key
```

## 🛠️ Management Commands

### Service Management
```bash
# Start stack
docker-compose up -d

# Stop stack
docker-compose down

# View logs
docker-compose logs nginx
docker-compose logs backend
docker-compose logs certbot

# Restart specific service
docker-compose restart nginx
```

### Certificate Management
```bash
# Generate new certificates
./setup-nginx-https.sh generate

# Enable HTTPS in Nginx
./setup-nginx-https.sh enable-https

# Renew certificates
./setup-nginx-https.sh renew

# Check certificate status
./setup-nginx-https.sh check

# Test setup
./setup-nginx-https.sh test
```

### Nginx Management
```bash
# Test Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx configuration
docker-compose exec nginx nginx -s reload

# View Nginx access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log

# View Nginx error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Certificate Generation Fails
**Error**: `Failed authorization procedure`

**Causes & Solutions:**
- **DNS not pointing to server**: Verify `civicfix-server.asolvitra.tech` resolves to your IP
- **Port 80 blocked**: Ensure firewall allows HTTP traffic
- **Webroot not accessible**: Check Nginx serves `/.well-known/acme-challenge/`

**Debug:**
```bash
# Test DNS resolution
nslookup civicfix-server.asolvitra.tech

# Test HTTP access to webroot
curl http://civicfix-server.asolvitra.tech/.well-known/acme-challenge/test

# Check Nginx logs
docker-compose logs nginx
```

#### 2. HTTPS Not Working
**Error**: `SSL connection error`

**Causes & Solutions:**
- **Certificates not generated**: Run `./setup-nginx-https.sh generate`
- **HTTPS not enabled**: Run `./setup-nginx-https.sh enable-https`
- **Nginx configuration error**: Check `docker-compose exec nginx nginx -t`

**Debug:**
```bash
# Check if certificates exist
docker-compose exec certbot ls -la /etc/letsencrypt/live/civicfix-server.asolvitra.tech/

# Test Nginx configuration
docker-compose exec nginx nginx -t

# Check SSL certificate
openssl s_client -connect civicfix-server.asolvitra.tech:443 -servername civicfix-server.asolvitra.tech
```

#### 3. Backend Not Accessible
**Error**: `502 Bad Gateway`

**Causes & Solutions:**
- **Backend container down**: Check `docker-compose ps`
- **Backend not healthy**: Check `docker-compose logs backend`
- **Network issues**: Verify containers on same network

**Debug:**
```bash
# Check backend health
docker-compose exec nginx curl http://backend:5000/health

# Check container network
docker network inspect backend_civicfix-network
```

### Health Checks

```bash
# Full system health check
echo "=== Container Status ==="
docker-compose ps

echo "=== Backend Health ==="
curl -s http://civicfix-server.asolvitra.tech/health | python3 -m json.tool

echo "=== HTTPS Health ==="
curl -s https://civicfix-server.asolvitra.tech/health | python3 -m json.tool

echo "=== Certificate Status ==="
./setup-nginx-https.sh check

echo "=== Nginx Configuration ==="
docker-compose exec nginx nginx -t
```

## 🔒 Security Features

### SSL Configuration
- **Modern TLS**: TLS 1.2 and 1.3 only
- **Strong Ciphers**: ECDHE and DHE cipher suites
- **HSTS**: HTTP Strict Transport Security enabled
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.

### Network Security
- **Private Backend**: Flask not exposed to internet
- **Reverse Proxy**: Only Nginx handles public traffic
- **Docker Network**: Internal communication via Docker network

### Certificate Security
- **Automatic Renewal**: Prevents certificate expiration
- **Persistent Storage**: Certificates survive container restarts
- **Read-Only Access**: Nginx has read-only access to certificates

## 📊 Monitoring

### Log Locations
```bash
# Nginx access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Nginx error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log

# Backend logs
docker-compose logs -f backend

# Certbot logs
docker-compose logs -f certbot
```

### Health Monitoring
```bash
# Backend health endpoint
curl https://civicfix-server.asolvitra.tech/health

# Certificate expiry check
./setup-nginx-https.sh check
```

## 🚀 Production Checklist

- [ ] Domain points to server IP
- [ ] Firewall allows ports 80 and 443
- [ ] All containers running (`docker-compose ps`)
- [ ] HTTP redirects to HTTPS
- [ ] HTTPS certificate valid
- [ ] Backend accessible via HTTPS
- [ ] Automatic renewal configured
- [ ] Monitoring setup
- [ ] Backup strategy for certificates

This setup provides a robust, production-ready HTTPS configuration with proper SSL termination, automatic certificate renewal, and secure backend isolation.
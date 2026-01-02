# CivicFix HTTPS Setup with Let's Encrypt

This guide explains how to set up HTTPS for CivicFix using Let's Encrypt certificates with Certbot.

## 🏗️ Architecture Overview

### Current Setup
- **Flask Backend**: Runs on `127.0.0.1:5000` (localhost only, not exposed publicly)
- **Certbot Service**: Manages SSL certificates using Let's Encrypt
- **Domain**: `civicfix-server.asolvitra.tech`
- **No Nginx**: Removed to simplify the setup

### How It Works
1. **Flask serves ACME challenges** at `/.well-known/acme-challenge/` for Let's Encrypt verification
2. **Certbot generates certificates** using the webroot method
3. **Certificates are stored persistently** in Docker volumes
4. **You configure your reverse proxy** (Cloudflare, AWS ALB, etc.) to use the certificates

## 📋 Services Explanation

### Backend Service
- **Purpose**: Flask application serving the API
- **Port**: `127.0.0.1:5000` (localhost only)
- **Webroot**: Serves Let's Encrypt challenges at `/.well-known/acme-challenge/`
- **Security**: Not exposed publicly, only accessible via reverse proxy

### Certbot Service
- **Purpose**: SSL certificate generation and renewal
- **Method**: Webroot validation (no need to stop services)
- **Storage**: Persistent Docker volumes for certificates
- **Renewal**: Manual or automated via cron jobs

## 🚀 Quick Start

### 1. Start the Stack
```bash
# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 2. Generate SSL Certificates

**Linux/Mac:**
```bash
./setup-https.sh generate
```

**Windows:**
```cmd
setup-https.bat generate
```

**Manual Method:**
```bash
# Create webroot directory
docker-compose exec backend mkdir -p /app/static/.well-known/acme-challenge

# Generate certificates
docker-compose exec certbot certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@asolvitra.tech \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d civicfix-server.asolvitra.tech
```

### 3. Configure Your Reverse Proxy
After certificates are generated, configure your reverse proxy (Cloudflare, Nginx, AWS ALB, etc.) to:
- **Forward HTTPS traffic** to `http://127.0.0.1:5000`
- **Use the generated certificates** from the Docker volumes
- **Handle SSL termination**

## 📁 Certificate Storage

### Docker Volumes
- **`letsencrypt-certs`**: Contains all certificate files
- **`letsencrypt-webroot`**: Webroot for ACME challenges
- **`letsencrypt-logs`**: Certbot operation logs

### Certificate Locations (Inside Containers)
```
/etc/letsencrypt/live/civicfix-server.asolvitra.tech/
├── cert.pem          # Certificate
├── chain.pem         # Certificate chain
├── fullchain.pem     # Certificate + chain (use this for most configs)
├── privkey.pem       # Private key
└── README
```

### Accessing Certificates from Host
```bash
# Copy certificates to host system
docker cp $(docker-compose ps -q certbot):/etc/letsencrypt/live/civicfix-server.asolvitra.tech/ ./certificates/

# Or mount them directly in your reverse proxy container
```

## 🔄 Certificate Renewal

### Manual Renewal
```bash
# Linux/Mac
./setup-https.sh renew

# Windows
setup-https.bat renew

# Manual command
docker-compose exec certbot certbot renew --quiet
```

### Automatic Renewal (Recommended)
Set up a cron job to run renewal daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at noon)
0 12 * * * cd /path/to/your/backend && docker-compose exec certbot certbot renew --quiet
```

### Renewal Process
1. **Certbot checks** if certificates need renewal (30 days before expiry)
2. **If renewal needed**, Certbot uses the webroot method
3. **Flask serves** the ACME challenge files
4. **Let's Encrypt validates** the domain ownership
5. **New certificates** are generated and stored

## 🛠️ Management Commands

### Check Certificate Status
```bash
./setup-https.sh check
# or
docker-compose exec certbot certbot certificates
```

### Test Setup
```bash
./setup-https.sh test
```

### View Certificate Info
```bash
./setup-https.sh info
```

### View Logs
```bash
# Certbot logs
docker-compose logs certbot

# Backend logs
docker-compose logs backend
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Domain Not Pointing to Server
**Error**: `Failed authorization procedure`
**Solution**: Ensure `civicfix-server.asolvitra.tech` points to your server's IP

#### 2. Port 80 Not Accessible
**Error**: `Connection refused`
**Solution**: Ensure your reverse proxy forwards HTTP traffic to Flask for ACME challenges

#### 3. Webroot Not Accessible
**Error**: `Challenge file not found`
**Solution**: Check if Flask is serving `/.well-known/acme-challenge/` correctly

#### 4. Permission Issues
**Error**: `Permission denied`
**Solution**: Check Docker volume permissions and container user

### Debug Commands
```bash
# Test if webroot is accessible
curl http://civicfix-server.asolvitra.tech/.well-known/acme-challenge/test

# Check container logs
docker-compose logs -f backend
docker-compose logs -f certbot

# Inspect volumes
docker volume inspect backend_letsencrypt-certs
docker volume inspect backend_letsencrypt-webroot

# Test certificate generation (dry run)
docker-compose exec certbot certbot certonly --webroot --webroot-path=/var/www/certbot --email admin@asolvitra.tech --agree-tos --no-eff-email --dry-run -d civicfix-server.asolvitra.tech
```

## 🔒 Security Considerations

### Best Practices
1. **Keep certificates secure**: Limit access to certificate files
2. **Monitor expiry**: Set up alerts for certificate expiration
3. **Use strong ciphers**: Configure your reverse proxy with modern TLS settings
4. **Regular updates**: Keep Certbot and Docker images updated
5. **Backup certificates**: Regularly backup the `letsencrypt-certs` volume

### Recommended Reverse Proxy Configuration
```nginx
# Example Nginx configuration
server {
    listen 443 ssl http2;
    server_name civicfix-server.asolvitra.tech;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Forward to Flask backend
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name civicfix-server.asolvitra.tech;
    return 301 https://$server_name$request_uri;
}
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs`
3. Test with dry-run: `--dry-run` flag with certbot
4. Verify DNS configuration
5. Check firewall settings

## 🔄 Migration from Nginx Setup

If you're migrating from the previous Nginx setup:
1. **Stop the old stack**: `docker-compose down`
2. **Remove Nginx volumes**: `docker volume rm $(docker volume ls -q | grep nginx)`
3. **Update docker-compose.yml**: Use the new configuration
4. **Start new stack**: `docker-compose up -d`
5. **Generate certificates**: `./setup-https.sh generate`
6. **Configure external reverse proxy**: Point to `127.0.0.1:5000`
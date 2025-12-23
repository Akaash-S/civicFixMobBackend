# 🚀 CivicFix Backend - Final Docker Deployment Guide

**Complete step-by-step guide to deploy CivicFix backend using Docker and Docker Compose**

---

## 📋 Prerequisites Checklist

### Server Requirements
- [ ] **Ubuntu 20.04+** or **Amazon Linux 2**
- [ ] **Minimum 2GB RAM** (4GB recommended)
- [ ] **2 vCPUs minimum**
- [ ] **20GB storage minimum**
- [ ] **Root or sudo access**

### Network Requirements
- [ ] **Port 80** (HTTP) - open to internet
- [ ] **Port 443** (HTTPS) - open to internet  
- [ ] **Port 22** (SSH) - for management
- [ ] **Port 5000** (Backend) - internal/testing

---

## 🛠️ Step 1: Server Setup

### 1.1 Update System
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git nano htop unzip
```

### 1.2 Install Docker
```bash
# Download and install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
docker info
```

### 1.3 Install Docker Compose
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## 📁 Step 2: Get the Code

### 2.1 Clone Repository
```bash
# Navigate to deployment directory
cd /opt
sudo mkdir -p civicfix
sudo chown $USER:$USER civicfix
cd civicfix

# Clone your repository
git clone <your-repository-url> backend
cd backend

# Or if you already have the code, navigate to it
cd /path/to/your/backend/code
```

### 2.2 Verify Files
```bash
# Check required files exist
ls -la

# You should see:
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - run.py
# - app/ directory
# - .env.example
```

---

## 🔐 Step 3: Configure Environment

### 3.1 Generate Secure Secrets
```bash
# Generate Flask secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate database password
python3 -c "import secrets, string; chars=string.ascii_letters+string.digits+'!@#$%^&*'; print('DB_PASSWORD=' + ''.join(secrets.choice(chars) for _ in range(24)))"

# Save these values - you'll need them!
```

### 3.2 Create Production Environment File
```bash
# Copy template
cp .env.example .env.production

# Edit with your values
nano .env.production
```

**Fill in these required values:**
```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=<your-generated-secret-key>

# Database Configuration
# Option A: SQLite (for testing/simple deployment)
DATABASE_URL=sqlite:///civicfix.db

# Option B: PostgreSQL (for production)
# DATABASE_URL=postgresql://username:password@host:5432/database
# DB_HOST=your-database-host
# DB_PORT=5432
# DB_NAME=civicfix_db
# DB_USER=civicfix_user
# DB_PASSWORD=<your-generated-password>

# AWS Configuration (required for file uploads)
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=<your-aws-region>
S3_BUCKET_NAME=<your-s3-bucket>

# Firebase Configuration (required for authentication)
# Option 1: Inline JSON (recommended for deployment)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"your-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}

# Option 2: File path (alternative)
# FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json

FIREBASE_PROJECT_ID=<your-firebase-project-id>

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Settings
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# File Upload Settings
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov

# API Settings
API_VERSION=v1

# Socket.IO Configuration
SOCKETIO_ASYNC_MODE=eventlet

# Production Settings
GUNICORN_WORKERS=2
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30
```

### 3.3 Add Firebase Service Account

**Option 1: Inline JSON (Recommended)**
```bash
# Get your Firebase service account JSON from Firebase Console:
# Project Settings → Service Accounts → Generate new private key

# Convert the JSON file to a single line:
cat service-account.json | jq -c .

# Add the single-line JSON to your .env.production file:
nano .env.production

# Add this line (replace with your actual JSON):
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project",...}
```

**Option 2: File Path (Alternative)**
```bash
# Upload service account file to server
scp service-account.json ubuntu@your-server:/opt/civicfix/backend/

# Or create/edit directly on server
nano service-account.json
# Paste your Firebase service account JSON content

# Set in .env.production:
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
```

### 3.4 Set Secure Permissions
```bash
# Secure environment files
chmod 600 .env.production

# If using service account file (optional)
chmod 600 service-account.json 2>/dev/null || true

# Verify permissions
ls -la .env.production
```

---

## 🐳 Step 4: Docker Deployment

### 4.1 Method A: Using Docker Compose (Recommended)

#### Start All Services
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Verify Deployment
```bash
# Check container health
docker-compose ps

# Test health endpoint
curl http://localhost:5000/health

# Check logs for any errors
docker-compose logs civicfix-backend
```

### 4.2 Method B: Using Deployment Script

#### Make Script Executable
```bash
chmod +x docker-deploy.sh
```

#### Run Full Deployment
```bash
# Deploy everything
./docker-deploy.sh deploy

# Or use individual commands:
./docker-deploy.sh start    # Start containers
./docker-deploy.sh stop     # Stop containers
./docker-deploy.sh restart  # Restart containers
./docker-deploy.sh logs     # View logs
./docker-deploy.sh status   # Check status
```

### 4.3 Method C: Manual Docker Commands

#### Create Network
```bash
docker network create civicfix-network
```

#### Start Redis
```bash
docker run -d \
  --name civicfix-redis \
  --network civicfix-network \
  --restart unless-stopped \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes --maxmemory 256mb
```

#### Build and Start Backend
```bash
# Build image
docker build -t civicfix/backend:latest .

# Run backend container
docker run -d \
  --name civicfix-backend \
  --network civicfix-network \
  --restart unless-stopped \
  --env-file .env.production \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/service-account.json:/app/service-account.json:ro \
  civicfix/backend:latest
```

#### Start Nginx (Optional)
```bash
docker run -d \
  --name civicfix-nginx \
  --network civicfix-network \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine
```

---

## ✅ Step 5: Verification

### 5.1 Check All Services
```bash
# Check running containers
docker ps

# Expected output should show:
# - civicfix-backend (port 5000)
# - civicfix-redis (port 6379)
# - civicfix-nginx (ports 80, 443) [if using]
```

### 5.2 Test Application
```bash
# Test health endpoint
curl http://localhost:5000/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "version": "1.0.0"}

# Test from external IP
curl http://YOUR_SERVER_IP:5000/health
```

### 5.3 Check Logs
```bash
# View backend logs
docker logs civicfix-backend

# Follow logs in real-time
docker logs -f civicfix-backend

# Or with docker-compose
docker-compose logs -f civicfix-backend
```

---

## 🔧 Step 6: Production Configuration

### 6.1 Setup Nginx Reverse Proxy
```bash
# Install Nginx on host (alternative to Docker Nginx)
sudo apt install nginx

# Create site configuration
sudo nano /etc/nginx/sites-available/civicfix

# Add configuration:
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to backend
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:5000/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/civicfix /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 6.2 Setup SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### 6.3 Setup Firewall
```bash
# Configure UFW firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🔄 Step 7: Management Commands

### 7.1 Container Management
```bash
# Start services
docker-compose up -d
# or
./docker-deploy.sh start

# Stop services
docker-compose down
# or
./docker-deploy.sh stop

# Restart services
docker-compose restart
# or
./docker-deploy.sh restart

# Update application
git pull origin main
docker-compose build --no-cache
docker-compose up -d
# or
./docker-deploy.sh update
```

### 7.2 Monitoring
```bash
# View resource usage
docker stats

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs
docker-compose logs -f --tail=100

# Check disk usage
df -h
docker system df
```

### 7.3 Backup
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

mkdir -p $BACKUP_DIR

# Backup application data
cp -r logs/ $BACKUP_DIR/logs_$DATE/
cp .env.production $BACKUP_DIR/env_$DATE.backup

# Backup database (if using SQLite)
cp civicfix.db $BACKUP_DIR/db_$DATE.sqlite 2>/dev/null || true

# Create archive
tar -czf $BACKUP_DIR/civicfix_backup_$DATE.tar.gz \
    $BACKUP_DIR/logs_$DATE/ \
    $BACKUP_DIR/env_$DATE.backup \
    $BACKUP_DIR/db_$DATE.sqlite

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: civicfix_backup_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Run backup
./backup.sh

# Schedule daily backups
echo "0 2 * * * /opt/civicfix/backend/backup.sh" | sudo crontab -
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Docker Permission Denied
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl restart docker
```

#### 2. Container Won't Start
```bash
# Check logs
docker logs civicfix-backend

# Check environment variables
docker exec civicfix-backend env | grep -E "(DATABASE|AWS|FIREBASE)"

# Verify files exist
ls -la .env.production service-account.json
```

#### 3. Database Connection Failed
```bash
# For SQLite: Check file permissions
ls -la civicfix.db

# For PostgreSQL: Test connection
docker run --rm --env-file .env.production postgres:13 \
  psql $DATABASE_URL -c "SELECT version();"
```

#### 4. Port Already in Use
```bash
# Find what's using the port
sudo netstat -tulpn | grep :5000

# Kill the process
sudo kill -9 <PID>

# Or use different port
docker run -p 5001:5000 ...
```

#### 5. Out of Disk Space
```bash
# Clean Docker system
docker system prune -a -f

# Remove old images
docker image prune -a -f

# Check disk usage
df -h
docker system df
```

---

## 📊 Monitoring Setup (Optional)

### Enable Monitoring Stack
```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access Grafana
# URL: http://your-server:3000
# Username: admin
# Password: (check .env.production for GF_SECURITY_ADMIN_PASSWORD)

# Access Prometheus
# URL: http://your-server:9090
```

---

## 🎯 Quick Reference Commands

### Essential Commands
```bash
# Deploy everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Update application
git pull && docker-compose build --no-cache && docker-compose up -d

# Backup data
./backup.sh

# Check health
curl http://localhost:5000/health
```

### Emergency Commands
```bash
# Stop all containers
docker stop $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)

# Clean everything
docker system prune -a -f

# Restart Docker service
sudo systemctl restart docker
```

---

## ✅ Success Checklist

After deployment, verify these items:

- [ ] **Containers running**: `docker ps` shows all containers
- [ ] **Health check passes**: `curl http://localhost:5000/health` returns 200
- [ ] **Database connected**: No database errors in logs
- [ ] **Redis working**: Backend can connect to Redis
- [ ] **File uploads work**: AWS S3 integration functional
- [ ] **Authentication ready**: Firebase service account loaded
- [ ] **Nginx proxy working**: External access via port 80/443
- [ ] **SSL certificate active**: HTTPS working (if configured)
- [ ] **Firewall configured**: Only necessary ports open
- [ ] **Backups scheduled**: Automated backup system active
- [ ] **Monitoring active**: Logs and metrics available

---

## 🎉 Deployment Complete!

Your CivicFix backend is now running in production with Docker!

### Access Points:
- **API**: `http://your-server-ip:5000` or `https://your-domain.com`
- **Health Check**: `http://your-server-ip:5000/health`
- **Grafana** (if enabled): `http://your-server-ip:3000`
- **Prometheus** (if enabled): `http://your-server-ip:9090`

### Next Steps:
1. **Configure your mobile app** to use the API endpoint
2. **Set up monitoring alerts** for production issues
3. **Configure automated backups** to cloud storage
4. **Set up CI/CD pipeline** for automated deployments
5. **Monitor logs and performance** regularly

---

## 📞 Support

If you encounter issues:

1. **Check logs first**: `docker-compose logs -f`
2. **Verify configuration**: Ensure all environment variables are set
3. **Test connectivity**: Check network access to external services
4. **Review this guide**: Follow each step carefully
5. **Check Docker status**: Ensure Docker daemon is running

**Remember**: Keep your `.env.production` and `service-account.json` files secure and never commit them to version control!

---

**🚀 Happy Deploying!**
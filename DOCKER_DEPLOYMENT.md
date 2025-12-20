# 🐳 CivicFix Backend - Docker Deployment Guide

Complete guide for deploying CivicFix backend using Docker on AWS EC2 or any Linux server.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Amazon Linux 2 / CentOS 8+
- **RAM**: Minimum 2GB (4GB recommended)
- **CPU**: 2 vCPUs minimum
- **Storage**: 20GB minimum
- **Network**: Open ports 80, 443, 5000

### Required Services
- **AWS RDS PostgreSQL** (database)
- **AWS S3 bucket** (media storage)
- **Firebase project** (authentication)
- **Domain name** (optional, for SSL)

## 🚀 Quick Start (Automated Deployment)

### Step 1: Prepare Your Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone the repository
git clone <your-repo-url>
cd civicfix-backend/backend
```

### Step 2: Configure Environment

```bash
# Generate secure secrets
python3 generate-secrets.py

# Copy and edit production environment
cp .env.example .env.production
nano .env.production
```

**Fill in these required values in `.env.production`:**
```env
SECRET_KEY=<generated-secret-key>
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/database
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=<your-aws-region>
S3_BUCKET_NAME=<your-s3-bucket>
FIREBASE_PROJECT_ID=<your-firebase-project-id>
```

### Step 3: Add Firebase Service Account

```bash
# Download from Firebase Console and save as:
# Project Settings → Service Accounts → Generate new private key
nano service-account.json
```

### Step 4: Deploy with Docker

```bash
# Make deployment script executable
chmod +x docker-deploy.sh

# Run full deployment
./docker-deploy.sh deploy
```

That's it! Your application will be available at `http://your-server-ip`

## 📖 Manual Deployment Steps

If you prefer manual control or need to troubleshoot:

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Log out and back in, then verify
docker --version
```

### 2. Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 3. Build and Run

#### Option A: Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

#### Option B: Using Individual Docker Commands

```bash
# Create network
docker network create civicfix-network

# Build image
docker build -t civicfix/backend:latest .

# Run Redis
docker run -d \
  --name civicfix-redis \
  --network civicfix-network \
  -p 6379:6379 \
  redis:7-alpine

# Run backend
docker run -d \
  --name civicfix-backend-prod \
  --network civicfix-network \
  --env-file .env.production \
  -p 5000:5000 \
  -v ./logs:/app/logs \
  -v ./service-account.json:/app/service-account.json:ro \
  civicfix/backend:latest
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | ✅ | `generated-64-char-hex` |
| `DATABASE_URL` | PostgreSQL connection | ✅ | `postgresql://user:pass@host:5432/db` |
| `AWS_ACCESS_KEY_ID` | AWS access key | ✅ | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | ✅ | `secret-key` |
| `S3_BUCKET_NAME` | S3 bucket name | ✅ | `my-bucket` |
| `FIREBASE_PROJECT_ID` | Firebase project | ✅ | `my-project-id` |
| `REDIS_URL` | Redis connection | ❌ | `redis://redis:6379/0` |
| `CORS_ORIGINS` | Allowed origins | ❌ | `https://mydomain.com` |

### Docker Compose Profiles

```bash
# Basic deployment (backend + redis + nginx)
docker-compose up -d

# With monitoring (adds Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Production with SSL
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔍 Monitoring and Management

### Health Checks

```bash
# Check application health
curl http://localhost:5000/health

# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f civicfix-backend

# Last 100 lines
docker logs --tail 100 civicfix-backend-prod
```

### Resource Monitoring

```bash
# Container resource usage
docker stats

# System resources
htop
df -h
free -h
```

### Database Operations

```bash
# Run database migrations
docker exec civicfix-backend-prod python -c "
from app import create_app
from app.extensions import db
app, _ = create_app()
with app.app_context():
    db.create_all()
"

# Access database directly
docker exec -it civicfix-backend-prod python -c "
from app import create_app
from app.extensions import db
app, _ = create_app()
with app.app_context():
    # Your database operations here
    pass
"
```

## 🔄 Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./docker-deploy.sh update

# Or manually:
docker-compose build --no-cache
docker-compose up -d
```

### Backup Data

```bash
# Backup Redis data
docker exec civicfix-redis redis-cli BGSAVE

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Database backup (if using local PostgreSQL)
docker exec postgres-container pg_dump -U username database > backup.sql
```

### Scale Services

```bash
# Scale backend instances
docker-compose up -d --scale civicfix-backend=3

# Update resource limits
docker update --memory=1g --cpus=2 civicfix-backend-prod
```

## 🛡️ Security Configuration

### SSL/HTTPS Setup

1. **Get SSL Certificate:**
```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

2. **Update Nginx Configuration:**
```bash
# Copy SSL certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem ./ssl/

# Update nginx.conf with SSL configuration
# (See SSL section in nginx.conf)
```

### Firewall Configuration

```bash
# Ubuntu/Debian
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### Security Headers

The Nginx configuration includes security headers:
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Content Security Policy
- HSTS (when SSL is enabled)

## 🚨 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker logs civicfix-backend-prod

# Check environment variables
docker exec civicfix-backend-prod env | grep -E "(DATABASE|AWS|FIREBASE)"

# Verify files exist
ls -la .env.production service-account.json
```

#### 2. Database Connection Failed
```bash
# Test database connectivity
docker run --rm --env-file .env.production postgres:13 \
  psql $DATABASE_URL -c "SELECT version();"

# Check RDS security groups
# Ensure port 5432 is open from your server's IP
```

#### 3. AWS S3 Access Denied
```bash
# Test AWS credentials
docker run --rm --env-file .env.production amazon/aws-cli \
  s3 ls s3://your-bucket-name

# Verify IAM permissions
# User needs s3:GetObject, s3:PutObject, s3:DeleteObject
```

#### 4. Firebase Authentication Failed
```bash
# Verify service account file
docker exec civicfix-backend-prod cat service-account.json | jq .

# Check Firebase project ID
docker exec civicfix-backend-prod env | grep FIREBASE_PROJECT_ID
```

#### 5. High Memory Usage
```bash
# Check memory usage
docker stats --no-stream

# Reduce Gunicorn workers
# Edit .env.production: GUNICORN_WORKERS=2

# Restart with new limits
docker update --memory=512m civicfix-backend-prod
docker restart civicfix-backend-prod
```

### Performance Optimization

#### 1. Database Connection Pooling
```env
# Add to .env.production
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

#### 2. Redis Caching
```env
# Enable Redis caching
REDIS_URL=redis://redis:6379/0
CACHE_TYPE=redis
```

#### 3. Gunicorn Tuning
```env
# Optimize for your server
GUNICORN_WORKERS=4          # 2 * CPU cores
GUNICORN_THREADS=2          # 2-4 threads per worker
GUNICORN_TIMEOUT=30         # Request timeout
GUNICORN_KEEPALIVE=2        # Keep-alive timeout
```

## 📊 Monitoring Setup

### Prometheus + Grafana (Optional)

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana
# URL: http://your-server:3000
# Username: admin
# Password: (check .env.production for GF_SECURITY_ADMIN_PASSWORD)

# Import CivicFix dashboard
# Dashboard ID: (create custom dashboard)
```

### Log Aggregation

```bash
# Install log rotation
sudo apt install logrotate

# Configure log rotation
sudo tee /etc/logrotate.d/civicfix << EOF
/var/log/civicfix/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

## 🔄 Backup and Recovery

### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application data
docker exec civicfix-redis redis-cli BGSAVE
cp -r logs/ $BACKUP_DIR/logs_$DATE/
cp .env.production $BACKUP_DIR/env_$DATE.backup

# Compress and upload to S3 (optional)
tar -czf $BACKUP_DIR/civicfix_backup_$DATE.tar.gz \
    $BACKUP_DIR/logs_$DATE/ \
    $BACKUP_DIR/env_$DATE.backup

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup.sh" | sudo crontab -
```

## 📞 Support

### Getting Help

1. **Check logs first:**
   ```bash
   ./docker-deploy.sh logs
   ```

2. **Verify configuration:**
   ```bash
   ./docker-deploy.sh status
   ```

3. **Test connectivity:**
   ```bash
   curl -v http://localhost:5000/health
   ```

### Useful Commands

```bash
# Quick deployment commands
./docker-deploy.sh deploy    # Full deployment
./docker-deploy.sh start     # Start containers
./docker-deploy.sh stop      # Stop containers
./docker-deploy.sh restart   # Restart containers
./docker-deploy.sh update    # Update application
./docker-deploy.sh status    # Show status
./docker-deploy.sh logs      # Show logs

# Docker Compose commands
docker-compose up -d         # Start all services
docker-compose down          # Stop all services
docker-compose ps            # Show status
docker-compose logs -f       # Follow logs
docker-compose pull          # Update images
```

---

## 🎉 Success!

If everything is working correctly, you should see:

- ✅ Application running at `http://your-server-ip`
- ✅ Health check responding at `/health`
- ✅ Database connected and tables created
- ✅ AWS S3 integration working
- ✅ Firebase authentication ready
- ✅ Redis caching enabled
- ✅ Nginx reverse proxy configured
- ✅ SSL/HTTPS enabled (if configured)

Your CivicFix backend is now ready for production use! 🚀
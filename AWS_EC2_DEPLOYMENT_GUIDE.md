# 🚀 CivicFix Backend - AWS EC2 Deployment Guide

## 📋 Overview

This guide will walk you through deploying your CivicFix backend to AWS EC2, integrating with your existing AWS RDS (PostgreSQL) and S3 services for a complete cloud-native solution.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Native  │    │     AWS EC2     │    │    AWS RDS      │
│   Frontend      │◄──►│   CivicFix      │◄──►│   PostgreSQL    │
│                 │    │   Backend       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │     AWS S3      │
                       │  Media Storage  │
                       └─────────────────┘
```

## 🎯 Prerequisites

### AWS Account Setup
- ✅ AWS Account with appropriate permissions
- ✅ AWS CLI installed and configured
- ✅ Existing RDS PostgreSQL instance
- ✅ Existing S3 bucket for media uploads

### Local Requirements
- ✅ SSH key pair for EC2 access
- ✅ Your backend code ready for deployment
- ✅ Domain name (optional but recommended)

## 🔧 Step 1: EC2 Instance Setup

### 1.1 Launch EC2 Instance

**Instance Configuration:**
```
AMI: Ubuntu Server 22.04 LTS (Free Tier Eligible)
Instance Type: t3.micro (Free Tier) or t3.small (Recommended)
Storage: 20 GB gp3 SSD
Security Group: civicfix-backend-sg (create new)
Key Pair: Your existing key pair or create new
```

**Security Group Rules:**
```
Inbound Rules:
- SSH (22): Your IP address
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- Custom TCP (5000): 0.0.0.0/0 (for direct API access)

Outbound Rules:
- All traffic: 0.0.0.0/0
```

### 1.2 AWS CLI Commands

```bash
# Create security group
aws ec2 create-security-group \
    --group-name civicfix-backend-sg \
    --description "Security group for CivicFix backend"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-name civicfix-backend-sg \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

aws ec2 authorize-security-group-ingress \
    --group-name civicfix-backend-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name civicfix-backend-sg \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name civicfix-backend-sg \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.small \
    --key-name YOUR_KEY_PAIR \
    --security-groups civicfix-backend-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=CivicFix-Backend}]'
```

## 🔧 Step 2: Server Setup

### 2.1 Connect to EC2 Instance

```bash
# Get your instance public IP from AWS Console
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 2.2 Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# Install Docker (optional, for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Node.js (for any frontend builds)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application directory
sudo mkdir -p /opt/civicfix
sudo chown ubuntu:ubuntu /opt/civicfix
```

### 2.3 Clone and Setup Application

```bash
# Navigate to application directory
cd /opt/civicfix

# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/civicfix-backend.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Gunicorn and production dependencies
pip install gunicorn eventlet gevent
```

## 🔧 Step 3: Environment Configuration

### 3.1 Create Production Environment File

```bash
# Create production environment file
nano .env.production
```

**Production Environment Configuration:**
```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-super-secure-production-secret-key-generate-new-one

# Database Configuration (AWS RDS)
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/database-name
DB_HOST=your-rds-endpoint
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket-name

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Redis Configuration (ElastiCache or local Redis)
REDIS_URL=redis://localhost:6379/0

# Security Settings
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# File Upload Settings
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov

# API Settings
API_VERSION=v1

# Socket.IO Configuration
SOCKETIO_ASYNC_MODE=eventlet

# Production Settings
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30
GUNICORN_BIND=0.0.0.0:5000
```

### 3.2 Upload Firebase Service Account

```bash
# Upload your Firebase service account file
# You can use scp from your local machine:
# scp -i your-key.pem service-account.json ubuntu@YOUR_EC2_IP:/opt/civicfix/

# Or create it directly on the server
nano service-account.json
# Paste your Firebase service account JSON content
```

### 3.3 Set Proper Permissions

```bash
# Set proper permissions
chmod 600 .env.production
chmod 600 service-account.json
chmod +x deploy_production.sh
chmod +x start_production.py
```

## 🔧 Step 4: Database and Services Setup

### 4.1 Test Database Connection

```bash
# Test RDS connection
python3 fix_rds_issues.py

# Initialize database
source venv/bin/activate
python3 -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import create_app
from app.config import config
from app.extensions import db
app, _ = create_app(config['production'])
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
```

### 4.2 Install and Configure Redis (Optional)

```bash
# Install Redis for rate limiting and caching
sudo apt install redis-server -y

# Configure Redis
sudo nano /etc/redis/redis.conf
# Change: bind 127.0.0.1 ::1
# Add: maxmemory 256mb
# Add: maxmemory-policy allkeys-lru

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## 🔧 Step 5: Application Deployment

### 5.1 Create Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/civicfix-backend.service
```

**Service Configuration:**
```ini
[Unit]
Description=CivicFix Backend API
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/civicfix
Environment=PATH=/opt/civicfix/venv/bin
EnvironmentFile=/opt/civicfix/.env.production
ExecStart=/opt/civicfix/venv/bin/gunicorn --config gunicorn.conf.py run:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 5.2 Start Application Service

```bash
# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl start civicfix-backend
sudo systemctl enable civicfix-backend

# Check service status
sudo systemctl status civicfix-backend

# View logs
sudo journalctl -u civicfix-backend -f
```

## 🔧 Step 6: Nginx Reverse Proxy Setup

### 6.1 Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/civicfix-backend
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;  # Replace with your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Socket.IO
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/civicfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6.2 Enable Nginx Configuration

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/civicfix-backend /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 🔧 Step 7: SSL Certificate Setup (Let's Encrypt)

### 7.1 Install Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### 7.2 Update Security Group for HTTPS

```bash
# Allow HTTPS traffic in security group (if not already done)
aws ec2 authorize-security-group-ingress \
    --group-name civicfix-backend-sg \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

## 🔧 Step 8: Monitoring and Logging

### 8.1 Setup Log Rotation

```bash
# Create log rotation configuration
sudo nano /etc/logrotate.d/civicfix-backend
```

```
/opt/civicfix/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload civicfix-backend
    endscript
}
```

### 8.2 Setup Monitoring Script

```bash
# Create monitoring cron job
crontab -e

# Add monitoring job (check every 5 minutes)
*/5 * * * * cd /opt/civicfix && /opt/civicfix/venv/bin/python monitor_production.py check >> /opt/civicfix/logs/monitor.log 2>&1
```

### 8.3 Setup CloudWatch Logs (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

## 🔧 Step 9: Deployment Automation

### 9.1 Create Deployment Script

```bash
# Create EC2-specific deployment script
nano deploy_ec2.sh
```

```bash
#!/bin/bash

# CivicFix Backend - EC2 Deployment Script
set -e

echo "🚀 Deploying CivicFix Backend to EC2..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import create_app
from app.config import config
from app.extensions import db
app, _ = create_app(config['production'])
with app.app_context():
    db.create_all()
    print('Database migrations completed')
"

# Restart application
echo "🔄 Restarting application..."
sudo systemctl restart civicfix-backend

# Wait for service to start
sleep 5

# Check service status
echo "🔍 Checking service status..."
sudo systemctl status civicfix-backend --no-pager

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -f http://localhost:5000/health || echo "Health check failed"

echo "✅ Deployment completed successfully!"
echo "🌐 Application is running at: https://your-domain.com"
```

```bash
# Make script executable
chmod +x deploy_ec2.sh
```

## 🔧 Step 10: Testing and Verification

### 10.1 Test Application

```bash
# Test local health endpoint
curl http://localhost:5000/health

# Test through Nginx
curl http://YOUR_EC2_PUBLIC_IP/health

# Test HTTPS (if configured)
curl https://your-domain.com/health

# Test API endpoints
curl https://your-domain.com/api/v1/issues
```

### 10.2 Run Production Tests

```bash
# Run production verification
cd /opt/civicfix
source venv/bin/activate
python verify_deployment.py

# Run monitoring check
python monitor_production.py check
```

## 📊 Step 11: Performance Optimization

### 11.1 Optimize Gunicorn Configuration

```bash
# Update gunicorn.conf.py for EC2
nano gunicorn.conf.py
```

```python
# EC2-optimized Gunicorn configuration
import os
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"  # Bind to localhost (behind Nginx)
backlog = 2048

# Worker processes (adjust based on EC2 instance size)
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "eventlet"
worker_connections = 1000
threads = 2
timeout = 30
keepalive = 2

# Memory management
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/opt/civicfix/logs/access.log"
errorlog = "/opt/civicfix/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "civicfix-backend"

# Preload application
preload_app = True
```

### 11.2 Setup Application Monitoring

```bash
# Create comprehensive monitoring script
nano /opt/civicfix/monitor_ec2.py
```

```python
#!/usr/bin/env python3
"""
EC2-specific monitoring for CivicFix Backend
"""

import subprocess
import requests
import psutil
import time
from datetime import datetime

def check_system_resources():
    """Check system resources"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {memory.percent}%")
    print(f"Disk Usage: {disk.percent}%")
    
    return {
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent
    }

def check_application_health():
    """Check application health"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_service_status():
    """Check systemd service status"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'civicfix-backend'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def main():
    print(f"=== CivicFix EC2 Health Check - {datetime.now()} ===")
    
    # Check system resources
    resources = check_system_resources()
    
    # Check service
    service_ok = check_service_status()
    print(f"Service Status: {'✅ Active' if service_ok else '❌ Inactive'}")
    
    # Check application
    app_ok = check_application_health()
    print(f"Application Health: {'✅ Healthy' if app_ok else '❌ Unhealthy'}")
    
    # Overall status
    overall_ok = service_ok and app_ok and resources['cpu'] < 80 and resources['memory'] < 80
    print(f"Overall Status: {'✅ Good' if overall_ok else '⚠️ Issues Detected'}")
    
    return overall_ok

if __name__ == "__main__":
    main()
```

## 🔧 Step 12: Backup and Recovery

### 12.1 Setup Automated Backups

```bash
# Create backup script
nano /opt/civicfix/backup_ec2.sh
```

```bash
#!/bin/bash

# CivicFix EC2 Backup Script
BACKUP_DIR="/opt/civicfix/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application code
tar -czf $BACKUP_DIR/civicfix_code_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='__pycache__' \
    /opt/civicfix

# Backup database (RDS snapshot via AWS CLI)
aws rds create-db-snapshot \
    --db-instance-identifier civicfix-db \
    --db-snapshot-identifier civicfix-backup-$DATE

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "civicfix_code_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 12.2 Setup Backup Cron Job

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/civicfix/backup_ec2.sh >> /opt/civicfix/logs/backup.log 2>&1
```

## 🎯 Final Checklist

### ✅ Pre-Deployment
- [ ] EC2 instance launched and configured
- [ ] Security groups properly configured
- [ ] RDS database accessible from EC2
- [ ] S3 bucket permissions configured
- [ ] Domain name configured (optional)

### ✅ Application Setup
- [ ] Code deployed to EC2
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized

### ✅ Production Services
- [ ] Gunicorn service running
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] Redis configured (optional)
- [ ] Monitoring setup

### ✅ Testing
- [ ] Health endpoints responding
- [ ] API endpoints working
- [ ] Database connectivity verified
- [ ] File uploads to S3 working
- [ ] Real-time features functional

## 🚀 Deployment Commands Summary

```bash
# 1. Connect to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 2. Deploy application
cd /opt/civicfix
./deploy_ec2.sh

# 3. Monitor application
python monitor_ec2.py

# 4. View logs
sudo journalctl -u civicfix-backend -f
tail -f logs/error.log

# 5. Restart if needed
sudo systemctl restart civicfix-backend
sudo systemctl restart nginx
```

## 🎊 Congratulations!

Your CivicFix backend is now deployed on AWS EC2 with:
- ✅ **High Availability** with systemd service management
- ✅ **Security** with Nginx reverse proxy and SSL
- ✅ **Scalability** with Gunicorn workers
- ✅ **Monitoring** with automated health checks
- ✅ **Integration** with AWS RDS and S3
- ✅ **Production Ready** for real users

**Your civic engagement platform is now live and ready to make a difference!** 🌟

---

**Deployment Guide Version**: 1.0  
**Last Updated**: December 2025  
**Status**: Production Ready ✅
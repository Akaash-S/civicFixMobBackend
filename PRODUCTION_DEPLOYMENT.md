# CivicFix Backend - Production Deployment Guide

## 🚀 Production Deployment Overview

This guide covers the complete production deployment process for the CivicFix backend, including configuration, deployment, monitoring, and maintenance.

## 📋 Prerequisites

### System Requirements
- **Docker**: Version 20.0+ with Docker Compose
- **Python**: 3.11+ (for local development/testing)
- **Memory**: Minimum 2GB RAM, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Outbound internet access for AWS/Firebase

### Required Services
- **AWS RDS**: PostgreSQL database instance
- **AWS S3**: Media file storage bucket
- **Redis**: Cache and rate limiting (AWS ElastiCache recommended)
- **Firebase**: Authentication service

## 🔧 Configuration Setup

### 1. Environment Configuration

Create `.env.production` file with production settings:

```bash
# Copy the template
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

**Critical Settings to Update:**
- `SECRET_KEY`: Generate a strong, unique secret key
- `DATABASE_URL`: Your AWS RDS PostgreSQL connection string
- `REDIS_URL`: Your Redis/ElastiCache endpoint
- `CORS_ORIGINS`: Your frontend domain(s)
- `AWS_*`: Your AWS credentials and region
- `FIREBASE_*`: Your Firebase project configuration

### 2. Firebase Service Account

Place your Firebase service account JSON file as `service-account.json`:

```bash
# Download from Firebase Console > Project Settings > Service Accounts
# Save as service-account.json in the backend directory
```

### 3. Database Setup

Ensure your AWS RDS instance is configured:

```bash
# Test RDS connection
python fix_rds_connection.py

# Run migrations (will be done automatically during deployment)
```

## 🚢 Deployment Process

### Option 1: Automated Deployment (Recommended)

```bash
# Make deployment script executable (Linux/Mac)
chmod +x deploy_production.sh

# Run deployment
./deploy_production.sh

# For Windows
deploy_production.bat
```

### Option 2: Manual Docker Deployment

```bash
# 1. Build the image
docker build -t civicfix/backend:latest .

# 2. Stop existing container
docker stop civicfix-backend-prod || true
docker rm civicfix-backend-prod || true

# 3. Run database migrations
docker run --rm --env-file .env.production civicfix/backend:latest \
  python -c "from app import create_app; from app.config import config; from app.extensions import db; app, _ = create_app(config['production']); app.app_context().push(); db.create_all()"

# 4. Start production container
docker run -d \
  --name civicfix-backend-prod \
  --env-file .env.production \
  -p 5000:5000 \
  --restart unless-stopped \
  --health-cmd="curl -f http://localhost:5000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  civicfix/backend:latest
```

### Option 3: Docker Compose Deployment

```bash
# Use the provided docker-compose.yml
docker-compose -f docker-compose.yml up -d
```

## 📊 Monitoring & Health Checks

### Automated Monitoring

```bash
# Run continuous monitoring (checks every 60 seconds)
python monitor_production.py continuous

# Run single health check
python monitor_production.py check

# View container logs
python monitor_production.py logs 100
```

### Manual Health Checks

```bash
# Application health
curl http://localhost:5000/health

# Container status
docker ps -f name=civicfix-backend-prod

# Container logs
docker logs civicfix-backend-prod --tail 50

# Container stats
docker stats civicfix-backend-prod --no-stream
```

### Key Metrics to Monitor

- **Response Time**: Health endpoint should respond < 1s
- **Memory Usage**: Should stay below 80% of allocated memory
- **CPU Usage**: Should average below 70%
- **Error Rate**: Should be < 1% of total requests
- **Database Connections**: Monitor connection pool usage

## 🔄 Maintenance Operations

### Updating the Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and redeploy
./deploy_production.sh

# 3. Verify deployment
python monitor_production.py check
```

### Database Migrations

```bash
# Run migrations manually
docker exec civicfix-backend-prod python -c "
from app import create_app
from app.config import config
from app.extensions import db
app, _ = create_app(config['production'])
with app.app_context():
    db.create_all()
"
```

### Log Management

```bash
# View application logs
docker logs civicfix-backend-prod

# View monitoring logs
tail -f logs/monitor.log

# View alert logs
tail -f logs/alerts.log

# Rotate logs (prevent disk space issues)
docker logs civicfix-backend-prod --since 24h > logs/app-$(date +%Y%m%d).log
```

### Backup Operations

```bash
# Database backup (run from RDS management console or CLI)
aws rds create-db-snapshot \
  --db-instance-identifier civicfix-db \
  --db-snapshot-identifier civicfix-backup-$(date +%Y%m%d)

# S3 backup (automatic with versioning enabled)
# Configure S3 lifecycle policies for cost optimization
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs for errors
docker logs civicfix-backend-prod

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Port already in use
# - Insufficient memory
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
python fix_rds_connection.py

# Check security groups
# Verify RDS endpoint and credentials
# Ensure RDS is publicly accessible (if needed)
```

#### 3. High Memory Usage
```bash
# Check memory stats
docker stats civicfix-backend-prod

# Restart container to free memory
docker restart civicfix-backend-prod

# Consider increasing container memory limits
```

#### 4. Slow Response Times
```bash
# Check database performance
# Monitor Redis connectivity
# Review application logs for bottlenecks
# Consider scaling horizontally
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Stop current container
docker stop civicfix-backend-prod

# Start previous version (if available)
docker run -d --name civicfix-backend-prod-rollback \
  --env-file .env.production \
  -p 5000:5000 \
  civicfix/backend:previous-tag
```

#### Scale Horizontally
```bash
# Run multiple instances behind a load balancer
docker run -d --name civicfix-backend-prod-2 \
  --env-file .env.production \
  -p 5001:5000 \
  civicfix/backend:latest
```

## 📈 Performance Optimization

### Production Tuning

1. **Database Connection Pooling**
   - Pool size: 20 connections
   - Max overflow: 10 connections
   - Connection recycling: 1 hour

2. **Gunicorn Configuration**
   - Workers: CPU cores × 2 + 1
   - Worker class: eventlet (for Socket.IO)
   - Timeout: 30 seconds

3. **Redis Configuration**
   - Use AWS ElastiCache for production
   - Enable persistence for rate limiting data
   - Configure appropriate memory limits

4. **AWS S3 Optimization**
   - Enable CloudFront CDN for media files
   - Configure lifecycle policies
   - Use appropriate storage classes

### Scaling Considerations

- **Horizontal Scaling**: Use load balancer with multiple containers
- **Database Scaling**: Consider read replicas for heavy read workloads
- **Cache Scaling**: Use Redis Cluster for high availability
- **CDN**: CloudFront for global content delivery

## 🔐 Security Checklist

- [ ] Strong SECRET_KEY configured
- [ ] Database credentials secured
- [ ] AWS IAM roles with minimal permissions
- [ ] CORS origins restricted to your domains
- [ ] HTTPS enabled (configure reverse proxy)
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery tested

## 📞 Support & Contacts

For production issues:

1. **Check monitoring logs**: `logs/monitor.log`
2. **Review application logs**: `docker logs civicfix-backend-prod`
3. **Run health checks**: `python monitor_production.py check`
4. **Check AWS service status**: AWS Console
5. **Escalate if needed**: Contact system administrator

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Environment**: Production
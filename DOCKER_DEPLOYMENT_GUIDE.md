# CivicFix Backend - Docker Deployment Guide

## 🎯 Overview
Docker deployment for CivicFix backend with AWS RDS and S3 integration.

## 📋 Prerequisites
- Docker and Docker Compose installed
- AWS RDS PostgreSQL database configured
- AWS S3 bucket created
- AWS IAM user with appropriate permissions
- Environment variables configured

## 🔧 Configuration Files

### Docker Files
- `Dockerfile` - Main application container with AWS validation
- `Dockerfile.validator` - Standalone AWS validation container
- `docker-compose.yml` - Full stack (Backend + Nginx)
- `docker-compose.simple.yml` - Backend only (for testing)

### Environment Files
- `.env` - Your actual configuration (copy from .env-clean)
- `.env-clean` - Template with all required variables
- `.env.docker` - Docker-specific template

### Scripts
- `startup.sh` - Container startup script with validation
- `validate_aws_setup.py` - AWS connectivity validation
- `test-docker-deployment.py` - Docker deployment testing

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env-clean .env

# Edit with your AWS credentials
nano .env
```

### 2. Validate AWS Setup
```bash
# Test AWS connectivity before Docker deployment
python validate_aws_setup.py
```

### 3. Deploy with Docker

#### Option A: Full Stack (Backend + Nginx)
```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Backend Only (for testing)
```bash
# Build and start backend only
docker-compose -f docker-compose.simple.yml up -d --build

# Test directly
curl http://localhost:5000/health
```

### 4. Test Deployment
```bash
# Run comprehensive tests
python test-docker-deployment.py

# Manual health check
curl http://localhost/health  # Full stack
curl http://localhost:5000/health  # Backend only
```

## 🔍 Environment Variables

### Required Variables
```env
# Flask Configuration
SECRET_KEY=your-super-secret-key
FLASK_ENV=production

# AWS RDS Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_B64=your-base64-credentials
FIREBASE_PROJECT_ID=your-project-id
```

### Optional Variables
```env
# CORS Configuration
CORS_ORIGINS=*

# Container Behavior
SKIP_VALIDATION=false  # Skip AWS validation on startup
RUN_MIGRATION=false    # Run database migration on startup
```

## 🏥 Health Monitoring

### Health Endpoint Response
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",  // AWS RDS status
    "firebase": "disabled", // Firebase status
    "s3": "healthy"        // AWS S3 status
  },
  "version": "2.0.0"
}
```

### Container Health Checks
- **Backend**: `curl -f http://localhost:5000/health`
- **Nginx**: `curl -f http://localhost/health`
- **Intervals**: 30s with 60s startup period

## 🔧 Management Commands

### Container Management
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Check container status
docker-compose ps
```

### AWS Validation
```bash
# Validate AWS setup
python validate_aws_setup.py

# Run database migration
python migrate_database.py

# Test API endpoints
python test-api-endpoints.py
```

## 🐛 Troubleshooting

### Common Issues

#### 1. AWS Validation Fails
```bash
# Check environment variables
cat .env

# Test AWS connectivity
python validate_aws_setup.py

# Skip validation temporarily
export SKIP_VALIDATION=true
docker-compose restart
```

#### 2. Container Won't Start
```bash
# Check container logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep AWS

# Rebuild container
docker-compose up -d --build --force-recreate
```

#### 3. Health Check Fails
```bash
# Test direct backend connection
curl http://localhost:5000/health

# Check AWS services
docker-compose exec backend python validate_aws_setup.py

# View detailed logs
docker-compose logs --tail=50 backend
```

#### 4. Database Connection Issues
```bash
# Test RDS connectivity
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful')
"

# Run migration
export RUN_MIGRATION=true
docker-compose restart backend
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate AWS credentials regularly

### Container Security
- Containers run as non-root user
- No unnecessary ports exposed
- Health checks prevent unhealthy containers

### AWS Security
- Use least-privilege IAM policies
- Enable RDS encryption
- Configure S3 bucket policies properly

## 📊 Performance Tuning

### Container Resources
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

### Database Optimization
- Use connection pooling
- Configure appropriate instance size
- Monitor RDS performance metrics

### S3 Optimization
- Use appropriate storage class
- Configure lifecycle policies
- Enable CloudFront for static assets

## 🎉 Production Deployment

### AWS EC2 Deployment
```bash
# On EC2 instance
git clone <your-repo>
cd backend

# Configure environment
cp .env-clean .env
nano .env

# Deploy
chmod +x deploy-aws-ec2.sh
./deploy-aws-ec2.sh
```

### Monitoring Setup
- Configure CloudWatch logs
- Set up health check alarms
- Monitor container metrics

---

**🚀 Your CivicFix backend is now ready for Docker deployment with full AWS integration!**
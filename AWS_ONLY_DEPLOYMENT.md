# 🚀 CivicFix Backend - AWS-Only Deployment Guide

**This application requires AWS RDS PostgreSQL and S3 - no local database options**

---

## ⚠️ IMPORTANT: AWS Requirements

This application has been configured to **ONLY** work with:
- **AWS RDS PostgreSQL** (database)
- **AWS S3** (file storage)
- **Firebase** (authentication)

**SQLite and local storage are NOT supported.**

---

## 📋 Prerequisites

### AWS Services Required
- [ ] **AWS RDS PostgreSQL instance** (running and accessible)
- [ ] **AWS S3 bucket** (created and configured)
- [ ] **AWS IAM user** with S3 and RDS permissions
- [ ] **Firebase project** with service account

### Server Requirements
- [ ] **Ubuntu 20.04+** or **Amazon Linux 2**
- [ ] **Minimum 2GB RAM** (4GB recommended)
- [ ] **2 vCPUs minimum**
- [ ] **20GB storage minimum**
- [ ] **Docker and Docker Compose installed**

---

## 🛠️ Step 1: AWS Setup

### 1.1 Create RDS PostgreSQL Instance
```bash
# Using AWS CLI (or use AWS Console)
aws rds create-db-instance \
    --db-instance-identifier civicfix-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username civicfix_admin \
    --master-user-password YOUR_SECURE_PASSWORD \
    --allocated-storage 20 \
    --db-name civicfix_db \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --publicly-accessible
```

### 1.2 Create S3 Bucket
```bash
# Create S3 bucket
aws s3 mb s3://your-civicfix-bucket --region us-east-1

# Configure bucket policy for private access
aws s3api put-public-access-block \
    --bucket your-civicfix-bucket \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 1.3 Create IAM User
```bash
# Create IAM user
aws iam create-user --user-name civicfix-app

# Create access key
aws iam create-access-key --user-name civicfix-app

# Attach S3 policy
aws iam attach-user-policy \
    --user-name civicfix-app \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

---

## 🔐 Step 2: Configure Environment

### 2.1 Create Production Environment File
```bash
# Copy template
cp .env.example .env.production

# Edit with your AWS credentials
nano .env.production
```

### 2.2 Required Configuration
```env
# Flask Configuration
SECRET_KEY=<generate-with-python3 -c "import secrets; print(secrets.token_hex(32))">

# Database Configuration - AWS RDS PostgreSQL REQUIRED
DATABASE_URL=postgresql://civicfix_admin:YOUR_PASSWORD@your-rds-endpoint.rds.amazonaws.com:5432/civicfix_db
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=civicfix_db
DB_USER=civicfix_admin
DB_PASSWORD=YOUR_SECURE_PASSWORD

# AWS Configuration - S3 REQUIRED
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-civicfix-bucket

# Firebase Configuration - REQUIRED
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id
```

### 2.3 Add Firebase Service Account
```bash
# Download from Firebase Console:
# Project Settings → Service Accounts → Generate new private key
# Save as service-account.json
```

---

## 🚀 Step 3: Deploy

### 3.1 Validate Configuration
```bash
# The deployment script will validate your configuration
./docker-deploy.sh deploy

# It will check for:
# - PostgreSQL DATABASE_URL format
# - AWS credentials (no placeholders)
# - Firebase service account file
# - Generated SECRET_KEY
```

### 3.2 Expected Validation
The deployment will **FAIL** if:
- DATABASE_URL doesn't start with `postgresql://`
- AWS credentials contain `your-` placeholders
- S3 bucket is not accessible
- RDS database is not reachable

### 3.3 Successful Deployment
```bash
# If all validations pass:
./docker-deploy.sh deploy

# Expected output:
# [INFO] AWS S3 initialized successfully with bucket: your-bucket
# [INFO] Database connected and tables created
# [INFO] Production container started successfully ✓
```

---

## 🔍 Step 4: Verification

### 4.1 Check Application Health
```bash
# Health check should show all services
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-12-20T...",
  "version": "1.0.0",
  "database": "connected",
  "aws_s3": "available",
  "firebase": "initialized"
}
```

### 4.2 Test Database Connection
```bash
# Check database tables were created
docker exec civicfix-backend-prod python -c "
from app import create_app
from app.extensions import db
app, _ = create_app()
with app.app_context():
    print('Tables:', db.engine.table_names())
"
```

### 4.3 Test S3 Connection
```bash
# Check S3 bucket access
docker exec civicfix-backend-prod python -c "
from app import create_app
app, _ = create_app()
with app.app_context():
    print('S3 Available:', app.aws_service.is_available())
"
```

---

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Test RDS connectivity from server
telnet your-rds-endpoint.rds.amazonaws.com 5432

# Check RDS security group allows your server IP
# Port 5432 must be open from your EC2 instance
```

### S3 Access Issues
```bash
# Test S3 access with AWS CLI
aws s3 ls s3://your-civicfix-bucket

# Check IAM permissions
aws iam list-attached-user-policies --user-name civicfix-app
```

### Common Error Messages

#### "Database configuration required!"
- Ensure DATABASE_URL is set and starts with `postgresql://`
- Check RDS instance is running and accessible

#### "AWS configuration required!"
- Ensure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME are set
- Remove any `your-` placeholder values

#### "AWS access denied"
- Check IAM user has S3 permissions
- Verify access keys are correct
- Ensure S3 bucket exists and is accessible

#### "Only PostgreSQL databases are supported"
- DATABASE_URL must start with `postgresql://`
- SQLite URLs (`sqlite://`) are not allowed

---

## 📊 Monitoring

### Application Logs
```bash
# View application logs
docker-compose logs -f civicfix-backend

# Check for AWS/Database errors
docker-compose logs civicfix-backend | grep -E "(ERROR|AWS|Database)"
```

### AWS CloudWatch
- Monitor RDS performance and connections
- Set up S3 access logging
- Create CloudWatch alarms for errors

### Database Monitoring
```bash
# Check database connections
docker exec civicfix-backend-prod python -c "
from app import create_app
from app.extensions import db
app, _ = create_app()
with app.app_context():
    print('DB Pool Status:', db.engine.pool.status())
"
```

---

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart (preserves data)
./docker-deploy.sh update
```

### Database Migrations
```bash
# Run database migrations
docker exec civicfix-backend-prod python -c "
from app import create_app
from app.extensions import db
app, _ = create_app()
with app.app_context():
    db.create_all()
    print('Database updated')
"
```

### Backup Strategy
- **RDS**: Use automated backups and snapshots
- **S3**: Enable versioning and cross-region replication
- **Application**: Regular container image backups

---

## ✅ Success Checklist

After deployment, verify:

- [ ] **RDS Connected**: Database tables created successfully
- [ ] **S3 Available**: File upload/download working
- [ ] **Firebase Ready**: Authentication service initialized
- [ ] **Health Check**: `/health` endpoint returns 200
- [ ] **No SQLite**: Application only uses PostgreSQL
- [ ] **AWS Required**: Application fails gracefully if AWS unavailable
- [ ] **Monitoring**: Logs show successful AWS/DB connections

---

## 🎯 Production Ready

Your CivicFix backend is now:
- ✅ **AWS-native**: Uses only AWS RDS and S3
- ✅ **Scalable**: PostgreSQL handles concurrent users
- ✅ **Reliable**: No local file storage dependencies
- ✅ **Secure**: Proper AWS IAM permissions
- ✅ **Monitored**: CloudWatch integration ready

**No SQLite fallbacks - AWS is required for operation!**
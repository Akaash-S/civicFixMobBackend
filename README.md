# CivicFix Backend - Clean Production Ready

## 🎯 Overview
Production-ready Flask backend using **AWS RDS PostgreSQL** and **AWS S3** for all environments (development and production).

## 📁 Essential Files
- `app.py` - Main Flask application (AWS-integrated backend)
- `requirements-clean.txt` - Dependencies including boto3
- `Dockerfile` - Production Docker image
- `docker-compose.yml` - AWS-integrated deployment stack
- `nginx-clean.conf` - Reverse proxy configuration
- `deploy-aws-ec2.sh` - Automated AWS EC2 deployment
- `test-api-endpoints.py` - API testing script
- `verify-deployment.py` - Deployment verification script
- `AWS_SETUP_GUIDE.md` - Complete AWS setup guide
- `.env-clean` - Environment template (all variables required)

## 🚀 Quick Start

### Prerequisites
- AWS Account with RDS and S3 configured
- AWS credentials (Access Key ID and Secret Access Key)
- PostgreSQL database on AWS RDS
- S3 bucket for file storage

### Local Development
```bash
# Copy and configure environment
cp .env-clean .env
# Edit .env with your AWS credentials and endpoints

# Install dependencies
pip install -r requirements-clean.txt

# Run application
python app.py

# Test all endpoints
python test-api-endpoints.py
```

### Docker Deployment
```bash
docker-compose up -d --build
curl http://localhost/health
python verify-deployment.py http://localhost
```

### AWS EC2 Deployment
```bash
chmod +x deploy-aws-ec2.sh
./deploy-aws-ec2.sh
python verify-deployment.py http://your-ec2-ip
```

## 🔧 Environment Setup
**All environment variables are REQUIRED** - no fallbacks to local services.

### Required AWS Configuration
- `SECRET_KEY` - Generate secure key (required)
- `DATABASE_URL` - AWS RDS PostgreSQL connection string (required)
- `AWS_ACCESS_KEY_ID` - AWS access key (required)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (required)
- `AWS_S3_BUCKET_NAME` - S3 bucket for file storage (required)
- `AWS_REGION` - AWS region (required, e.g., us-east-1)

### Required Firebase Configuration
- `FIREBASE_SERVICE_ACCOUNT_B64` - Base64 Firebase credentials (required)
- `FIREBASE_PROJECT_ID` - Firebase project ID (required)

### Optional Configuration
- `CORS_ORIGINS` - Allowed origins (default: *)
- `FLASK_ENV` - Environment mode (development/production)

### AWS Setup Required
1. **RDS PostgreSQL Database**
   - Create RDS PostgreSQL instance
   - Configure security groups for access
   - Get connection string for DATABASE_URL

2. **S3 Bucket**
   - Create S3 bucket for file storage
   - Configure bucket policy for public read access
   - Set up CORS policy for web uploads

3. **IAM User**
   - Create IAM user with S3 and RDS permissions
   - Generate access keys
   - Update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

**⚠️ Important:** The application will not start without proper AWS configuration.

## 📚 API Documentation

### Core Endpoints
- `GET /` - Home endpoint with API info
- `GET /health` - Health check with service status

### Issue Management
- `GET /api/v1/issues` - List issues (pagination, filtering)
- `POST /api/v1/issues` - Create issue (auth required)
- `GET /api/v1/issues/{id}` - Get specific issue
- `PUT /api/v1/issues/{id}` - Update issue (auth required)
- `DELETE /api/v1/issues/{id}` - Delete issue (auth required)
- `PUT /api/v1/issues/{id}/status` - Update issue status (auth required)
- `GET /api/v1/issues/nearby` - Get nearby issues (lat, lng, radius)

### File Upload (AWS S3)
- `POST /api/v1/upload` - Upload single file (auth required)
- `POST /api/v1/upload/multiple` - Upload multiple files (auth required)

### User Management
- `GET /api/v1/users/me` - Get current user (auth required)
- `PUT /api/v1/users/me` - Update user profile (auth required)
- `GET /api/v1/users/{id}/issues` - Get user's issues

### Utility Endpoints
- `GET /api/v1/categories` - Available issue categories
- `GET /api/v1/status-options` - Available status options
- `GET /api/v1/priority-options` - Available priority options
- `GET /api/v1/stats` - System statistics

### Query Parameters
- `page` - Page number for pagination
- `per_page` - Items per page (max 100)
- `category` - Filter by category
- `status` - Filter by status
- `latitude`, `longitude`, `radius` - For nearby search

### Authentication
- Header: `Authorization: Bearer <firebase-token>`
- Firebase Authentication with fallback for development

## ✅ Features
- **AWS-First Architecture** - No local fallbacks, cloud-native design
- **AWS RDS PostgreSQL** - Production database for all environments
- **AWS S3 File Storage** - Scalable image storage with public URLs
- Complete REST API for CivicFix
- Firebase Authentication integration
- Docker containerization with health checks
- Nginx reverse proxy with rate limiting
- CORS configuration for frontend integration
- **Multi-image support** for issues
- **File upload validation** (type, size limits)
- **Environment validation** - Fails fast if AWS not configured
- Comprehensive error handling and logging
- Production-ready security headers

## 🎉 Ready for Production!
All tests passing, Docker configured, AWS deployment ready.
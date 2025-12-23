# CivicFix Backend - Clean Production Ready

## 🎯 Overview
Clean, single-file Flask backend ready for AWS EC2 Docker deployment.

## 📁 Essential Files
- `app.py` - Main Flask application (complete backend)
- `requirements-clean.txt` - Minimal dependencies
- `Dockerfile` - Production Docker image
- `docker-compose.yml` - Full deployment stack
- `nginx-clean.conf` - Reverse proxy configuration
- `deploy-aws-ec2.sh` - Automated AWS EC2 deployment
- `test-api-endpoints.py` - API testing script
- `verify-deployment.py` - Deployment verification script
- `.env-clean` - Environment template

## 🚀 Quick Start

### Local Development
```bash
python app.py
python test-api-endpoints.py  # Test all endpoints
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
Copy `.env-clean` to `.env` and update with your values:
- `SECRET_KEY` - Generate secure key
- `DB_PASSWORD` - Database password
- `FIREBASE_SERVICE_ACCOUNT_B64` - Base64 Firebase credentials
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `CORS_ORIGINS` - Allowed origins (comma-separated or *)

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
- Complete REST API for CivicFix
- Firebase Authentication with mock fallback
- PostgreSQL database with SQLAlchemy ORM
- Docker containerization with health checks
- Nginx reverse proxy with rate limiting
- CORS configuration for frontend integration
- Comprehensive error handling
- Logging and monitoring
- Production-ready security headers

## 🎉 Ready for Production!
All tests passing, Docker configured, AWS deployment ready.
# 🚀 CivicFix Backend - Render Deployment Guide

## Overview
This guide will help you deploy your CivicFix backend to Render.com as a native Python Flask application (no Docker required).

---

## 📋 Prerequisites

### ✅ Render Account Setup
1. **Create Render account**: Go to [render.com](https://render.com) and sign up
2. **Connect GitHub**: Link your GitHub account to Render
3. **Push code to GitHub**: Ensure your backend code is in a GitHub repository

### ✅ External Services Required
1. **PostgreSQL Database**: Use Render PostgreSQL or external provider
2. **AWS S3 Bucket**: For file storage (required)
3. **Firebase Project**: For authentication (required)

---

## 🔧 Step 1: Prepare Your Code for Render

### 1.1 Required Files (Already Created)
Your backend now includes these Render-specific files:

- ✅ **`build.sh`** - Build script for installing dependencies
- ✅ **`start.sh`** - Start script for running the application
- ✅ **`render.yaml`** - Render service configuration
- ✅ **`runtime.txt`** - Python version specification
- ✅ **`Procfile`** - Alternative process definition
- ✅ **`requirements.txt`** - Python dependencies (optimized)
- ✅ **`gunicorn.conf.py`** - Production server configuration (updated for Render)

### 1.2 Make Scripts Executable
```bash
chmod +x build.sh start.sh
```

---

## 🗄️ Step 2: Set Up Database

### Option A: Use Render PostgreSQL (Recommended)
1. **In Render Dashboard**:
   - Go to "New" → "PostgreSQL"
   - Choose plan (Starter for testing, Standard for production)
   - Name: `civicfix-db`
   - Note the connection details

### Option B: Use External PostgreSQL
- AWS RDS, Google Cloud SQL, or other PostgreSQL provider
- Get the connection string in format: `postgresql://user:password@host:port/database`

---

## 🔐 Step 3: Prepare Environment Variables

### 3.1 Required Environment Variables
You'll need to set these in Render dashboard:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-super-secret-key-32-chars-minimum

# Database (from Render PostgreSQL or external)
DATABASE_URL=postgresql://user:password@host:port/database

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket-name

# Firebase Configuration (inline JSON)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project",...}
FIREBASE_PROJECT_ID=your-firebase-project-id

# Optional: CORS Origins
CORS_ORIGINS=https://your-frontend-domain.com,https://your-app.com
```

### 3.2 Generate Secure SECRET_KEY
```python
# Run this to generate a secure secret key
import secrets
print(secrets.token_hex(32))
```

---

## 🚀 Step 4: Deploy to Render

### Method 1: Using Render Dashboard (Recommended)

#### 4.1 Create Web Service
1. **Go to Render Dashboard** → "New" → "Web Service"
2. **Connect Repository**: Select your GitHub repository
3. **Configure Service**:
   - **Name**: `civicfix-backend`
   - **Environment**: `Python`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your deployment branch)
   - **Build Command**: `./build.sh`
   - **Start Command**: `./start.sh`

#### 4.2 Configure Environment Variables
In the "Environment" section, add all the variables from Step 3.1:

```
FLASK_ENV = production
FLASK_APP = run.py
SECRET_KEY = your-generated-secret-key
DATABASE_URL = your-database-connection-string
AWS_ACCESS_KEY_ID = your-aws-key
AWS_SECRET_ACCESS_KEY = your-aws-secret
AWS_REGION = us-east-1
S3_BUCKET_NAME = your-bucket-name
FIREBASE_SERVICE_ACCOUNT_JSON = {"type":"service_account",...}
FIREBASE_PROJECT_ID = your-firebase-project
```

#### 4.3 Advanced Settings
- **Health Check Path**: `/health`
- **Plan**: Start with "Starter" ($7/month), upgrade to "Standard" for production
- **Auto-Deploy**: Enable for automatic deployments on git push

#### 4.4 Deploy
Click "Create Web Service" - Render will automatically build and deploy your app!

### Method 2: Using render.yaml (Infrastructure as Code)

#### 4.1 Update render.yaml
Edit `render.yaml` with your specific values:

```yaml
services:
  - type: web
    name: civicfix-backend
    env: python
    plan: starter
    buildCommand: "./build.sh"
    startCommand: "./start.sh"
    healthCheckPath: "/health"
    
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        value: your-secret-key
      # ... add other environment variables
```

#### 4.2 Deploy via Git
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

Then in Render dashboard, create service from repository.

---

## ✅ Step 5: Verification

### 5.1 Check Deployment Status
1. **Monitor Build Logs**: Watch the build process in Render dashboard
2. **Check Service Status**: Ensure service shows as "Live"
3. **View Application Logs**: Monitor for any startup errors

### 5.2 Test Your Deployment
```bash
# Replace with your Render URL
curl https://your-app-name.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-XX-XXTXX:XX:XX",
  "version": "1.0.0",
  "services": {
    "database": {"status": "healthy"},
    "aws_s3": {"status": "healthy"},
    "firebase": {"status": "healthy"}
  }
}
```

### 5.3 Test API Endpoints
```bash
# Test basic API
curl https://your-app-name.onrender.com/api/v1/issues

# Test with your mobile app
# Update your mobile app's API base URL to: https://your-app-name.onrender.com
```

---

## 🔧 Step 6: Production Optimization

### 6.1 Upgrade Service Plan
For production, consider upgrading to:
- **Standard Plan** ($25/month): Better performance, more memory
- **Pro Plan** ($85/month): High performance, dedicated resources

### 6.2 Custom Domain
1. **In Render Dashboard**: Go to Settings → Custom Domains
2. **Add Domain**: Enter your domain (e.g., `api.civicfix.com`)
3. **Configure DNS**: Add CNAME record pointing to Render
4. **SSL Certificate**: Render automatically provides SSL

### 6.3 Environment-Specific Configuration
```bash
# Production optimizations
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=gevent
GUNICORN_TIMEOUT=120
FLASK_ENV=production
```

---

## 🔍 Step 7: Monitoring and Maintenance

### 7.1 Monitor Application
- **Render Dashboard**: Built-in metrics and logs
- **Health Checks**: Automatic monitoring via `/health` endpoint
- **Alerts**: Set up notifications for downtime

### 7.2 Log Management
```bash
# View logs in Render dashboard or via CLI
render logs -s your-service-name --tail
```

### 7.3 Database Management
```bash
# Connect to your database
render connect your-database-name

# Run migrations manually if needed
render run -s your-service-name "python -c 'from flask_migrate import upgrade; from app import create_app; app, _ = create_app(); app.app_context().push(); upgrade()'"
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Build Fails
```bash
# Check build logs in Render dashboard
# Common fixes:
# 1. Ensure build.sh is executable
# 2. Check requirements.txt for invalid packages
# 3. Verify Python version in runtime.txt
```

#### Application Won't Start
```bash
# Check start logs
# Common fixes:
# 1. Verify all environment variables are set
# 2. Check database connection string
# 3. Ensure start.sh is executable
```

#### Database Connection Issues
```bash
# Verify DATABASE_URL format
# Should be: postgresql://user:password@host:port/database
# Check if database is running and accessible
```

#### Firebase Authentication Issues
```bash
# Verify FIREBASE_SERVICE_ACCOUNT_JSON is valid JSON
# Check FIREBASE_PROJECT_ID matches your Firebase project
# Ensure Firebase service account has proper permissions
```

---

## 📊 Performance Tips

### 7.1 Optimize for Render
```python
# In gunicorn.conf.py (already configured)
workers = 2  # Optimal for Render Starter plan
worker_class = "gevent"  # Better memory usage
timeout = 120  # Allow time for initialization
```

### 7.2 Database Optimization
```python
# Connection pooling (already configured in config.py)
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True
}
```

### 7.3 Caching Strategy
```python
# Consider adding Redis for caching (optional)
# Render offers Redis add-on
```

---

## 🎉 Deployment Complete!

Your CivicFix backend is now deployed on Render! 

### 🔗 Your Application URLs:
- **API Base**: `https://your-app-name.onrender.com`
- **Health Check**: `https://your-app-name.onrender.com/health`
- **API Documentation**: `https://your-app-name.onrender.com/api/v1/`

### 📱 Update Your Mobile App:
Update your mobile app's API configuration to use:
```
API_BASE_URL = "https://your-app-name.onrender.com"
```

### 🔄 Continuous Deployment:
Every time you push to your main branch, Render will automatically:
1. Build your application
2. Run tests (if configured)
3. Deploy the new version
4. Perform health checks

---

## 📞 Support Resources

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)

**Your CivicFix backend is now live and ready to serve your mobile application!** 🚀📱
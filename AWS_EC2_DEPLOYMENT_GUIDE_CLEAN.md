# 🚀 CivicFix Backend - Clean AWS EC2 Docker Deployment

## Overview
This is a completely rewritten, clean, and production-ready CivicFix backend designed for reliable deployment on AWS EC2 with Docker.

## ✨ What's New - Clean Architecture

### **🔧 Simplified Structure**
- **Single file application** (`app.py`) - Easy to understand and maintain
- **Minimal dependencies** - Only essential packages
- **Clean Docker setup** - Optimized for production
- **Reliable authentication** - Firebase with Base64 encoding
- **Simple database models** - User and Issue entities

### **📦 Clean Files**
- ✅ **`app.py`** - Complete Flask application in one file
- ✅ **`requirements-clean.txt`** - Minimal, reliable dependencies
- ✅ **`Dockerfile-clean`** - Optimized Docker configuration
- ✅ **`docker-compose-clean.yml`** - Complete stack with PostgreSQL and Nginx
- ✅ **`nginx-clean.conf`** - Production-ready reverse proxy
- ✅ **`.env-clean`** - Environment template
- ✅ **`deploy-aws-ec2.sh`** - Automated deployment script

---

## 🚀 Quick Deployment Steps

### **Step 1: Launch AWS EC2 Instance**
1. **Launch Ubuntu 22.04 LTS** instance
2. **Instance type**: t3.medium or larger (recommended)
3. **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 5000 (Backend)
4. **Storage**: 20GB minimum
5. **Key Pair**: Create or use existing for SSH access

### **Step 2: Connect to EC2 Instance**
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### **Step 3: Clone and Deploy**
```bash
# Clone your repository
git clone https://github.com/your-username/your-repo.git
cd your-repo/backend

# Make deployment script executable
chmod +x deploy-aws-ec2.sh

# Run deployment (this will install Docker and deploy everything)
./deploy-aws-ec2.sh
```

### **Step 4: Configure Environment**
```bash
# Edit environment file with your credentials
nano .env

# Update these values:
SECRET_KEY=your-super-secret-key-generate-with-python-secrets
DB_PASSWORD=your-strong-database-password
FIREBASE_SERVICE_ACCOUNT_B64=your-base64-encoded-firebase-credentials
FIREBASE_PROJECT_ID=your-firebase-project-id

# Restart services
docker-compose -f docker-compose-clean.yml restart
```

### **Step 5: Verify Deployment**
```bash
# Check service status
docker-compose -f docker-compose-clean.yml ps

# Test health endpoint
curl http://localhost/health

# Test API
curl http://your-ec2-public-ip/api/v1/categories
```

---

## 🔧 Manual Deployment (If Script Fails)

### **Install Docker**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in, or run:
newgrp docker
```

### **Deploy Application**
```bash
# Create environment file
cp .env-clean .env
nano .env  # Update with your values

# Deploy with Docker Compose
docker-compose -f docker-compose-clean.yml up -d --build

# Check status
docker-compose -f docker-compose-clean.yml ps
```

---

## 🔐 Firebase Configuration

### **Convert Service Account to Base64**
```bash
# On your local machine, convert Firebase service account
base64 -i service-account.json -o firebase.b64

# Copy the Base64 string and set in .env
FIREBASE_SERVICE_ACCOUNT_B64=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50...
```

### **Alternative: Use Python Script**
```bash
# Use the conversion script
python convert-firebase-to-base64.py service-account.json
```

---

## 🌐 API Endpoints

### **Core Endpoints**
- **GET** `/` - Home/status
- **GET** `/health` - Health check
- **GET** `/api/v1/categories` - Issue categories

### **Issue Management**
- **GET** `/api/v1/issues` - List issues (with pagination)
- **POST** `/api/v1/issues` - Create issue (requires auth)
- **GET** `/api/v1/issues/{id}` - Get specific issue
- **PUT** `/api/v1/issues/{id}/status` - Update issue status (requires auth)

### **User Management**
- **GET** `/api/v1/users/me` - Get current user (requires auth)
- **PUT** `/api/v1/users/me` - Update user profile (requires auth)

### **Authentication**
All protected endpoints require:
```
Authorization: Bearer YOUR_FIREBASE_ID_TOKEN
```

---

## 🔍 Testing Your Deployment

### **Health Check**
```bash
curl http://your-ec2-ip/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-XX-XXTXX:XX:XX",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "firebase": "healthy"
  }
}
```

### **Create Issue (with Authentication)**
```bash
curl -X POST http://your-ec2-ip/api/v1/issues \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Issue",
    "category": "Pothole",
    "description": "Test issue description",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "address": "New York, NY"
  }'
```

### **List Issues**
```bash
curl http://your-ec2-ip/api/v1/issues
```

---

## 🔧 Management Commands

### **View Logs**
```bash
# All services
docker-compose -f docker-compose-clean.yml logs -f

# Specific service
docker-compose -f docker-compose-clean.yml logs -f backend
```

### **Restart Services**
```bash
# Restart all
docker-compose -f docker-compose-clean.yml restart

# Restart specific service
docker-compose -f docker-compose-clean.yml restart backend
```

### **Update Application**
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose-clean.yml up -d --build
```

### **Stop Services**
```bash
docker-compose -f docker-compose-clean.yml down
```

### **Database Access**
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose-clean.yml exec postgres psql -U civicfix -d civicfix
```

---

## 🛡️ Security Configuration

### **Firewall Setup**
```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **SSL Certificate (Optional)**
```bash
# Install Certbot
sudo apt install certbot

# Get SSL certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com

# Update nginx configuration to use SSL
```

---

## 📊 Monitoring

### **Check System Resources**
```bash
# Docker stats
docker stats

# System resources
htop
df -h
```

### **Application Monitoring**
```bash
# Check container health
docker-compose -f docker-compose-clean.yml ps

# Monitor logs
docker-compose -f docker-compose-clean.yml logs -f --tail=100
```

---

## 🚨 Troubleshooting

### **Common Issues**

#### **Docker Permission Denied**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### **Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :80

# Kill the process or change port in docker-compose
```

#### **Database Connection Failed**
```bash
# Check PostgreSQL container
docker-compose -f docker-compose-clean.yml logs postgres

# Restart database
docker-compose -f docker-compose-clean.yml restart postgres
```

#### **Firebase Authentication Issues**
```bash
# Check Firebase configuration
docker-compose -f docker-compose-clean.yml logs backend | grep -i firebase

# Verify Base64 encoding
echo $FIREBASE_SERVICE_ACCOUNT_B64 | base64 -d | python -m json.tool
```

---

## 🎯 Production Checklist

### **Before Going Live**
- [ ] **Strong SECRET_KEY** generated
- [ ] **Secure DB_PASSWORD** set
- [ ] **Valid Firebase credentials** configured
- [ ] **Firewall** properly configured
- [ ] **SSL certificate** installed (for HTTPS)
- [ ] **Domain name** configured
- [ ] **Backup strategy** implemented
- [ ] **Monitoring** set up

### **Performance Optimization**
- [ ] **Instance size** appropriate for load
- [ ] **Database** optimized
- [ ] **Nginx** caching configured
- [ ] **Log rotation** set up
- [ ] **Resource limits** configured

---

## 🎉 Success!

Your CivicFix backend is now running on AWS EC2 with Docker!

### **Access Your API**
- **Base URL**: `http://your-ec2-public-ip`
- **Health Check**: `http://your-ec2-public-ip/health`
- **API Documentation**: Available at all endpoints

### **Next Steps**
1. **Configure your mobile app** to use the new API URL
2. **Set up SSL certificate** for HTTPS
3. **Configure domain name** (optional)
4. **Set up monitoring and backups**
5. **Test all functionality** with your mobile app

**Your clean, production-ready CivicFix backend is now live!** 🚀
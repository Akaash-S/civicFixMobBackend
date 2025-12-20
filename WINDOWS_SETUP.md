# CivicFix Backend - Windows Setup Guide

Complete guide to set up the CivicFix backend on Windows with AWS RDS.

## 🚀 Quick Setup (Recommended)

### Option 1: Using Batch Script (CMD)

1. **Open Command Prompt as Administrator**
2. **Navigate to backend directory**:
   ```cmd
   cd D:\Projects\Android\civicFix\backend
   ```

3. **Run setup script**:
   ```cmd
   setup_windows.bat
   ```

### Option 2: Using PowerShell Script

1. **Open PowerShell as Administrator**
2. **Enable script execution** (first time only):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Navigate to backend directory**:
   ```powershell
   cd D:\Projects\Android\civicFix\backend
   ```

4. **Run setup script**:
   ```powershell
   .\setup_windows.ps1
   ```

## 📋 What the Setup Script Does

✅ Checks Python installation  
✅ Creates virtual environment  
✅ Installs all dependencies  
✅ Tests Flask installation  
✅ Creates startup scripts  

## 🔧 Manual Setup (If Scripts Fail)

### Step 1: Install Python

1. Download Python 3.8+ from https://python.org
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Create Virtual Environment

```cmd
cd D:\Projects\Android\civicFix\backend
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment

1. Copy `.env.example` to `.env`:
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` file with your AWS RDS credentials:
   ```env
   DATABASE_URL=postgresql://civicfix_user:your_password@your-rds-endpoint.amazonaws.com:5432/civicfix
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   S3_BUCKET_NAME=civicfix-media-uploads
   FIREBASE_PROJECT_ID=your-firebase-project-id
   ```

### Step 6: Initialize Database

```cmd
python init_database.py
```

### Step 7: Start Backend

```cmd
python run.py
```

## 🗄️ AWS RDS Setup

### Option 1: Automatic Setup

```cmd
python setup_aws_rds.py
```

This will:
- Create RDS PostgreSQL instance
- Configure security groups
- Update .env file automatically

### Option 2: Manual RDS Setup

1. **Go to AWS Console** → RDS → Create Database

2. **Configuration**:
   - Engine: PostgreSQL 15.4
   - Template: Free tier
   - DB instance identifier: `civicfix-db`
   - Master username: `civicfix_user`
   - Master password: (your choice)
   - DB instance class: `db.t3.micro`
   - Storage: 20 GB
   - Public access: Yes

3. **Security Group**:
   - Add inbound rule: PostgreSQL (port 5432)
   - Source: 0.0.0.0/0 (or your IP)

4. **Update .env file** with RDS endpoint:
   ```env
   DATABASE_URL=postgresql://civicfix_user:your_password@your-rds-endpoint.amazonaws.com:5432/civicfix
   ```

## 🔥 Common Issues & Solutions

### Issue 1: "Python not found"

**Solution**:
1. Reinstall Python from https://python.org
2. Check "Add Python to PATH" during installation
3. Restart Command Prompt/PowerShell

### Issue 2: "Cannot run scripts" (PowerShell)

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 3: "pip is not recognized"

**Solution**:
```cmd
python -m pip install --upgrade pip
```

### Issue 4: "Virtual environment activation fails"

**Solution**:
```cmd
# Delete and recreate
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate.bat
```

### Issue 5: "Database connection refused"

**Solutions**:
1. Check RDS security group allows port 5432
2. Verify RDS endpoint in .env file
3. Ensure RDS instance is running
4. Check VPC and subnet configuration

### Issue 6: "Module not found" errors

**Solution**:
```cmd
# Ensure virtual environment is activated
venv\Scripts\activate.bat

# Reinstall dependencies
pip install -r requirements.txt
```

## 🧪 Testing the Setup

### 1. Test Python Installation
```cmd
python --version
```

### 2. Test Virtual Environment
```cmd
venv\Scripts\activate.bat
python -c "import sys; print(sys.prefix)"
```

### 3. Test Flask Installation
```cmd
python -c "import flask; print('Flask version:', flask.__version__)"
```

### 4. Test Database Connection
```cmd
python -c "from app import create_app; from app.config import DevelopmentConfig; app, socketio = create_app(DevelopmentConfig); print('App created successfully')"
```

### 5. Test Health Endpoint
```cmd
# Start server in one terminal
python run.py

# In another terminal
curl http://localhost:5000/health
```

## 📁 Project Structure

```
backend/
├── venv/                      # Virtual environment (created by setup)
├── app/                       # Main application
│   ├── models/               # Database models
│   ├── routes/               # API endpoints
│   ├── services/             # AWS & Firebase services
│   └── utils/                # Helpers
├── logs/                      # Application logs
├── migrations/                # Database migrations
├── .env                       # Configuration (create from .env.example)
├── requirements.txt           # Python dependencies
├── run.py                     # Main entry point
├── setup_windows.bat          # Windows setup script (CMD)
├── setup_windows.ps1          # Windows setup script (PowerShell)
├── start_backend.bat          # Start server (CMD)
├── start_backend.ps1          # Start server (PowerShell)
└── init_database.bat          # Initialize database (CMD)
```

## 🚀 Starting the Backend

### Method 1: Using Batch Script
```cmd
start_backend.bat
```

### Method 2: Using PowerShell Script
```powershell
.\start_backend.ps1
```

### Method 3: Manual Start
```cmd
venv\Scripts\activate.bat
python run.py
```

The server will start on `http://localhost:5000`

## 🔒 AWS Configuration

### AWS Credentials

Set up AWS credentials using one of these methods:

**Method 1: Environment Variables**
```cmd
set AWS_ACCESS_KEY_ID=your-key
set AWS_SECRET_ACCESS_KEY=your-secret
set AWS_DEFAULT_REGION=us-east-1
```

**Method 2: AWS CLI**
```cmd
pip install awscli
aws configure
```

**Method 3: .env File**
```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

## 🔥 Firebase Configuration

1. **Create Firebase Project**:
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Authentication → Google Sign-In

2. **Download Service Account**:
   - Project Settings → Service Accounts
   - Generate new private key
   - Save as `firebase-service-account.json` in backend directory

3. **Update .env**:
   ```env
   FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
   FIREBASE_PROJECT_ID=your-project-id
   ```

## 📊 Database Management

### Initialize Database
```cmd
python init_database.py
```

### Create Migration
```cmd
flask db migrate -m "Description"
```

### Apply Migration
```cmd
flask db upgrade
```

### Rollback Migration
```cmd
flask db downgrade
```

## 🎯 Next Steps

1. ✅ Complete setup using `setup_windows.bat`
2. ✅ Configure `.env` file with AWS RDS credentials
3. ✅ Initialize database with `python init_database.py`
4. ✅ Start backend with `start_backend.bat`
5. ✅ Test API at `http://localhost:5000/health`
6. ✅ Connect your React Native app

## 📞 Support

If you encounter issues:

1. Check the logs in `logs/civicfix.log`
2. Verify all environment variables in `.env`
3. Ensure AWS and Firebase credentials are correct
4. Check Windows Firewall settings
5. Review the error messages carefully

## 🎉 Success Indicators

You'll know the setup is successful when:

✅ Virtual environment activates without errors  
✅ All dependencies install successfully  
✅ Database connection test passes  
✅ Server starts on port 5000  
✅ Health endpoint returns `{"status": "healthy"}`  

---

**CivicFix Backend** - Ready to serve your civic engagement platform on Windows! 🏛️
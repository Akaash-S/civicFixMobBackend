# CivicFix Backend Setup Guide

Complete guide to set up the CivicFix backend with AWS RDS and fix Python path issues.

## 🚀 Quick Setup (Recommended)

### Step 1: Fix Python Environment
```bash
python3 fix_python_path.py
```
This will:
- ✅ Detect correct Python executable
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create run scripts for your platform

### Step 2: Configure AWS RDS (Optional)
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Set up AWS RDS
python setup_aws_rds.py
```

### Step 3: Initialize Database
```bash
python init_database.py
```

### Step 4: Start Backend
```bash
# Use the generated script
./start_backend.sh        # Linux/Mac
start_backend.bat         # Windows

# OR manually
source venv/bin/activate && python run.py
```

## 🔧 Manual Setup

### Prerequisites
- Python 3.8+
- AWS Account (for RDS and S3)
- Firebase Project (for authentication)

### 1. Environment Setup

#### Create Virtual Environment
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. AWS RDS Configuration

#### Option A: Automatic Setup
```bash
python setup_aws_rds.py
```

#### Option B: Manual Configuration
1. **Create RDS Instance**:
   - Engine: PostgreSQL 15.4
   - Instance: db.t3.micro (free tier)
   - Database name: `civicfix`
   - Username: `civicfix_user`
   - Password: (your choice)
   - Public access: Yes
   - Security group: Allow port 5432

2. **Update .env file**:
```env
DATABASE_URL=postgresql://civicfix_user:your_password@your-rds-endpoint.amazonaws.com:5432/civicfix
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432
DB_NAME=civicfix
DB_USER=civicfix_user
DB_PASSWORD=your_password
```

### 3. AWS S3 Configuration

Update your `.env` file:
```env
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=civicfix-media-uploads
```

The backend will automatically create the S3 bucket if it doesn't exist.

### 4. Firebase Configuration

1. **Create Firebase Project**:
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Authentication with Google Sign-In

2. **Generate Service Account**:
   - Project Settings > Service Accounts
   - Generate new private key
   - Save as `firebase-service-account.json` in backend directory

3. **Update .env file**:
```env
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id
```

### 5. Database Initialization

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade

# OR use the initialization script
python init_database.py
```

### 6. Start the Backend

```bash
python run.py
```

The backend will start on `http://localhost:5000`

## 🔍 Troubleshooting

### Python Path Issues

**Error**: `No Python at '"/usr/bin\python.exe'`

**Solution**:
```bash
python3 fix_python_path.py
```

### Database Connection Issues

**Error**: `Connection refused` or `Authentication failed`

**Solutions**:
1. Check RDS security group allows port 5432
2. Verify database credentials in `.env`
3. Ensure RDS instance is publicly accessible
4. Check VPC and subnet configuration

### AWS Credentials Issues

**Error**: `Unable to locate credentials`

**Solutions**:
1. Install AWS CLI: `pip install awscli`
2. Configure credentials: `aws configure`
3. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   ```

### Firebase Issues

**Error**: `Firebase service account not found`

**Solutions**:
1. Download service account JSON from Firebase Console
2. Place in backend directory as `firebase-service-account.json`
3. Update `FIREBASE_PROJECT_ID` in `.env`

## 🧪 Testing the Setup

### 1. Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "CivicFix API"
}
```

### 2. Database Test
```bash
python -c "
from app import create_app
from app.config import DevelopmentConfig
app, socketio = create_app(DevelopmentConfig)
with app.app_context():
    from app.extensions import db
    print('Database connection:', db.engine.execute('SELECT 1').scalar())
"
```

### 3. Run Test Suite
```bash
python test_basic.py
```

## 🚀 Production Deployment

### Environment Variables
Set these in your production environment:
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/civicfix
AWS_ACCESS_KEY_ID=your-production-key
AWS_SECRET_ACCESS_KEY=your-production-secret
S3_BUCKET_NAME=civicfix-prod-uploads
FIREBASE_PROJECT_ID=your-prod-project
SECRET_KEY=your-super-secret-production-key
```

### Docker Deployment
```bash
# Build image
docker build -t civicfix-backend .

# Run with environment file
docker run --env-file .env -p 5000:5000 civicfix-backend
```

### Using Docker Compose
```bash
# Update docker-compose.yml with your credentials
docker-compose up -d
```

## 📊 Monitoring

### Logs
- Console output: Real-time logs
- File logs: `logs/civicfix.log`

### Health Checks
- Endpoint: `GET /health`
- Database: Automatic connection testing
- AWS services: Initialization verification

## 🆘 Getting Help

### Common Commands
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Database operations
flask db init
flask db migrate -m "Description"
flask db upgrade

# Run backend
python run.py

# Run tests
python test_basic.py
```

### Log Files
Check these for debugging:
- `logs/civicfix.log` - Application logs
- Console output - Real-time logs
- Database logs - SQL queries (in development)

### Support
- Check the main README.md for detailed API documentation
- Review error messages in logs
- Ensure all environment variables are set correctly
- Verify AWS and Firebase credentials

---

**CivicFix Backend** - Ready to serve your civic engagement platform! 🏛️
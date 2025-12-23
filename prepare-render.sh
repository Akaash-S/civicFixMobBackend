#!/bin/bash
# CivicFix Backend - Render Preparation Script

echo "🚀 Preparing CivicFix Backend for Render Deployment"
echo "=================================================="

# Make scripts executable
echo "📝 Making scripts executable..."
chmod +x build.sh
chmod +x start.sh
chmod +x prepare-render.sh

# Validate required files
echo "✅ Checking required files..."
required_files=("build.sh" "start.sh" "requirements.txt" "run.py" "gunicorn.conf.py" "runtime.txt")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing files: ${missing_files[*]}"
    exit 1
fi

# Validate Python syntax
echo "🐍 Checking Python syntax..."
if find . -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null; then
    echo "✅ Python syntax check passed"
else
    echo "❌ Python syntax issues found"
    exit 1
fi

# Check requirements.txt
echo "📦 Validating requirements.txt..."
if python3 -c "
import pkg_resources
with open('requirements.txt', 'r') as f:
    requirements = f.read().strip().split('\n')
    requirements = [r for r in requirements if r and not r.startswith('#')]
    for req in requirements:
        try:
            pkg_resources.Requirement.parse(req)
        except Exception as e:
            print(f'Invalid requirement: {req} - {e}')
            exit(1)
print('Requirements validation passed')
"; then
    echo "✅ Requirements.txt is valid"
else
    echo "❌ Requirements.txt has issues"
    exit 1
fi

# Generate example environment variables
echo "🔐 Generating example environment variables..."
cat > .env.render.example << 'EOF'
# CivicFix Backend - Render Environment Variables
# Copy these to your Render dashboard Environment section

# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-super-secret-key-generate-with-secrets-token-hex-32

# Database (from Render PostgreSQL or external)
DATABASE_URL=postgresql://user:password@host:port/database

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# Firebase Configuration (inline JSON - convert your service account file)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"your-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}
FIREBASE_PROJECT_ID=your-firebase-project-id

# Optional Configuration
CORS_ORIGINS=https://your-frontend-domain.com
GUNICORN_WORKERS=2
GUNICORN_WORKER_CLASS=gevent
GUNICORN_TIMEOUT=120
EOF

echo "✅ Created .env.render.example with template environment variables"

# Create deployment checklist
echo "📋 Creating deployment checklist..."
cat > RENDER_DEPLOYMENT_CHECKLIST.md << 'EOF'
# Render Deployment Checklist

## Before Deployment
- [ ] Code pushed to GitHub repository
- [ ] All required files present (build.sh, start.sh, requirements.txt, etc.)
- [ ] Scripts are executable (run prepare-render.sh)
- [ ] Python syntax validated
- [ ] Requirements.txt validated

## Render Setup
- [ ] Render account created and GitHub connected
- [ ] PostgreSQL database created (or external database ready)
- [ ] AWS S3 bucket created and configured
- [ ] Firebase project set up with service account

## Environment Variables (Set in Render Dashboard)
- [ ] FLASK_ENV=production
- [ ] FLASK_APP=run.py
- [ ] SECRET_KEY (generated with secrets.token_hex(32))
- [ ] DATABASE_URL (from Render PostgreSQL or external)
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] AWS_REGION
- [ ] S3_BUCKET_NAME
- [ ] FIREBASE_SERVICE_ACCOUNT_JSON (inline JSON)
- [ ] FIREBASE_PROJECT_ID
- [ ] CORS_ORIGINS (optional)

## Render Service Configuration
- [ ] Service name: civicfix-backend
- [ ] Environment: Python
- [ ] Build command: ./build.sh
- [ ] Start command: ./start.sh
- [ ] Health check path: /health
- [ ] Plan selected (Starter for testing, Standard for production)

## Post-Deployment Verification
- [ ] Service shows as "Live" in Render dashboard
- [ ] Health check endpoint responds: https://your-app.onrender.com/health
- [ ] API endpoints accessible: https://your-app.onrender.com/api/v1/issues
- [ ] Database connection working
- [ ] AWS S3 integration working
- [ ] Firebase authentication working
- [ ] Mobile app updated with new API URL

## Production Optimization (Optional)
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Monitoring and alerts set up
- [ ] Service plan upgraded if needed
- [ ] Performance monitoring enabled
EOF

echo "✅ Created RENDER_DEPLOYMENT_CHECKLIST.md"

# Summary
echo ""
echo "🎉 Render preparation completed successfully!"
echo "=================================================="
echo ""
echo "📁 Files created/updated:"
echo "  ✅ build.sh (executable)"
echo "  ✅ start.sh (executable)"
echo "  ✅ render.yaml"
echo "  ✅ runtime.txt"
echo "  ✅ Procfile"
echo "  ✅ .env.render.example"
echo "  ✅ RENDER_DEPLOYMENT_CHECKLIST.md"
echo "  ✅ gunicorn.conf.py (updated for Render)"
echo ""
echo "🚀 Next Steps:"
echo "  1. Review RENDER_DEPLOYMENT_GUIDE.md for complete instructions"
echo "  2. Check RENDER_DEPLOYMENT_CHECKLIST.md for deployment steps"
echo "  3. Set up your environment variables using .env.render.example"
echo "  4. Push your code to GitHub"
echo "  5. Create a new Web Service in Render dashboard"
echo ""
echo "📖 Full guide: RENDER_DEPLOYMENT_GUIDE.md"
echo "✅ Checklist: RENDER_DEPLOYMENT_CHECKLIST.md"
echo ""
echo "Your CivicFix backend is ready for Render deployment! 🚀"
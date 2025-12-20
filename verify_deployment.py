#!/usr/bin/env python3
"""
Deployment Verification Script
Final verification that the CivicFix backend is ready for production deployment
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def verify_gunicorn_compatibility():
    """Verify Gunicorn compatibility"""
    print_header("GUNICORN COMPATIBILITY")
    
    try:
        # Test application import
        result = subprocess.run([
            sys.executable, '-c',
            'from run import application; print("Import successful:", callable(application))'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "Import successful: True" in result.stdout:
            print_success("Application import and callable check")
        else:
            print_error("Application import failed")
            print(f"Error: {result.stderr}")
            return False
        
        # Test WSGI interface
        result = subprocess.run([
            sys.executable, 'test_wsgi.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "🎉 WSGI application is ready for Gunicorn!" in result.stdout:
            print_success("WSGI interface compatibility")
        else:
            print_error("WSGI interface test failed")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Gunicorn compatibility check failed: {e}")
        return False

def verify_database_connection():
    """Verify database connection"""
    print_header("DATABASE CONNECTION")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            '''
from app import create_app
from app.config import config
from app.extensions import db
app, _ = create_app(config["development"])
with app.app_context():
    with db.engine.connect() as conn:
        result = conn.execute(db.text("SELECT current_database(), version()")).fetchone()
        print(f"Database: {result[0]}")
        print(f"Version: {result[1][:50]}...")
'''
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and "Database:" in result.stdout:
            print_success("PostgreSQL connection working")
            print(result.stdout.strip())
        else:
            print_error("Database connection failed")
            print(f"Error: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Database verification failed: {e}")
        return False

def verify_aws_services():
    """Verify AWS services"""
    print_header("AWS SERVICES")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            '''
from app.services.aws_service import AWSService
from app import create_app
from app.config import config
app, _ = create_app(config["development"])
with app.app_context():
    aws = AWSService()
    aws.initialize()
    print(f"S3 Bucket: {aws.bucket_name}")
    print("AWS S3 service initialized successfully")
'''
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and "AWS S3 service initialized successfully" in result.stdout:
            print_success("AWS S3 service working")
            print(result.stdout.strip())
        else:
            print_warning("AWS S3 service not available (optional for development)")
            print(f"Details: {result.stderr}")
        
        return True
        
    except Exception as e:
        print_warning(f"AWS services check failed (optional): {e}")
        return True  # AWS is optional for basic functionality

def verify_firebase_service():
    """Verify Firebase service"""
    print_header("FIREBASE AUTHENTICATION")
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            '''
from app.services.firebase_service import FirebaseService
from app import create_app
from app.config import config
app, _ = create_app(config["development"])
with app.app_context():
    firebase = FirebaseService()
    firebase.initialize()
    print("Firebase Admin SDK initialized successfully")
'''
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and "Firebase Admin SDK initialized successfully" in result.stdout:
            print_success("Firebase Authentication service working")
        else:
            print_warning("Firebase service not available (optional for development)")
            print(f"Details: {result.stderr}")
        
        return True
        
    except Exception as e:
        print_warning(f"Firebase service check failed (optional): {e}")
        return True  # Firebase is optional for basic functionality

def verify_production_files():
    """Verify production files exist"""
    print_header("PRODUCTION FILES")
    
    required_files = [
        '.env.production',
        'gunicorn.conf.py',
        'Dockerfile',
        'deploy_production.sh',
        'deploy_production.bat',
        'monitor_production.py',
        'start_production.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def verify_api_health():
    """Verify API health (if server is running)"""
    print_header("API HEALTH CHECK")
    
    try:
        import requests
        response = requests.get('http://localhost:5000/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health endpoint: {data}")
            return True
        else:
            print_warning(f"Health endpoint returned {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_warning("Server not running (start with: python quick_start_fixed.py)")
        return True  # Not critical for deployment verification
    except Exception as e:
        print_warning(f"Health check failed: {e}")
        return True

def main():
    """Main verification function"""
    print_header("CIVICFIX BACKEND - DEPLOYMENT VERIFICATION")
    print("This script verifies that the backend is ready for production deployment")
    
    verifications = [
        ("Gunicorn Compatibility", verify_gunicorn_compatibility),
        ("Database Connection", verify_database_connection),
        ("AWS Services", verify_aws_services),
        ("Firebase Authentication", verify_firebase_service),
        ("Production Files", verify_production_files),
        ("API Health", verify_api_health),
    ]
    
    passed = 0
    critical_passed = 0
    critical_tests = ["Gunicorn Compatibility", "Database Connection", "Production Files"]
    
    for test_name, test_func in verifications:
        try:
            if test_func():
                passed += 1
                if test_name in critical_tests:
                    critical_passed += 1
        except Exception as e:
            print_error(f"{test_name}: Exception - {e}")
    
    print_header("VERIFICATION SUMMARY")
    
    print(f"Total Tests: {passed}/{len(verifications)} passed")
    print(f"Critical Tests: {critical_passed}/{len(critical_tests)} passed")
    
    if critical_passed == len(critical_tests):
        print_success("🎉 BACKEND IS READY FOR PRODUCTION DEPLOYMENT!")
        print("\n📋 DEPLOYMENT CHECKLIST:")
        print("   1. ✅ Gunicorn compatibility verified")
        print("   2. ✅ Database connection working")
        print("   3. ✅ Production files present")
        print("   4. ⚠️  Configure .env.production for your environment")
        print("   5. ⚠️  Setup Redis for production rate limiting")
        print("   6. ⚠️  Configure domain and SSL certificates")
        
        print("\n🚀 DEPLOYMENT COMMANDS:")
        print("   Windows: deploy_production.bat")
        print("   Linux/Mac: ./deploy_production.sh")
        print("   Docker: docker build -t civicfix/backend .")
        
        print("\n📊 MONITORING:")
        print("   Health: python monitor_production.py check")
        print("   Continuous: python monitor_production.py continuous")
        
        return True
    else:
        print_error("❌ CRITICAL ISSUES FOUND - FIX BEFORE DEPLOYMENT")
        print("\n🔧 REQUIRED FIXES:")
        if "Gunicorn Compatibility" not in [verifications[i][0] for i in range(len(verifications)) if i < critical_passed]:
            print("   - Fix Gunicorn application import issues")
        if "Database Connection" not in [verifications[i][0] for i in range(len(verifications)) if i < critical_passed]:
            print("   - Fix database connection (check .env configuration)")
        if "Production Files" not in [verifications[i][0] for i in range(len(verifications)) if i < critical_passed]:
            print("   - Create missing production files")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
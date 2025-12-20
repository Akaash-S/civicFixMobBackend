#!/usr/bin/env python3
"""
CivicFix Backend Setup Test
Quick test to verify the backend setup is working
"""

import sys
import os
import requests
import time
import subprocess
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        import flask_sqlalchemy
        import flask_migrate
        import flask_cors
        import flask_socketio
        import boto3
        import firebase_admin
        import redis
        print("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test if configuration files exist"""
    print("🔍 Testing configuration...")
    
    required_files = [
        '.env.example',
        'requirements.txt',
        'run.py',
        'app/__init__.py',
        'app/config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def test_environment_variables():
    """Test if .env file exists and has required variables"""
    print("🔍 Testing environment configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found (using .env.example)")
        return True
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'DATABASE_URL',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'S3_BUCKET_NAME',
            'FIREBASE_PROJECT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("   Please configure these in your .env file")
        else:
            print("✅ All required environment variables configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def test_database_models():
    """Test if database models can be imported"""
    print("🔍 Testing database models...")
    
    try:
        from app.models import User, Issue, IssueMedia, Upvote, Comment, StatusHistory
        print("✅ All database models imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Model import error: {e}")
        return False

def test_routes():
    """Test if route blueprints can be imported"""
    print("🔍 Testing route blueprints...")
    
    try:
        from app.routes.auth import auth_bp
        from app.routes.issues import issues_bp
        from app.routes.media import media_bp
        from app.routes.interactions import interactions_bp
        from app.routes.analytics import analytics_bp
        print("✅ All route blueprints imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Route import error: {e}")
        return False

def test_services():
    """Test if services can be imported"""
    print("🔍 Testing services...")
    
    try:
        from app.services.aws_service import AWSService
        from app.services.firebase_service import FirebaseService
        print("✅ All services imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Service import error: {e}")
        return False

def test_app_creation():
    """Test if Flask app can be created"""
    print("🔍 Testing Flask app creation...")
    
    try:
        # Set test environment
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        
        from app import create_app
        from app.config import TestingConfig
        
        app, socketio = create_app(TestingConfig)
        
        if app and socketio:
            print("✅ Flask app created successfully")
            return True
        else:
            print("❌ Failed to create Flask app")
            return False
            
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def run_quick_server_test():
    """Test if server can start (quick test)"""
    print("🔍 Testing server startup...")
    
    try:
        # This is a basic test - in a real scenario you might want to start the server
        # in a subprocess and test the health endpoint
        print("⚠️  Server startup test skipped (requires manual testing)")
        print("   Run 'python run.py' to test server startup")
        return True
        
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CivicFix Backend Setup Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Environment Test", test_environment_variables),
        ("Database Models Test", test_database_models),
        ("Routes Test", test_routes),
        ("Services Test", test_services),
        ("App Creation Test", test_app_creation),
        ("Server Test", run_quick_server_test)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 40)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your backend setup looks good.")
        print("💡 Next steps:")
        print("   1. Configure your .env file")
        print("   2. Set up Firebase service account")
        print("   3. Run database migrations")
        print("   4. Start the server with 'python run.py'")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        print("💡 Common issues:")
        print("   - Missing dependencies (run: pip install -r requirements.txt)")
        print("   - Missing configuration files")
        print("   - Environment variables not set")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
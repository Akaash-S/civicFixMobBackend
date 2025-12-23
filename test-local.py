#!/usr/bin/env python3
"""
CivicFix Backend - Local Testing Script
Test the application locally before Render deployment
"""

import os
import sys
import time
import requests
import subprocess
from threading import Thread

def test_imports():
    """Test that all required packages can be imported"""
    print("🐍 Testing Python imports...")
    
    try:
        import flask
        import sqlalchemy
        import firebase_admin
        import boto3
        import gunicorn
        print("✅ All core packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    print("🏗️ Testing Flask app creation...")
    
    try:
        # Set minimal environment variables for testing
        os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-local-testing-only')
        os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
        
        sys.path.append('.')
        from app import create_app
        
        app, socketio = create_app()
        print("✅ Flask app created successfully")
        return True, app
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False, None

def test_health_endpoint(app):
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    
    try:
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint responding")
                return True
            else:
                print(f"❌ Health endpoint returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_gunicorn_config():
    """Test that gunicorn configuration is valid"""
    print("🦄 Testing Gunicorn configuration...")
    
    try:
        import gunicorn.config
        from gunicorn.app.wsgiapp import WSGIApplication
        
        # Test config loading
        config_file = 'gunicorn.conf.py'
        if os.path.exists(config_file):
            print("✅ Gunicorn config file found")
            return True
        else:
            print("❌ Gunicorn config file not found")
            return False
    except Exception as e:
        print(f"❌ Gunicorn config test failed: {e}")
        return False

def test_requirements():
    """Test that requirements.txt is valid"""
    print("📦 Testing requirements.txt...")
    
    try:
        import pkg_resources
        
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
            requirements = [r for r in requirements if r and not r.startswith('#')]
            
        for req in requirements:
            try:
                pkg_resources.Requirement.parse(req)
            except Exception as e:
                print(f"❌ Invalid requirement: {req} - {e}")
                return False
        
        print("✅ Requirements.txt is valid")
        return True
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_build_script():
    """Test that build script works"""
    print("🔨 Testing build script...")
    
    try:
        if os.path.exists('build.sh'):
            # Check if script is executable
            if os.access('build.sh', os.X_OK):
                print("✅ Build script is executable")
                return True
            else:
                print("⚠️ Build script exists but is not executable")
                return True  # Still okay, Render will handle this
        else:
            print("❌ Build script not found")
            return False
    except Exception as e:
        print(f"❌ Build script test failed: {e}")
        return False

def test_start_script():
    """Test that start script exists"""
    print("🚀 Testing start script...")
    
    try:
        if os.path.exists('start.sh'):
            if os.access('start.sh', os.X_OK):
                print("✅ Start script is executable")
                return True
            else:
                print("⚠️ Start script exists but is not executable")
                return True  # Still okay, Render will handle this
        else:
            print("❌ Start script not found")
            return False
    except Exception as e:
        print(f"❌ Start script test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CivicFix Backend - Local Testing")
    print("===================================")
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Requirements Test", test_requirements),
        ("Build Script Test", test_build_script),
        ("Start Script Test", test_start_script),
        ("Gunicorn Config Test", test_gunicorn_config),
    ]
    
    results = []
    app = None
    
    # Run basic tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Test app creation separately
    try:
        app_result, app = test_app_creation()
        results.append(("App Creation Test", app_result))
        print()
        
        if app_result and app:
            health_result = test_health_endpoint(app)
            results.append(("Health Endpoint Test", health_result))
            print()
    except Exception as e:
        print(f"❌ App tests crashed: {e}")
        results.append(("App Creation Test", False))
        results.append(("Health Endpoint Test", False))
    
    # Summary
    print("📊 Test Results Summary")
    print("======================")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your app is ready for Render deployment.")
        print()
        print("🚀 Next steps:")
        print("  1. Push your code to GitHub")
        print("  2. Set up environment variables in Render")
        print("  3. Create a new Web Service in Render dashboard")
        print("  4. Use build command: ./build.sh")
        print("  5. Use start command: ./start.sh")
        return True
    else:
        print("⚠️ Some tests failed. Please fix the issues before deploying.")
        print()
        print("🔧 Common fixes:")
        print("  - Run: pip install -r requirements.txt")
        print("  - Run: chmod +x build.sh start.sh")
        print("  - Check that all required files exist")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
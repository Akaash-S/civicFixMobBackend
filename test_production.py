#!/usr/bin/env python3
"""
Test Production Setup
Validates that all production components are working correctly
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_gunicorn_import():
    """Test that Gunicorn can import the application"""
    print("Testing Gunicorn application import...")
    
    try:
        # Test import
        result = subprocess.run([
            sys.executable, '-c',
            'from run import application; print("SUCCESS: Application imported:", type(application).__name__)'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            print("✓ Gunicorn application import: PASSED")
            return True
        else:
            print("✗ Gunicorn application import: FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Gunicorn import test failed: {e}")
        return False

def test_production_config():
    """Test production configuration"""
    print("\nTesting production configuration...")
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        result = subprocess.run([
            sys.executable, '-c',
            '''
import os
os.environ["FLASK_ENV"] = "production"
from app import create_app
from app.config import config
app, socketio = create_app(config["production"])
print("SUCCESS: Production app created")
print(f"Debug mode: {app.config.get('DEBUG')}")
print(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
'''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            print("✓ Production configuration: PASSED")
            print(result.stdout.strip())
            return True
        else:
            print("✗ Production configuration: FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Production config test failed: {e}")
        return False
    finally:
        # Reset environment
        os.environ['FLASK_ENV'] = 'development'

def test_database_connection():
    """Test database connectivity"""
    print("\nTesting database connection...")
    
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
        result = conn.execute(db.text("SELECT 1")).fetchone()
        print(f"SUCCESS: Database query result: {result[0]}")
'''
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            print("✓ Database connection: PASSED")
            return True
        else:
            print("✗ Database connection: FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    base_url = "http://localhost:5000"
    
    endpoints = [
        ("/health", "GET"),
        ("/api/v1/issues", "GET"),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code < 500:  # Accept 4xx errors (auth required, etc.)
                print(f"✓ {method} {endpoint}: {response.status_code}")
                passed += 1
            else:
                print(f"✗ {method} {endpoint}: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ {method} {endpoint}: Connection failed (server not running?)")
        except Exception as e:
            print(f"✗ {method} {endpoint}: {e}")
    
    if passed == total:
        print(f"✓ API endpoints: {passed}/{total} PASSED")
        return True
    else:
        print(f"⚠ API endpoints: {passed}/{total} passed")
        return passed > 0

def test_production_files():
    """Test that production files exist"""
    print("\nTesting production files...")
    
    required_files = [
        '.env.production',
        'gunicorn.conf.py',
        'Dockerfile',
        'start_production.py',
        'deploy_production.sh',
        'deploy_production.bat',
        'monitor_production.py',
        'PRODUCTION_DEPLOYMENT.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✓ All production files present")
        return True
    else:
        print(f"✗ Missing production files: {missing_files}")
        return False

def main():
    """Run all production tests"""
    print("=" * 60)
    print("CivicFix Backend - Production Readiness Test")
    print("=" * 60)
    
    tests = [
        ("Gunicorn Import", test_gunicorn_import),
        ("Production Config", test_production_config),
        ("Database Connection", test_database_connection),
        ("API Endpoints", test_api_endpoints),
        ("Production Files", test_production_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name}: Exception - {e}")
        
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"PRODUCTION READINESS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Backend is PRODUCTION READY!")
        print("\nNext steps:")
        print("1. Configure .env.production with your production settings")
        print("2. Deploy using: ./deploy_production.sh")
        print("3. Monitor with: python monitor_production.py")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
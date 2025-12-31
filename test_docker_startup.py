#!/usr/bin/env python3
"""
Test Docker startup without external dependencies
"""

import os
import sys

def test_environment():
    """Test basic environment setup"""
    print("🧪 Testing Docker startup environment...")
    
    # Check Python version
    print(f"✅ Python version: {sys.version}")
    
    # Check basic imports
    try:
        import flask
        print(f"✅ Flask version: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import psycopg2
        print("✅ psycopg2 available")
    except ImportError as e:
        print(f"❌ psycopg2 import failed: {e}")
        return False
    
    try:
        import boto3
        print("✅ boto3 available")
    except ImportError as e:
        print(f"❌ boto3 import failed: {e}")
        return False
    
    # Check environment variables
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'SUPABASE_JWT_SECRET']
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is missing")
            return False
    
    print("✅ Basic environment test passed!")
    return True

def test_flask_app():
    """Test Flask app creation"""
    try:
        from flask import Flask
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test'
        
        @test_app.route('/test')
        def test_route():
            return {'status': 'ok'}
        
        with test_app.test_client() as client:
            response = client.get('/test')
            if response.status_code == 200:
                print("✅ Flask app creation test passed!")
                return True
            else:
                print(f"❌ Flask test failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐳 Docker Startup Test")
    print("=" * 30)
    
    success = True
    
    if not test_environment():
        success = False
    
    if not test_flask_app():
        success = False
    
    if success:
        print("\n🎉 All Docker startup tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Docker startup tests failed!")
        sys.exit(1)
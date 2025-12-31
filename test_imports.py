#!/usr/bin/env python3
"""
Test all imports required by app.py
"""

def test_imports():
    """Test all imports from app.py"""
    print("🧪 Testing all imports from app.py...")
    
    try:
        print("📦 Testing standard library imports...")
        import os
        import logging
        from datetime import datetime
        import json
        import uuid
        from functools import lru_cache
        import time
        import hashlib
        import secrets
        print("✅ Standard library imports successful")
        
        print("📦 Testing Flask imports...")
        from flask import Flask, request, jsonify
        from flask_sqlalchemy import SQLAlchemy
        from flask_cors import CORS
        from flask_migrate import Migrate
        from werkzeug.utils import secure_filename
        print("✅ Flask imports successful")
        
        print("📦 Testing AWS imports...")
        import boto3
        from botocore.exceptions import ClientError
        print("✅ AWS imports successful")
        
        print("📦 Testing authentication imports...")
        import jwt
        print("✅ Authentication imports successful")
        
        print("📦 Testing optional imports...")
        try:
            from dotenv import load_dotenv
            print("✅ python-dotenv available")
        except ImportError:
            print("⚠️ python-dotenv not available (optional)")
        
        try:
            import requests
            print("✅ requests available")
        except ImportError:
            print("⚠️ requests not available")
        
        print("\n🎉 All required imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_flask_app_creation():
    """Test basic Flask app creation"""
    print("\n🧪 Testing Flask app creation...")
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_cors import CORS
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        CORS(app)
        
        @app.route('/test')
        def test_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            response = client.get('/test')
            if response.status_code == 200:
                print("✅ Flask app creation successful")
                return True
            else:
                print(f"❌ Flask app test failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CivicFix Import Test")
    print("=" * 40)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_flask_app_creation():
        success = False
    
    if success:
        print("\n🎉 All tests passed! Ready for deployment.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Check missing dependencies.")
        exit(1)
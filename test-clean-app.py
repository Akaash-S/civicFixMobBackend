#!/usr/bin/env python3
"""
Test script for the clean CivicFix backend
"""

import sys
import os

def test_imports():
    """Test that all required packages can be imported"""
    print("🐍 Testing imports...")
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_cors import CORS
        from flask_migrate import Migrate
        print("✅ All Flask imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test that the app can be created"""
    print("🏗️ Testing app creation...")
    
    try:
        # Set test environment
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        
        # Import the app
        sys.path.append('.')
        import app
        
        print("✅ App creation successful")
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Clean CivicFix Backend")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("App Creation Test", test_app_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            print()
    
    print("📊 Test Results")
    print("=" * 20)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Clean backend is ready for deployment.")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
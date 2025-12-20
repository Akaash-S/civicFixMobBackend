#!/usr/bin/env python3
"""
Basic test to verify the Flask app can start
"""

import os
import sys

def test_basic_import():
    """Test basic imports"""
    try:
        from app import create_app
        from app.config import DevelopmentConfig
        print("✅ Basic imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test app creation with minimal config"""
    try:
        # Set minimal environment
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        os.environ['SECRET_KEY'] = 'test-key'
        
        from app import create_app
        from app.config import DevelopmentConfig
        
        app, socketio = create_app(DevelopmentConfig)
        
        if app and socketio:
            print("✅ App creation successful")
            print(f"   App name: {app.name}")
            print(f"   Debug mode: {app.debug}")
            print(f"   Socket.IO initialized: {socketio is not None}")
            return True
        else:
            print("❌ App creation failed")
            return False
            
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    try:
        from app import create_app
        from app.config import DevelopmentConfig
        
        app, socketio = create_app(DevelopmentConfig)
        
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                print(f"   Response: {response.get_json()}")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("🧪 CivicFix Basic Test")
    print("=" * 30)
    
    tests = [
        ("Import Test", test_basic_import),
        ("App Creation Test", test_app_creation),
        ("Health Endpoint Test", test_health_endpoint)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 20)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Results: ✅ {passed} passed, ❌ {failed} failed")
    
    if failed == 0:
        print("\n🎉 Basic tests passed! Try running: python run.py")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
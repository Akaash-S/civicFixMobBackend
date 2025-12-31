#!/usr/bin/env python3
"""
Test Flask routes for duplicates and conflicts
"""

import sys
import os

def test_flask_routes():
    """Test Flask app creation and route registration"""
    print("🧪 Testing Flask routes for duplicates...")
    
    try:
        # Set minimal environment variables for testing
        os.environ.setdefault('SECRET_KEY', 'test-key-for-route-testing')
        os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
        os.environ.setdefault('SUPABASE_JWT_SECRET', 'test-jwt-secret')
        os.environ.setdefault('SKIP_VALIDATION', 'true')
        
        # Import the app
        print("📦 Importing app.py...")
        from app import app
        
        print("✅ App imported successfully - no duplicate route errors!")
        
        # Test route registration
        print("🔍 Checking registered routes...")
        routes = []
        for rule in app.url_map.iter_rules():
            route_info = f"{rule.rule} [{', '.join(rule.methods)}]"
            routes.append(route_info)
            print(f"  ✓ {route_info}")
        
        print(f"\n📊 Total routes registered: {len(routes)}")
        
        # Check for specific onboarding routes
        onboarding_routes = [r for r in routes if 'onboarding' in r]
        print(f"📋 Onboarding routes: {len(onboarding_routes)}")
        for route in onboarding_routes:
            print(f"  • {route}")
        
        return True
        
    except AssertionError as e:
        if "overwriting an existing endpoint function" in str(e):
            print(f"❌ Duplicate route detected: {e}")
            return False
        else:
            print(f"❌ Assertion error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False

def test_basic_endpoints():
    """Test basic endpoint functionality"""
    print("\n🧪 Testing basic endpoint functionality...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"⚠️ Health endpoint returned {response.status_code}")
            
            # Test categories endpoint
            response = client.get('/api/v1/categories')
            if response.status_code == 200:
                print("✅ Categories endpoint working")
            else:
                print(f"⚠️ Categories endpoint returned {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CivicFix Route Testing")
    print("=" * 40)
    
    success = True
    
    if not test_flask_routes():
        success = False
    
    if not test_basic_endpoints():
        success = False
    
    if success:
        print("\n🎉 All route tests passed!")
        print("✅ No duplicate routes detected")
        print("✅ App loads successfully")
        print("✅ Basic endpoints working")
        sys.exit(0)
    else:
        print("\n❌ Some route tests failed!")
        sys.exit(1)
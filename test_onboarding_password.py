#!/usr/bin/env python3
"""
Test onboarding password endpoint functionality
"""

import os
import sys

def test_hash_password_function():
    """Test the hash_password function"""
    print("🧪 Testing hash_password function...")
    
    try:
        # Set minimal environment for testing
        os.environ.setdefault('SECRET_KEY', 'test-key')
        os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
        os.environ.setdefault('SUPABASE_JWT_SECRET', 'test-jwt-secret')
        os.environ.setdefault('SKIP_VALIDATION', 'true')
        
        # Import the functions
        from app import hash_password, verify_password
        
        # Test password hashing
        test_password = "testpassword123"
        hashed = hash_password(test_password)
        
        print(f"✅ Password hashed successfully: {hashed[:20]}...")
        
        # Test password verification
        if verify_password(test_password, hashed):
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test wrong password
        if not verify_password("wrongpassword", hashed):
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password incorrectly accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Hash function test failed: {e}")
        return False

def test_onboarding_endpoint():
    """Test the onboarding password endpoint"""
    print("\n🧪 Testing onboarding password endpoint...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test endpoint exists
            response = client.post('/api/v1/onboarding/password', 
                                 json={'password': 'testpass123'},
                                 headers={'Authorization': 'Bearer fake-token'})
            
            # We expect 401 (unauthorized) since we don't have real auth
            # But we should NOT get 500 (internal server error)
            if response.status_code == 401:
                print("✅ Endpoint accessible (401 Unauthorized as expected)")
                return True
            elif response.status_code == 500:
                print(f"❌ Internal server error: {response.get_json()}")
                return False
            else:
                print(f"✅ Endpoint responded with status {response.status_code}")
                return True
                
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CivicFix Onboarding Password Test")
    print("=" * 50)
    
    success = True
    
    if not test_hash_password_function():
        success = False
    
    if not test_onboarding_endpoint():
        success = False
    
    if success:
        print("\n🎉 All onboarding password tests passed!")
        print("✅ Hash function working correctly")
        print("✅ Endpoint accessible without 500 errors")
        sys.exit(0)
    else:
        print("\n❌ Some onboarding password tests failed!")
        sys.exit(1)
#!/usr/bin/env python3
"""
Test Supabase Authentication Locally
"""

import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_local_supabase_auth():
    """Test Supabase authentication functions locally"""
    
    print("🔐 Testing Supabase Authentication Locally")
    print("=" * 50)
    
    # Import the app functions
    import app
    
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found")
        return False
    
    print(f"🔑 JWT Secret: {jwt_secret[:20]}...")
    
    # Test 1: Create HS256 token
    print("\n1. Testing HS256 Token Creation and Verification...")
    
    payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'iss': 'https://your-project.supabase.co/auth/v1',
        'sub': 'test-user-12345',
        'email': 'testuser@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'testuser@example.com',
            'full_name': 'Test User'
        }
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    print(f"✅ Token created: {token[:50]}...")
    
    # Test verification
    user_data = app.verify_supabase_token(token)
    if user_data:
        print(f"✅ Token verified successfully")
        print(f"   User: {user_data.get('email')}")
        print(f"   UID: {user_data.get('uid')}")
        print(f"   Algorithm: {user_data.get('algorithm')}")
    else:
        print("❌ Token verification failed")
        return False
    
    # Test 2: Test JWT secret function
    print("\n2. Testing JWT Secret Function...")
    secret = app.get_supabase_jwt_secret()
    if secret:
        print(f"✅ JWT secret function works: {secret[:20]}...")
    else:
        print("❌ JWT secret function failed")
        return False
    
    # Test 3: Test invalid token
    print("\n3. Testing Invalid Token (should fail)...")
    invalid_token = "invalid.token.here"
    invalid_user_data = app.verify_supabase_token(invalid_token)
    if not invalid_user_data:
        print("✅ Invalid token correctly rejected")
    else:
        print("❌ Invalid token was accepted (should have failed)")
        return False
    
    # Test 4: Test expired token
    print("\n4. Testing Expired Token (should fail)...")
    expired_payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) - 3600,  # Expired 1 hour ago
        'iat': int(time.time()) - 7200,  # Issued 2 hours ago
        'sub': 'expired-user',
        'email': 'expired@example.com'
    }
    
    expired_token = jwt.encode(expired_payload, jwt_secret, algorithm='HS256')
    expired_user_data = app.verify_supabase_token(expired_token)
    if not expired_user_data:
        print("✅ Expired token correctly rejected")
    else:
        print("❌ Expired token was accepted (should have failed)")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL LOCAL TESTS PASSED!")
    print("✅ Supabase authentication functions work correctly")
    print("✅ Valid tokens are accepted")
    print("✅ Invalid tokens are rejected")
    print("✅ Expired tokens are rejected")
    print("✅ Ready for deployment!")
    
    return True

if __name__ == "__main__":
    success = test_local_supabase_auth()
    exit(0 if success else 1)
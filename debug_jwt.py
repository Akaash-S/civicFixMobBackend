#!/usr/bin/env python3
"""
Debug JWT token creation and verification
"""

import jwt
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_jwt_creation():
    """Test JWT creation and verification locally"""
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found")
        return
    
    print(f"✅ JWT Secret found: {jwt_secret[:20]}...")
    
    # Create test payload
    payload = {
        'sub': 'test_user_123',
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600,  # 1 hour from now
        'iat': int(time.time()),
        'user_metadata': {
            'full_name': 'Test User',
            'email': 'test@example.com'
        }
    }
    
    try:
        # Create JWT
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        print(f"✅ JWT created: {token[:50]}...")
        
        # Verify JWT
        decoded = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=['HS256'],
            options={"verify_exp": True, "verify_aud": False}
        )
        
        print(f"✅ JWT verified successfully")
        print(f"   User: {decoded['email']}")
        print(f"   Sub: {decoded['sub']}")
        print(f"   Expires: {time.ctime(decoded['exp'])}")
        
        return token
        
    except Exception as e:
        print(f"❌ JWT error: {e}")
        return None

def test_backend_jwt_verification(token):
    """Test JWT with backend"""
    import requests
    
    print(f"\n🔍 Testing JWT with backend...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test with users/me endpoint
        response = requests.get("http://3.110.42.224:80/api/v1/users/me", headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Backend JWT verification successful")
        else:
            print("❌ Backend JWT verification failed")
            
    except Exception as e:
        print(f"❌ Request error: {e}")

def main():
    print("🔍 JWT Debug Tool")
    print("=" * 50)
    
    # Test local JWT creation/verification
    token = test_jwt_creation()
    
    if token:
        # Test with backend
        test_backend_jwt_verification(token)
    
    print("\n" + "=" * 50)
    print("Debug completed!")

if __name__ == "__main__":
    main()
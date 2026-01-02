#!/usr/bin/env python3
"""
Test if JWT secret is properly configured on the server
"""

import requests
import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_test_jwt():
    """Create a test JWT with the local secret"""
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    if not jwt_secret:
        print("❌ Local JWT secret not found")
        return None
    
    payload = {
        'sub': 'test_user_123',
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'user_metadata': {
            'full_name': 'Test User',
            'email': 'test@example.com'
        }
    }
    
    try:
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        print(f"✅ Local JWT created successfully")
        return token
    except Exception as e:
        print(f"❌ JWT creation failed: {e}")
        return None

def test_different_secrets():
    """Test with different possible JWT secrets"""
    
    # Get the JWT secret from .env
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    if not jwt_secret:
        print("❌ No JWT secret found in environment")
        return
    
    print(f"🔍 Testing with JWT secret: {jwt_secret[:20]}...")
    
    # Create payload
    payload = {
        'sub': 'test_user_123',
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'user_metadata': {
            'full_name': 'Test User'
        }
    }
    
    # Test with current secret
    try:
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://civicfix-server.asolvitra.tech/api/v1/users/me", headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ JWT verification successful!")
        elif response.status_code == 401:
            error_data = response.json()
            if "Invalid or expired token" in error_data.get('error', ''):
                print("❌ JWT signature verification failed")
                print("   This means the server has a different JWT secret")
            elif "Authorization header required" in error_data.get('error', ''):
                print("❌ Authorization header not sent properly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_simple_custom_token():
    """Test with simple custom token (development mode)"""
    print(f"\n🔍 Testing custom token (development mode)...")
    
    import base64
    import json
    
    # Create simple custom token
    token_data = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600
    }
    
    custom_token = base64.b64encode(json.dumps(token_data).encode()).decode()
    
    headers = {"Authorization": f"Bearer {custom_token}"}
    response = requests.get("https://civicfix-server.asolvitra.tech/api/v1/users/me", headers=headers)
    
    print(f"Custom token status: {response.status_code}")
    print(f"Custom token response: {response.text}")

def main():
    print("🔍 JWT Secret Configuration Test")
    print("=" * 50)
    
    # Test JWT creation locally
    token = create_test_jwt()
    
    if token:
        # Test with server
        test_different_secrets()
    
    # Test custom token
    test_simple_custom_token()
    
    print("\n" + "=" * 50)
    print("Diagnosis:")
    print("- If JWT verification fails: Server JWT secret mismatch")
    print("- If custom token works: Server is in development mode")
    print("- Check server environment variables")

if __name__ == "__main__":
    main()
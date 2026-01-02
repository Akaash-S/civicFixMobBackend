#!/usr/bin/env python3
"""
Comprehensive JWT Issue Diagnosis Tool
Identifies the exact cause of JWT verification failures
"""

import requests
import jwt
import time
import os
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://civicfix-server.asolvitra.tech"

def test_multiple_jwt_secrets():
    """Test with different possible JWT secrets"""
    
    # Get the local JWT secret
    local_secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not local_secret:
        print("❌ No local SUPABASE_JWT_SECRET found")
        return
    
    print(f"🔍 Local JWT Secret: {local_secret[:30]}...")
    
    # Common variations that might be on the server
    test_secrets = [
        local_secret,  # Exact match
        local_secret.strip(),  # Remove whitespace
        local_secret.replace('\n', '').replace('\r', ''),  # Remove line breaks
    ]
    
    # Also test some common default Supabase secrets (if user might have used defaults)
    common_secrets = [
        "your-super-secret-jwt-token-with-at-least-32-characters-long",
        "super-secret-jwt-token-with-at-least-32-characters-long",
    ]
    
    test_secrets.extend(common_secrets)
    
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
    
    for i, secret in enumerate(test_secrets):
        print(f"\n🧪 Testing secret #{i+1}: {secret[:30]}...")
        
        try:
            # Create JWT with this secret
            token = jwt.encode(payload, secret, algorithm='HS256')
            
            # Test with server
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! This secret works: {secret[:30]}...")
                data = response.json()
                print(f"   User: {data['user']['email']}")
                return secret
            else:
                print(f"❌ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with secret #{i+1}: {e}")
    
    print("\n❌ None of the test secrets worked")
    return None

def test_server_environment():
    """Test what environment the server is running in"""
    
    print("\n🔍 Testing server environment...")
    
    # Test 1: Check if server accepts custom tokens (development mode)
    custom_token_data = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600
    }
    custom_token = base64.b64encode(json.dumps(custom_token_data).encode()).decode()
    
    headers = {"Authorization": f"Bearer {custom_token}"}
    response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
    
    if response.status_code == 200:
        print("✅ Server accepts custom tokens (DEVELOPMENT MODE)")
        print("   This means FLASK_ENV=development on server")
        return "development"
    else:
        print("❌ Server rejects custom tokens (PRODUCTION MODE)")
        print("   This means FLASK_ENV=production on server")
        return "production"

def test_jwt_secret_loading():
    """Test if the server is loading JWT secrets properly"""
    
    print("\n🔍 Testing JWT secret loading on server...")
    
    # Create a token with an obviously wrong secret
    wrong_secret = "definitely_wrong_secret_12345"
    
    payload = {
        'sub': 'test_user_123',
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time())
    }
    
    try:
        wrong_token = jwt.encode(payload, wrong_secret, algorithm='HS256')
        headers = {"Authorization": f"Bearer {wrong_token}"}
        response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
        
        if response.status_code == 401:
            error_data = response.json()
            error_msg = error_data.get('error', '')
            
            if "SUPABASE_JWT_SECRET not found" in error_msg:
                print("❌ Server doesn't have SUPABASE_JWT_SECRET configured")
                return False
            elif "Invalid or expired token" in error_msg:
                print("✅ Server has JWT secret configured (but wrong one)")
                return True
            else:
                print(f"⚠️ Unexpected error: {error_msg}")
                return True
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_real_supabase_token():
    """Create a token that matches real Supabase format exactly"""
    
    local_secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not local_secret:
        return None
    
    # Real Supabase token format
    payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'iss': 'https://xbnqoujxrmyoredzujqx.supabase.co/auth/v1',
        'sub': 'test-user-uuid-12345',
        'email': 'test@example.com',
        'phone': '',
        'app_metadata': {
            'provider': 'google',
            'providers': ['google']
        },
        'user_metadata': {
            'avatar_url': 'https://example.com/avatar.jpg',
            'email': 'test@example.com',
            'email_verified': True,
            'full_name': 'Test User',
            'iss': 'https://accounts.google.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'provider_id': '123456789',
            'sub': '123456789'
        },
        'role': 'authenticated',
        'aal': 'aal1',
        'amr': [{'method': 'oauth', 'timestamp': int(time.time())}],
        'session_id': 'test-session-id'
    }
    
    try:
        token = jwt.encode(payload, local_secret, algorithm='HS256')
        print(f"✅ Real Supabase format token created")
        return token
    except Exception as e:
        print(f"❌ Failed to create real Supabase token: {e}")
        return None

def main():
    print("🔍 Comprehensive JWT Issue Diagnosis")
    print("=" * 50)
    
    # Test 1: Check server environment
    env_mode = test_server_environment()
    
    # Test 2: Check if JWT secret is loaded
    jwt_loaded = test_jwt_secret_loading()
    
    # Test 3: Try multiple JWT secrets
    working_secret = test_multiple_jwt_secrets()
    
    # Test 4: Try real Supabase token format
    print("\n🔍 Testing real Supabase token format...")
    real_token = create_real_supabase_token()
    if real_token:
        headers = {"Authorization": f"Bearer {real_token}"}
        response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
        
        if response.status_code == 200:
            print("✅ Real Supabase format token works!")
            data = response.json()
            print(f"   User: {data['user']['email']}")
        else:
            print(f"❌ Real Supabase format failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    print(f"Server Environment: {env_mode}")
    print(f"JWT Secret Loaded: {'Yes' if jwt_loaded else 'No'}")
    print(f"Working Secret Found: {'Yes' if working_secret else 'No'}")
    
    if not jwt_loaded:
        print("\n❌ ISSUE: Server doesn't have SUPABASE_JWT_SECRET")
        print("   Solution: Add SUPABASE_JWT_SECRET to server environment")
    elif not working_secret:
        print("\n❌ ISSUE: JWT secret mismatch")
        print("   Solution: Ensure server has exact same JWT secret as local")
        print(f"   Local secret: {os.environ.get('SUPABASE_JWT_SECRET', 'NOT_FOUND')[:50]}...")
    else:
        print(f"\n✅ WORKING SECRET: {working_secret[:50]}...")
    
    print("\n🔧 Next Steps:")
    print("1. SSH into EC2 instance")
    print("2. Check: echo $SUPABASE_JWT_SECRET")
    print("3. Set: export SUPABASE_JWT_SECRET='your_secret_here'")
    print("4. Restart backend application")
    print("5. Run test again")

if __name__ == "__main__":
    main()
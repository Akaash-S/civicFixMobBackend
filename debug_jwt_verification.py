#!/usr/bin/env python3
"""
Debug JWT Verification Process
Step-by-step debugging of JWT token verification
"""

import jwt
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_jwt_verification():
    """Debug the JWT verification process step by step"""
    
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    backend_url = "https://civicfix-server.asolvitra.tech"
    
    print("🔍 JWT Verification Debug")
    print("=" * 50)
    
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found")
        return
    
    print(f"🔑 Local JWT Secret: {jwt_secret[:30]}...")
    print(f"   Length: {len(jwt_secret)}")
    
    # Create test token
    payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'iss': 'https://your-project.supabase.co/auth/v1',
        'sub': 'debug-user-12345',
        'email': 'debug@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'debug@example.com',
            'full_name': 'Debug User'
        }
    }
    
    print(f"\n🔨 Creating token with payload:")
    for key, value in payload.items():
        if key != 'user_metadata':
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    print(f"\n✅ Token created: {token[:50]}...")
    
    # Verify token locally
    print(f"\n🔍 Verifying token locally...")
    try:
        decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'], options={"verify_exp": True, "verify_aud": False})
        print(f"✅ Local verification successful!")
        print(f"   Subject: {decoded.get('sub')}")
        print(f"   Email: {decoded.get('email')}")
    except Exception as e:
        print(f"❌ Local verification failed: {e}")
        return
    
    # Test with server
    print(f"\n🌐 Testing with server...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test health endpoint first
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is reachable")
        else:
            print(f"⚠️ Server returned {response.status_code}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return
    
    # Test auth endpoint with detailed error info
    print("\n2. Testing auth endpoint with debug info...")
    try:
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("\n🔍 401 Error Analysis:")
            print("   Possible causes:")
            print("   1. Server JWT secret is different from local")
            print("   2. Server is not reading SUPABASE_JWT_SECRET env var")
            print("   3. Token format is not what server expects")
            print("   4. Server JWT verification logic has a bug")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test with a malformed token to see different error
    print("\n3. Testing with malformed token...")
    bad_headers = {
        'Authorization': f'Bearer invalid-token-12345',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=bad_headers, timeout=10)
        print(f"Bad token status: {response.status_code}")
        print(f"Bad token response: {response.text}")
    except Exception as e:
        print(f"❌ Bad token request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DEBUGGING COMPLETE")
    print("Check the server logs for more details on JWT verification")

if __name__ == "__main__":
    debug_jwt_verification()
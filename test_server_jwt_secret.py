#!/usr/bin/env python3
"""
Test Server JWT Secret
Try to determine if the server has the correct JWT secret
"""

import jwt
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_server_jwt_secret():
    """Test different JWT secrets to see which one the server accepts"""
    
    backend_url = "https://civicfix-server.asolvitra.tech"
    local_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    print("🔍 Testing Server JWT Secret")
    print("=" * 50)
    
    # Common Supabase JWT secrets to try
    secrets_to_try = [
        local_secret,  # Our local secret
        "your-super-secret-jwt-token-with-at-least-32-characters-long",  # Default
        "sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE",  # Explicit
    ]
    
    # Remove duplicates and None values
    secrets_to_try = list(filter(None, list(set(secrets_to_try))))
    
    payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'iss': 'https://your-project.supabase.co/auth/v1',
        'sub': 'test-user-12345',
        'email': 'test@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'test@example.com',
            'full_name': 'Test User'
        }
    }
    
    print(f"🧪 Testing {len(secrets_to_try)} different JWT secrets...")
    
    for i, secret in enumerate(secrets_to_try, 1):
        if not secret:
            continue
            
        print(f"\n{i}. Testing secret: {secret[:30]}...")
        
        try:
            # Create token with this secret
            token = jwt.encode(payload, secret, algorithm='HS256')
            
            # Test with server
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{backend_url}/api/v1/auth/test", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Server accepts this secret")
                print(f"   Secret: {secret}")
                print(f"   Response: {response.json()}")
                return secret
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("❌ None of the JWT secrets worked")
    print("🔍 This suggests:")
    print("   1. Server has a different JWT secret than expected")
    print("   2. Server JWT verification logic is broken")
    print("   3. Server environment variables are not loaded correctly")
    
    # Try to get more info from server
    print(f"\n🔍 Additional server info:")
    try:
        health_response = requests.get(f"{backend_url}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Server status: {health_data.get('status')}")
            print(f"   Services: {health_data.get('services')}")
    except:
        pass
    
    return None

if __name__ == "__main__":
    test_server_jwt_secret()
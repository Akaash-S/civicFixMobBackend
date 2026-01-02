#!/usr/bin/env python3
"""
Test Supabase Token with Backend
Create a test token and verify it works with the backend
"""

import jwt
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_supabase_token_with_backend():
    """Test that a Supabase-like token works with the backend"""
    
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    backend_url = "https://civicfix-server.asolvitra.tech"
    
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found in environment")
        return False
    
    print("🧪 Testing Supabase Token with Backend")
    print("=" * 50)
    
    # Create a test payload (similar to what Supabase creates)
    payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,  # 1 hour from now
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
    
    try:
        # Create JWT token
        print("🔨 Creating test Supabase token...")
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        print(f"✅ Token created: {token[:50]}...")
        
        # Test with backend
        print("\n🔍 Testing token with backend...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test auth endpoint
        print("1. Testing /api/v1/auth/test endpoint...")
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auth test successful!")
            print(f"   User: {data.get('user', {}).get('email', 'Unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
        else:
            print(f"❌ Auth test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test users/me endpoint
        print("\n2. Testing /api/v1/users/me endpoint...")
        response = requests.get(f"{backend_url}/api/v1/users/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Users/me successful!")
            print(f"   User: {data.get('user', {}).get('email', 'Unknown')}")
        else:
            print(f"❌ Users/me failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test create issue endpoint
        print("\n3. Testing /api/v1/issues endpoint...")
        issue_data = {
            'title': 'Test Issue from Token Test',
            'description': 'This is a test issue created during token testing',
            'category': 'Infrastructure',
            'priority': 'Medium',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'address': 'Test Address, San Francisco, CA'
        }
        
        response = requests.post(f"{backend_url}/api/v1/issues", 
                               headers=headers, 
                               json=issue_data)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Create issue successful!")
            print(f"   Issue: {data.get('issue', {}).get('title', 'Unknown')}")
            print(f"   ID: {data.get('issue', {}).get('id', 'Unknown')}")
        else:
            print(f"❌ Create issue failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Supabase token format works with backend")
        print("✅ Authentication is working correctly")
        print("✅ JWT secret is properly configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_token_with_backend()
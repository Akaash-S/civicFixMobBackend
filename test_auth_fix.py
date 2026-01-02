#!/usr/bin/env python3
"""
Test Authentication Fix
Test that the authentication fix works correctly
"""

import jwt
import time
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_auth_fix():
    """Test that the authentication fix works"""
    
    backend_url = "https://civicfix-server.asolvitra.tech"
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    
    print("🧪 Testing Authentication Fix")
    print("=" * 50)
    
    if not jwt_secret:
        print("❌ SUPABASE_JWT_SECRET not found")
        return False
    
    print(f"🔑 Using JWT Secret: {jwt_secret[:20]}...")
    
    # Test 1: Create a custom token like our Google auth endpoint does
    print("\n1. Testing Custom JWT Token (like Google auth creates)...")
    
    payload = {
        'user_id': 1,
        'email': 'test@example.com',
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    
    # Create token using the same method as Google auth endpoint
    custom_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    print(f"✅ Custom token created: {custom_token[:50]}...")
    
    # Test with server
    headers = {
        'Authorization': f'Bearer {custom_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Custom token authentication successful!")
            custom_success = True
        else:
            print("❌ Custom token authentication failed")
            custom_success = False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        custom_success = False
    
    # Test 2: Test create issue with custom token
    print("\n2. Testing Create Issue with Custom Token...")
    
    issue_data = {
        'title': 'Test Issue - Auth Fix',
        'description': 'This is a test issue created after the auth fix',
        'category': 'Infrastructure',
        'priority': 'Medium',
        'latitude': 37.7749,
        'longitude': -122.4194,
        'address': 'Test Address, San Francisco, CA'
    }
    
    try:
        response = requests.post(f"{backend_url}/api/v1/issues", 
                               headers=headers, 
                               json=issue_data,
                               timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Create issue successful!")
            issue_success = True
        else:
            print("❌ Create issue failed")
            issue_success = False
    except Exception as e:
        print(f"❌ Create issue request failed: {e}")
        issue_success = False
    
    # Test 3: Test Supabase-style token (if different)
    print("\n3. Testing Supabase-style Token...")
    
    supabase_payload = {
        'aud': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
        'iss': 'https://your-project.supabase.co/auth/v1',
        'sub': 'supabase-user-12345',
        'email': 'supabase@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'supabase@example.com',
            'full_name': 'Supabase User'
        }
    }
    
    supabase_token = jwt.encode(supabase_payload, jwt_secret, algorithm='HS256')
    print(f"✅ Supabase token created: {supabase_token[:50]}...")
    
    supabase_headers = {
        'Authorization': f'Bearer {supabase_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=supabase_headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Supabase token authentication successful!")
            supabase_success = True
        else:
            print("❌ Supabase token authentication failed")
            supabase_success = False
    except Exception as e:
        print(f"❌ Supabase request failed: {e}")
        supabase_success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS")
    print("=" * 50)
    
    results = {
        'Custom Token Auth': custom_success,
        'Create Issue': issue_success,
        'Supabase Token Auth': supabase_success
    }
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Authentication fix is working correctly")
        print("✅ Report form should now work without errors")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("❌ Authentication may still have issues")
        print("🔍 Check server logs for more details")
    
    return all_passed

if __name__ == "__main__":
    success = test_auth_fix()
    exit(0 if success else 1)
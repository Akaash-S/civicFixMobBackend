#!/usr/bin/env python3
"""
Simple Comments Test
Test just the comments endpoint to see the exact error
"""

import requests
import jwt
import time

# Configuration
BASE_URL = "http://3.110.42.224:80"
JWT_SECRET = "sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE"

def create_test_token():
    """Create a test JWT token"""
    payload = {
        'sub': 'test-user-comments',
        'email': 'comments-test@civicfix.com',
        'name': 'Comments Test User',
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,
        'user_metadata': {
            'full_name': 'Comments Test User',
            'email': 'comments-test@civicfix.com'
        }
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def test_comments():
    """Test comments endpoint"""
    print("🧪 Testing Comments Endpoint")
    print("=" * 40)
    
    # Test without auth first (should work for GET)
    print("1. Testing GET comments without auth...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/issues/1/comments")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {len(data.get('comments', []))} comments found")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test with auth
    print("\n2. Testing GET comments with auth...")
    token = create_test_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/issues/1/comments", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {len(data.get('comments', []))} comments found")
            print(f"   Response preview: {str(data)[:200]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test creating a comment
    print("\n3. Testing POST comment...")
    comment_data = {'content': 'Test comment from simple test script'}
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/issues/1/comments", 
                               headers=headers, json=comment_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Success: Comment created with ID {data.get('comment', {}).get('id')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_comments()
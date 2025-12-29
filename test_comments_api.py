#!/usr/bin/env python3
"""
Test the comments API endpoints
"""

import requests
import json
import jwt
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://3.110.42.224:80"  # Production server
JWT_SECRET = "sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE"

def create_test_token():
    """Create a test JWT token for authentication"""
    payload = {
        'sub': 'test-user-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,  # 1 hour from now
        'user_metadata': {
            'full_name': 'Test User',
            'email': 'test@example.com'
        }
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def test_comments_endpoints():
    """Test all comment-related endpoints"""
    print("🧪 Testing Comments API Endpoints")
    print("=" * 50)
    
    # Create test token
    token = create_test_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔑 Using token: {token[:50]}...")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Test 1: Get comments for issue (should work even if no comments exist)
    print("\n📋 Test 1: Get comments for issue 1")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/issues/1/comments", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {len(data.get('comments', []))} comments")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Create a comment
    print("\n💬 Test 2: Create a comment")
    comment_data = {
        'content': 'This is a test comment from the API test script'
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/issues/1/comments", 
                               headers=headers, 
                               json=comment_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            comment_id = data.get('comment', {}).get('id')
            print(f"   ✅ Success: Created comment with ID {comment_id}")
            return comment_id
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return None

def test_health_check():
    """Test basic health check"""
    print("🏥 Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server healthy: {data.get('status')}")
            print(f"   📊 Database: {data.get('services', {}).get('database')}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comments API Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Test health first
    test_health_check()
    
    # Test comments
    test_comments_endpoints()
    
    print("\n🎉 Test completed!")
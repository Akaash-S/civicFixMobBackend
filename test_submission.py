#!/usr/bin/env python3
"""
Test script for CivicFix backend submission
Tests authentication and issue creation
"""

import requests
import json
import base64
import time

# Configuration
BASE_URL = "http://localhost:5000" #"http://3.110.42.224:80"
TEST_USER_DATA = {
    "user_id": "test_user_123",
    "email": "test@example.com",
    "exp": int(time.time()) + 3600  # 1 hour from now
}

def create_test_token():
    """Create a simple test token"""
    token_data = json.dumps(TEST_USER_DATA)
    token = base64.b64encode(token_data.encode()).decode()
    return token

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_auth():
    """Test authentication endpoint"""
    print("\n🔐 Testing authentication...")
    try:
        token = create_test_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/api/v1/auth/test", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication successful: {data['user']['email']}")
            return True, token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False, None

def test_issue_creation(token):
    """Test issue creation"""
    print("\n📝 Testing issue creation...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        issue_data = {
            "title": "Test Issue from Backend Script",
            "description": "This is a test issue created from the backend test script",
            "category": "Testing",
            "priority": "low",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "address": "Test Location, San Francisco, CA",
            "image_urls": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/issues", 
            headers=headers, 
            json=issue_data
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Issue created successfully: ID {data['issue']['id']}")
            print(f"   Title: {data['issue']['title']}")
            return True
        else:
            print(f"❌ Issue creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Issue creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting CivicFix Backend Tests")
    print(f"   Base URL: {BASE_URL}")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed - stopping tests")
        return
    
    # Test 2: Authentication
    auth_success, token = test_auth()
    if not auth_success:
        print("\n❌ Authentication failed - stopping tests")
        return
    
    # Test 3: Issue creation
    test_issue_creation(token)
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()
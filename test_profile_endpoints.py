#!/usr/bin/env python3
"""
Test script for profile management endpoints
Tests the new profile, settings, and password endpoints
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Change to your backend URL
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzM1NjU4NzI3LCJpYXQiOjE3MzU2NTUxMjcsImlzcyI6Imh0dHBzOi8vdGVzdC5zdXBhYmFzZS5jbyIsInN1YiI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9leGFtcGxlLmNvbS9hdmF0YXIuanBnIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IlRlc3QgVXNlciIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJUZXN0IFVzZXIiLCJwaWN0dXJlIjoiaHR0cHM6Ly9leGFtcGxlLmNvbS9hdmF0YXIuanBnIiwicHJvdmlkZXJfaWQiOiIxMjM0NTY3ODkwMTIzNDU2Nzg5MCIsInN1YiI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzM1NjU1MTI3fV0sInNlc3Npb25faWQiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIifQ.test_signature_for_development"

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with authentication"""
    url = f"{BASE_URL}{endpoint}"
    
    default_headers = {
        'Authorization': f'Bearer {TEST_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=default_headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"\n{method.upper()} {endpoint}")
        print(f"Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_profile_endpoints():
    """Test profile management endpoints"""
    
    print("🧪 Testing Profile Management Endpoints")
    print("=" * 50)
    
    # Test 1: Get current user
    print("\n1️⃣ Testing GET /api/v1/users/me")
    response = make_request('GET', '/api/v1/users/me')
    
    # Test 2: Update profile
    print("\n2️⃣ Testing PUT /api/v1/users/me (Profile Update)")
    profile_data = {
        'name': 'Updated Test User',
        'phone': '+1234567890',
        'bio': 'This is my updated bio for testing profile endpoints.'
    }
    response = make_request('PUT', '/api/v1/users/me', profile_data)
    
    # Test 3: Update settings
    print("\n3️⃣ Testing PUT /api/v1/users/me/settings")
    settings_data = {
        'notifications_enabled': False,
        'dark_mode': True,
        'anonymous_reporting': True,
        'satellite_view': False,
        'save_to_gallery': False
    }
    response = make_request('PUT', '/api/v1/users/me/settings', settings_data)
    
    # Test 4: Change password (Supabase integration)
    print("\n4️⃣ Testing PUT /api/v1/users/me/password")
    password_data = {
        'current_password': 'current123',
        'new_password': 'newpassword123'
    }
    response = make_request('PUT', '/api/v1/users/me/password', password_data)
    
    # Test 5: Verify profile changes
    print("\n5️⃣ Testing GET /api/v1/users/me (Verify Changes)")
    response = make_request('GET', '/api/v1/users/me')
    
    print("\n✅ Profile endpoint testing completed!")

def test_validation():
    """Test validation and error handling"""
    
    print("\n🔍 Testing Validation and Error Handling")
    print("=" * 50)
    
    # Test empty profile update
    print("\n1️⃣ Testing empty profile update")
    response = make_request('PUT', '/api/v1/users/me', {})
    
    # Test invalid name (empty)
    print("\n2️⃣ Testing invalid name (empty)")
    response = make_request('PUT', '/api/v1/users/me', {'name': ''})
    
    # Test name too long
    print("\n3️⃣ Testing name too long")
    response = make_request('PUT', '/api/v1/users/me', {'name': 'x' * 300})
    
    # Test invalid settings
    print("\n4️⃣ Testing invalid settings")
    response = make_request('PUT', '/api/v1/users/me/settings', {'invalid_field': True})
    
    # Test password change without required fields
    print("\n5️⃣ Testing password change without required fields")
    response = make_request('PUT', '/api/v1/users/me/password', {'current_password': 'test'})
    
    print("\n✅ Validation testing completed!")

if __name__ == '__main__':
    print("🚀 Starting Profile Management Endpoint Tests")
    print(f"📍 Backend URL: {BASE_URL}")
    print(f"🔑 Using test token: {TEST_TOKEN[:50]}...")
    
    # Test basic endpoints
    test_profile_endpoints()
    
    # Test validation
    test_validation()
    
    print("\n🎉 All tests completed!")
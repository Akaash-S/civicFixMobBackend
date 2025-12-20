#!/usr/bin/env python3
"""
API Test Script for CivicFix Backend
Tests all main endpoints to verify functionality
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=5)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_data = response.json()
                print(f"   Response: {json.dumps(json_data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:100]}...")
        else:
            print(f"   Response: {response.text[:100]}...")
        
        return response.status_code < 400
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection failed (server not running?)")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("=" * 60)
    print("CivicFix Backend API Test Suite")
    print("=" * 60)
    
    tests = [
        # Health check
        ("GET", "/health"),
        
        # Issues endpoints
        ("GET", "/api/v1/issues"),
        ("GET", "/api/v1/issues?page=1&per_page=10"),
        
        # Auth endpoints (will fail without token, but should return proper error)
        ("POST", "/api/v1/auth/sync-user", {"firebase_uid": "test"}),
        
        # Media endpoints
        ("POST", "/api/v1/media/presign-url", {
            "file_name": "test.jpg",
            "content_type": "image/jpeg"
        }),
        
        # Analytics (admin only, will fail but should return proper error)
        ("GET", "/api/v1/analytics/summary"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, *args in tests:
        data = args[0] if args else None
        success = test_endpoint(method, endpoint, data)
        if success:
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All endpoints are responding correctly!")
        return True
    else:
        print("⚠️  Some endpoints may need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test Enhanced Backend API Endpoints
Comprehensive testing of all backend endpoints to ensure they work correctly
"""

import requests
import json
import jwt
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000" #"https://civicfix-server.asolvitra.tech"  # Production server
JWT_SECRET = "sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE"

def create_test_token():
    """Create a test JWT token for authentication"""
    payload = {
        'sub': 'test-user-enhanced-123',
        'email': 'enhanced-test@civicfix.com',
        'name': 'Enhanced Test User',
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,  # 1 hour from now
        'user_metadata': {
            'full_name': 'Enhanced Test User',
            'email': 'enhanced-test@civicfix.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def test_endpoint(method, endpoint, headers=None, data=None, expected_status=200, description=""):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False
        
        status_ok = response.status_code == expected_status
        status_icon = "✅" if status_ok else "❌"
        
        print(f"   {status_icon} {method} {endpoint} - Status: {response.status_code} {description}")
        
        if response.status_code == 200 or response.status_code == 201:
            try:
                data = response.json()
                if isinstance(data, dict):
                    # Show some key information
                    if 'message' in data:
                        print(f"      Message: {data['message']}")
                    elif 'status' in data:
                        print(f"      Status: {data['status']}")
                    elif 'issues' in data:
                        print(f"      Issues count: {len(data['issues'])}")
                    elif 'comments' in data:
                        print(f"      Comments count: {len(data['comments'])}")
                    elif 'categories' in data:
                        print(f"      Categories: {len(data['categories'])}")
            except:
                pass
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"      Error: {response.text[:100]}")
        
        return status_ok
        
    except Exception as e:
        print(f"   ❌ {method} {endpoint} - Exception: {e}")
        return False

def test_enhanced_backend():
    """Test all enhanced backend endpoints"""
    print("🧪 Testing Enhanced CivicFix Backend")
    print("=" * 60)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test token
    token = create_test_token()
    auth_headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    test_results = []
    
    # Test 1: Basic Health and Info Endpoints
    print("🏥 Test 1: Basic Health and Info Endpoints")
    print("-" * 40)
    test_results.append(test_endpoint('GET', '/health', description="(Health check)"))
    test_results.append(test_endpoint('GET', '/', description="(Home endpoint)"))
    
    # Test 2: Public API Endpoints (No Auth Required)
    print("\n📋 Test 2: Public API Endpoints")
    print("-" * 40)
    test_results.append(test_endpoint('GET', '/api/v1/categories', description="(Get categories)"))
    test_results.append(test_endpoint('GET', '/api/v1/priority-options', description="(Get priority options)"))
    test_results.append(test_endpoint('GET', '/api/v1/status-options', description="(Get status options)"))
    test_results.append(test_endpoint('GET', '/api/v1/stats', description="(Get statistics)"))
    test_results.append(test_endpoint('GET', '/api/v1/issues', description="(Get all issues)"))
    test_results.append(test_endpoint('GET', '/api/v1/issues?page=1&per_page=5', description="(Get issues with pagination)"))
    
    # Test 3: Authentication Endpoints
    print("\n🔐 Test 3: Authentication Endpoints")
    print("-" * 40)
    test_results.append(test_endpoint('GET', '/api/v1/auth/test', auth_headers, description="(Test auth endpoint)"))
    
    # Test Google auth endpoint (will fail without valid Google token, but should exist)
    google_auth_data = {'id_token': 'invalid-token-for-testing'}
    test_results.append(test_endpoint('POST', '/api/v1/auth/google', data=google_auth_data, expected_status=401, description="(Google auth - expected to fail with invalid token)"))
    
    # Test 4: User Endpoints (Auth Required)
    print("\n👤 Test 4: User Endpoints")
    print("-" * 40)
    test_results.append(test_endpoint('GET', '/api/v1/users/me', auth_headers, description="(Get current user)"))
    
    # Test 5: Issue Management Endpoints (Auth Required)
    print("\n📝 Test 5: Issue Management Endpoints")
    print("-" * 40)
    
    # Create a test issue
    test_issue_data = {
        'title': 'Enhanced Backend Test Issue',
        'description': 'This is a test issue created by the enhanced backend test script',
        'category': 'Other',
        'priority': 'medium',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'address': 'Test Location, New Delhi'
    }
    
    create_result = test_endpoint('POST', '/api/v1/issues', auth_headers, test_issue_data, 201, "(Create test issue)")
    test_results.append(create_result)
    
    # Get specific issue (assuming issue ID 1 exists)
    test_results.append(test_endpoint('GET', '/api/v1/issues/1', description="(Get specific issue)"))
    
    # Test nearby issues
    test_results.append(test_endpoint('GET', '/api/v1/issues/nearby?latitude=28.6139&longitude=77.2090&radius=10', description="(Get nearby issues)"))
    
    # Test 6: Comment System Endpoints
    print("\n💬 Test 6: Comment System Endpoints")
    print("-" * 40)
    
    # Get comments for issue 1
    test_results.append(test_endpoint('GET', '/api/v1/issues/1/comments', description="(Get comments for issue 1)"))
    
    # Create a test comment
    test_comment_data = {'content': 'This is a test comment from the enhanced backend test script'}
    create_comment_result = test_endpoint('POST', '/api/v1/issues/1/comments', auth_headers, test_comment_data, 201, "(Create test comment)")
    test_results.append(create_comment_result)
    
    # Test 7: File Upload Endpoints (Auth Required)
    print("\n📁 Test 7: File Upload Endpoints")
    print("-" * 40)
    
    # Test upload endpoint (will fail without actual file, but should exist)
    test_results.append(test_endpoint('POST', '/api/v1/upload', auth_headers, expected_status=400, description="(Upload endpoint - expected to fail without file)"))
    
    # Test 8: Error Handling
    print("\n🚫 Test 8: Error Handling")
    print("-" * 40)
    
    # Test non-existent endpoints
    test_results.append(test_endpoint('GET', '/api/v1/nonexistent', expected_status=404, description="(Non-existent endpoint)"))
    
    # Test unauthorized access
    test_results.append(test_endpoint('GET', '/api/v1/users/me', expected_status=401, description="(Unauthorized access)"))
    
    # Calculate results
    passed = sum(test_results)
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 ENHANCED BACKEND TEST RESULTS")
    print("=" * 60)
    print(f"📈 Tests Passed: {passed}/{total}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print(f"⏰ Test Duration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_rate >= 80:
        print("✅ Enhanced backend is working well!")
    elif success_rate >= 60:
        print("⚠️ Enhanced backend has some issues but is mostly functional")
    else:
        print("❌ Enhanced backend has significant issues")
    
    print("\n🔗 Key Endpoints Available:")
    print(f"   Health: {BASE_URL}/health")
    print(f"   Issues: {BASE_URL}/api/v1/issues")
    print(f"   Comments: {BASE_URL}/api/v1/issues/[id]/comments")
    print(f"   Auth: {BASE_URL}/api/v1/auth/google")
    print(f"   Categories: {BASE_URL}/api/v1/categories")
    
    return success_rate >= 70

if __name__ == "__main__":
    print("🚀 Starting Enhanced Backend API Test")
    print("-" * 60)
    
    success = test_enhanced_backend()
    
    if success:
        print("\n🎉 Enhanced backend test completed successfully!")
    else:
        print("\n⚠️ Enhanced backend test completed with issues!")
        print("🔧 Check the results above for details")
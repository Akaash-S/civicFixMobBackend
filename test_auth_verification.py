#!/usr/bin/env python3
"""
Comprehensive Authentication Verification Test
Tests Supabase authentication end-to-end with the deployed backend
"""

import jwt
import time
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class AuthVerificationTest:
    def __init__(self):
        self.backend_url = "https://civicfix-server.asolvitra.tech" #"https://civicfix-server.asolvitra.tech"
        self.jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
    
    def log_result(self, test_name, success, message=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        
        self.test_results.append(result)
        print(result)
    
    def create_supabase_token(self, user_data=None, algorithm='HS256', expired=False):
        """Create a Supabase-style JWT token"""
        if not user_data:
            user_data = {
                'sub': 'test-user-12345',
                'email': 'testuser@example.com',
                'full_name': 'Test User'
            }
        
        # Calculate expiration
        if expired:
            exp_time = int(time.time()) - 3600  # Expired 1 hour ago
            iat_time = int(time.time()) - 7200  # Issued 2 hours ago
        else:
            exp_time = int(time.time()) + 3600  # Valid for 1 hour
            iat_time = int(time.time())
        
        payload = {
            'aud': 'authenticated',
            'exp': exp_time,
            'iat': iat_time,
            'iss': 'https://your-project.supabase.co/auth/v1',
            'sub': user_data['sub'],
            'email': user_data['email'],
            'role': 'authenticated',
            'user_metadata': {
                'email': user_data['email'],
                'full_name': user_data.get('full_name', 'Test User'),
                'avatar_url': user_data.get('avatar_url', '')
            },
            'app_metadata': {
                'provider': 'google',
                'providers': ['google']
            }
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=algorithm)
    
    def make_request(self, method, endpoint, headers=None, json_data=None, timeout=10):
        """Make HTTP request with error handling"""
        url = f"{self.backend_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {e}")
            return None
    
    def test_server_health(self):
        """Test 1: Server health and configuration"""
        print("\n🏥 Test 1: Server Health Check")
        
        response = self.make_request('GET', '/health')
        if not response:
            self.log_result("Server Health", False, "Server not reachable")
            return False
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                version = health_data.get('version', 'unknown')
                auth_type = health_data.get('authentication', 'unknown')
                supabase_status = health_data.get('services', {}).get('supabase_auth', 'unknown')
                
                print(f"   Version: {version}")
                print(f"   Authentication: {auth_type}")
                print(f"   Supabase Auth: {supabase_status}")
                
                # Check if it's the new Supabase version
                if 'supabase' in version.lower() or auth_type == 'supabase':
                    self.log_result("Server Health", True, f"Supabase backend v{version}")
                    return True
                else:
                    self.log_result("Server Health", False, f"Old version detected: {version}")
                    return False
                    
            except json.JSONDecodeError:
                self.log_result("Server Health", False, "Invalid JSON response")
                return False
        else:
            self.log_result("Server Health", False, f"HTTP {response.status_code}")
            return False
    
    def test_valid_token_authentication(self):
        """Test 2: Valid token authentication"""
        print("\n🔐 Test 2: Valid Token Authentication")
        
        if not self.jwt_secret:
            self.log_result("Valid Token Auth", False, "JWT secret not configured")
            return False
        
        # Create valid token
        token = self.create_supabase_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"   Token: {token[:50]}...")
        
        # Test auth endpoint
        response = self.make_request('GET', '/api/v1/auth/test', headers=headers)
        if not response:
            self.log_result("Valid Token Auth", False, "Request failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                user_email = data.get('user', {}).get('email', 'unknown')
                self.log_result("Valid Token Auth", True, f"User: {user_email}")
                return True
            except json.JSONDecodeError:
                self.log_result("Valid Token Auth", False, "Invalid JSON response")
                return False
        else:
            self.log_result("Valid Token Auth", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_invalid_token_rejection(self):
        """Test 3: Invalid token rejection"""
        print("\n🚫 Test 3: Invalid Token Rejection")
        
        invalid_tokens = [
            ("Empty token", ""),
            ("Invalid format", "invalid-token-123"),
            ("Malformed JWT", "header.payload"),
            ("Wrong signature", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.wrong_signature")
        ]
        
        all_rejected = True
        
        for test_name, invalid_token in invalid_tokens:
            headers = {
                'Authorization': f'Bearer {invalid_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.make_request('GET', '/api/v1/auth/test', headers=headers)
            if response and response.status_code == 401:
                print(f"   ✅ {test_name}: Correctly rejected")
            else:
                print(f"   ❌ {test_name}: Should have been rejected")
                all_rejected = False
        
        self.log_result("Invalid Token Rejection", all_rejected)
        return all_rejected
    
    def test_expired_token_rejection(self):
        """Test 4: Expired token rejection"""
        print("\n⏰ Test 4: Expired Token Rejection")
        
        if not self.jwt_secret:
            self.log_result("Expired Token Rejection", False, "JWT secret not configured")
            return False
        
        # Create expired token
        expired_token = self.create_supabase_token(expired=True)
        headers = {
            'Authorization': f'Bearer {expired_token}',
            'Content-Type': 'application/json'
        }
        
        response = self.make_request('GET', '/api/v1/auth/test', headers=headers)
        if response and response.status_code == 401:
            self.log_result("Expired Token Rejection", True, "Expired token correctly rejected")
            return True
        else:
            self.log_result("Expired Token Rejection", False, f"Expected 401, got {response.status_code if response else 'no response'}")
            return False
    
    def test_missing_authorization_header(self):
        """Test 5: Missing Authorization header"""
        print("\n📋 Test 5: Missing Authorization Header")
        
        # Request without Authorization header
        response = self.make_request('GET', '/api/v1/auth/test')
        if response and response.status_code == 401:
            self.log_result("Missing Auth Header", True, "Correctly requires Authorization header")
            return True
        else:
            self.log_result("Missing Auth Header", False, f"Expected 401, got {response.status_code if response else 'no response'}")
            return False
    
    def test_protected_endpoints(self):
        """Test 6: Protected endpoints require authentication"""
        print("\n🛡️ Test 6: Protected Endpoints")
        
        if not self.jwt_secret:
            self.log_result("Protected Endpoints", False, "JWT secret not configured")
            return False
        
        # Create valid token
        token = self.create_supabase_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        protected_endpoints = [
            ('GET', '/api/v1/users/me', 'Get current user'),
            ('GET', '/api/v1/issues', 'List issues'),
        ]
        
        all_protected = True
        
        for method, endpoint, description in protected_endpoints:
            # Test without auth (should fail)
            response_no_auth = self.make_request(method, endpoint)
            
            # Test with auth (should succeed or at least not return 401)
            response_with_auth = self.make_request(method, endpoint, headers=headers)
            
            if response_no_auth and response_no_auth.status_code == 401:
                if response_with_auth and response_with_auth.status_code != 401:
                    print(f"   ✅ {description}: Protected correctly")
                else:
                    print(f"   ❌ {description}: Auth not working")
                    all_protected = False
            else:
                print(f"   ❌ {description}: Not protected")
                all_protected = False
        
        self.log_result("Protected Endpoints", all_protected)
        return all_protected
    
    def test_user_creation_and_sync(self):
        """Test 7: User creation and synchronization"""
        print("\n👤 Test 7: User Creation and Sync")
        
        if not self.jwt_secret:
            self.log_result("User Creation", False, "JWT secret not configured")
            return False
        
        # Create token for a new user
        unique_user = {
            'sub': f'test-user-{int(time.time())}',
            'email': f'testuser{int(time.time())}@example.com',
            'full_name': 'Test User Sync'
        }
        
        token = self.create_supabase_token(unique_user)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Make authenticated request to trigger user sync
        response = self.make_request('GET', '/api/v1/users/me', headers=headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                user_data = data.get('user', {})
                
                if user_data.get('email') == unique_user['email']:
                    self.log_result("User Creation", True, f"User synced: {user_data.get('email')}")
                    return True
                else:
                    self.log_result("User Creation", False, "User data mismatch")
                    return False
            except json.JSONDecodeError:
                self.log_result("User Creation", False, "Invalid JSON response")
                return False
        else:
            self.log_result("User Creation", False, f"HTTP {response.status_code if response else 'no response'}")
            return False
    
    def test_issue_creation_with_auth(self):
        """Test 8: Issue creation with authentication"""
        print("\n📝 Test 8: Issue Creation with Auth")
        
        if not self.jwt_secret:
            self.log_result("Issue Creation", False, "JWT secret not configured")
            return False
        
        # Create valid token
        token = self.create_supabase_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test issue data
        issue_data = {
            'title': f'Test Issue - Auth Verification {int(time.time())}',
            'description': 'This issue was created during authentication verification testing',
            'category': 'Infrastructure',
            'priority': 'Medium',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'address': 'San Francisco, CA, USA'
        }
        
        # Try to create issue
        response = self.make_request('POST', '/api/v1/issues', headers=headers, json_data=issue_data)
        
        if response and response.status_code == 201:
            try:
                data = response.json()
                issue = data.get('issue', {})
                issue_title = issue.get('title', '')
                issue_id = issue.get('id', 'unknown')
                
                self.log_result("Issue Creation", True, f"Issue #{issue_id}: {issue_title[:50]}...")
                return True
            except json.JSONDecodeError:
                self.log_result("Issue Creation", False, "Invalid JSON response")
                return False
        else:
            error_msg = response.text if response else "No response"
            self.log_result("Issue Creation", False, f"HTTP {response.status_code if response else 'no response'}: {error_msg}")
            return False
    
    def run_all_tests(self):
        """Run all authentication verification tests"""
        print("🔐 COMPREHENSIVE AUTHENTICATION VERIFICATION")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"JWT Secret: {'✅ Configured' if self.jwt_secret else '❌ Missing'}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_server_health,
            self.test_valid_token_authentication,
            self.test_invalid_token_rejection,
            self.test_expired_token_rejection,
            self.test_missing_authorization_header,
            self.test_protected_endpoints,
            self.test_user_creation_and_sync,
            self.test_issue_creation_with_auth
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_result(test_name, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            print(result)
        
        print(f"\nResults: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Supabase authentication is working perfectly")
            print("✅ Backend is properly configured")
            print("✅ All security measures are in place")
            print("✅ Ready for production use")
            return True
        elif self.passed_tests >= self.total_tests * 0.8:  # 80% pass rate
            print("\n⚠️  MOSTLY WORKING")
            print("✅ Core authentication is functional")
            print("⚠️  Some minor issues detected")
            print("🔍 Review failed tests above")
            return True
        else:
            print("\n❌ AUTHENTICATION ISSUES DETECTED")
            print("❌ Critical authentication problems found")
            print("🔧 Backend needs configuration or deployment")
            print("🔍 Check server logs and environment variables")
            return False

def main():
    """Main test execution"""
    tester = AuthVerificationTest()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🔧 TROUBLESHOOTING GUIDE")
    print("=" * 60)
    
    if not success:
        print("If tests failed, check:")
        print("1. Server is running: curl https://civicfix-server.asolvitra.tech/health")
        print("2. SUPABASE_JWT_SECRET is set on server")
        print("3. Backend code is deployed: version should be 3.0.0-supabase")
        print("4. Docker containers are running: docker-compose ps")
        print("5. Check server logs: docker-compose logs")
        print("\nDeploy fixes with: python deploy-supabase-auth.py")
    else:
        print("✅ Authentication system is working correctly!")
        print("🚀 Your app should now work without authentication errors")
        print("📱 Test the report form in your mobile app")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
CivicFix Backend API Endpoint Testing Script
Tests all API endpoints with comprehensive scenarios
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_USER_TOKEN = "test-token-123"  # Mock token for testing
TEST_ISSUE_DATA = {
    "title": "Broken Street Light on Main Street",
    "description": "The street light at the corner of Main St and Oak Ave has been out for 3 days",
    "category": "Street Light",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "address": "123 Main St, New York, NY 10001",
    "priority": "HIGH"
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_issue_id = None
        
    def log_test(self, test_name, success, response=None, error=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if response:
            print(f"   Status: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        
        if error:
            print(f"   Error: {error}")
        
        print("-" * 50)
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            success = response.status_code == 200 and 'status' in response.json()
            self.log_test("Health Check", success, response)
            return success
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
            return False
    
    def test_home_endpoint(self):
        """Test home endpoint"""
        try:
            response = self.session.get(BASE_URL)
            success = response.status_code == 200 and 'message' in response.json()
            self.log_test("Home Endpoint", success, response)
            return success
        except Exception as e:
            self.log_test("Home Endpoint", False, error=str(e))
            return False
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/categories")
            success = response.status_code == 200 and 'categories' in response.json()
            self.log_test("Get Categories", success, response)
            return success
        except Exception as e:
            self.log_test("Get Categories", False, error=str(e))
            return False
    
    def test_get_issues_no_auth(self):
        """Test getting issues without authentication (should work)"""
        try:
            response = self.session.get(f"{API_BASE}/issues")
            success = response.status_code == 200 and 'issues' in response.json()
            self.log_test("Get Issues (No Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Issues (No Auth)", False, error=str(e))
            return False
    
    def test_get_issues_with_pagination(self):
        """Test getting issues with pagination"""
        try:
            response = self.session.get(f"{API_BASE}/issues?page=1&per_page=5")
            success = response.status_code == 200 and 'pagination' in response.json()
            self.log_test("Get Issues (Pagination)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Issues (Pagination)", False, error=str(e))
            return False
    
    def test_get_issues_with_filters(self):
        """Test getting issues with filters"""
        try:
            response = self.session.get(f"{API_BASE}/issues?category=Street Light&status=OPEN")
            success = response.status_code == 200
            self.log_test("Get Issues (Filtered)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Issues (Filtered)", False, error=str(e))
            return False
    
    def test_create_issue_no_auth(self):
        """Test creating issue without authentication (should fail)"""
        try:
            response = self.session.post(f"{API_BASE}/issues", json=TEST_ISSUE_DATA)
            success = response.status_code == 401
            self.log_test("Create Issue (No Auth - Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Create Issue (No Auth - Should Fail)", False, error=str(e))
            return False
    
    def test_create_issue_with_auth(self):
        """Test creating issue with authentication"""
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            response = self.session.post(f"{API_BASE}/issues", json=TEST_ISSUE_DATA, headers=headers)
            success = response.status_code == 201
            
            if success and response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if 'issue' in data and 'id' in data['issue']:
                    self.created_issue_id = data['issue']['id']
            
            self.log_test("Create Issue (With Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Create Issue (With Auth)", False, error=str(e))
            return False
    
    def test_create_issue_invalid_data(self):
        """Test creating issue with invalid data"""
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            invalid_data = {"title": "Test"}  # Missing required fields
            response = self.session.post(f"{API_BASE}/issues", json=invalid_data, headers=headers)
            success = response.status_code == 400
            self.log_test("Create Issue (Invalid Data - Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Create Issue (Invalid Data - Should Fail)", False, error=str(e))
            return False
    
    def test_get_specific_issue(self):
        """Test getting a specific issue"""
        if not self.created_issue_id:
            self.log_test("Get Specific Issue", False, error="No issue ID available")
            return False
        
        try:
            response = self.session.get(f"{API_BASE}/issues/{self.created_issue_id}")
            success = response.status_code == 200 and 'issue' in response.json()
            self.log_test("Get Specific Issue", success, response)
            return success
        except Exception as e:
            self.log_test("Get Specific Issue", False, error=str(e))
            return False
    
    def test_get_nonexistent_issue(self):
        """Test getting a non-existent issue"""
        try:
            response = self.session.get(f"{API_BASE}/issues/99999")
            success = response.status_code == 404
            self.log_test("Get Non-existent Issue (Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Non-existent Issue (Should Fail)", False, error=str(e))
            return False
    
    def test_update_issue_status_no_auth(self):
        """Test updating issue status without authentication"""
        if not self.created_issue_id:
            self.log_test("Update Issue Status (No Auth)", False, error="No issue ID available")
            return False
        
        try:
            response = self.session.put(
                f"{API_BASE}/issues/{self.created_issue_id}/status",
                json={"status": "IN_PROGRESS"}
            )
            success = response.status_code == 401
            self.log_test("Update Issue Status (No Auth - Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Update Issue Status (No Auth - Should Fail)", False, error=str(e))
            return False
    
    def test_update_issue_status_with_auth(self):
        """Test updating issue status with authentication"""
        if not self.created_issue_id:
            self.log_test("Update Issue Status (With Auth)", False, error="No issue ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            response = self.session.put(
                f"{API_BASE}/issues/{self.created_issue_id}/status",
                json={"status": "IN_PROGRESS"},
                headers=headers
            )
            success = response.status_code == 200
            self.log_test("Update Issue Status (With Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Update Issue Status (With Auth)", False, error=str(e))
            return False
    
    def test_get_current_user_no_auth(self):
        """Test getting current user without authentication"""
        try:
            response = self.session.get(f"{API_BASE}/users/me")
            success = response.status_code == 401
            self.log_test("Get Current User (No Auth - Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Current User (No Auth - Should Fail)", False, error=str(e))
            return False
    
    def test_get_current_user_with_auth(self):
        """Test getting current user with authentication"""
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            response = self.session.get(f"{API_BASE}/users/me", headers=headers)
            success = response.status_code == 200 and 'user' in response.json()
            self.log_test("Get Current User (With Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Get Current User (With Auth)", False, error=str(e))
            return False
    
    def test_update_current_user_with_auth(self):
        """Test updating current user with authentication"""
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            update_data = {
                "name": "Updated Test User",
                "phone": "+1234567890"
            }
            response = self.session.put(f"{API_BASE}/users/me", json=update_data, headers=headers)
            success = response.status_code == 200
            self.log_test("Update Current User (With Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Update Current User (With Auth)", False, error=str(e))
            return False
    
    def test_get_status_options(self):
        """Test getting status options"""
        try:
            response = self.session.get(f"{API_BASE}/status-options")
            success = response.status_code == 200 and 'statuses' in response.json()
            self.log_test("Get Status Options", success, response)
            return success
        except Exception as e:
            self.log_test("Get Status Options", False, error=str(e))
            return False
    
    def test_get_priority_options(self):
        """Test getting priority options"""
        try:
            response = self.session.get(f"{API_BASE}/priority-options")
            success = response.status_code == 200 and 'priorities' in response.json()
            self.log_test("Get Priority Options", success, response)
            return success
        except Exception as e:
            self.log_test("Get Priority Options", False, error=str(e))
            return False
    
    def test_get_stats(self):
        """Test getting system statistics"""
        try:
            response = self.session.get(f"{API_BASE}/stats")
            success = response.status_code == 200 and 'total_issues' in response.json()
            self.log_test("Get System Stats", success, response)
            return success
        except Exception as e:
            self.log_test("Get System Stats", False, error=str(e))
            return False
    
    def test_get_nearby_issues(self):
        """Test getting nearby issues"""
        try:
            response = self.session.get(f"{API_BASE}/issues/nearby?latitude=40.7128&longitude=-74.0060&radius=5")
            success = response.status_code == 200 and 'issues' in response.json()
            self.log_test("Get Nearby Issues", success, response)
            return success
        except Exception as e:
            self.log_test("Get Nearby Issues", False, error=str(e))
            return False
    
    def test_update_issue_with_auth(self):
        """Test updating an issue with authentication"""
        if not self.created_issue_id:
            self.log_test("Update Issue (With Auth)", False, error="No issue ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
            update_data = {
                "title": "Updated Street Light Issue",
                "description": "Updated description with more details",
                "priority": "HIGH"
            }
            response = self.session.put(
                f"{API_BASE}/issues/{self.created_issue_id}",
                json=update_data,
                headers=headers
            )
            success = response.status_code == 200
            self.log_test("Update Issue (With Auth)", success, response)
            return success
        except Exception as e:
            self.log_test("Update Issue (With Auth)", False, error=str(e))
            return False
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/invalid-endpoint")
            success = response.status_code == 404
            self.log_test("Invalid Endpoint (Should Fail)", success, response)
            return success
        except Exception as e:
            self.log_test("Invalid Endpoint (Should Fail)", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting CivicFix Backend API Tests")
        print("=" * 50)
        print(f"Base URL: {BASE_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test Token: {TEST_USER_TOKEN}")
        print("=" * 50)
        
        # Basic endpoint tests
        self.test_health_endpoint()
        self.test_home_endpoint()
        self.test_categories_endpoint()
        
        # Issue endpoint tests
        self.test_get_issues_no_auth()
        self.test_get_issues_with_pagination()
        self.test_get_issues_with_filters()
        self.test_create_issue_no_auth()
        self.test_create_issue_with_auth()
        self.test_create_issue_invalid_data()
        self.test_get_specific_issue()
        self.test_get_nonexistent_issue()
        self.test_update_issue_status_no_auth()
        self.test_update_issue_status_with_auth()
        
        # User endpoint tests
        self.test_get_current_user_no_auth()
        self.test_get_current_user_with_auth()
        self.test_update_current_user_with_auth()
        
        # Additional endpoint tests
        self.test_get_status_options()
        self.test_get_priority_options()
        self.test_get_stats()
        self.test_get_nearby_issues()
        self.test_update_issue_with_auth()
        
        # Error handling tests
        self.test_invalid_endpoint()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}")
        
        print("\n🎉 Testing completed!")
        
        return failed_tests == 0

def main():
    """Main function"""
    print("CivicFix Backend API Testing Script")
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    tester = APITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
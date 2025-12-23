#!/usr/bin/env python3
"""
CivicFix Backend - Deployment Verification Script
Comprehensive verification of deployed backend
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_endpoint(url, method='GET', data=None, headers=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        success = response.status_code == expected_status
        return success, response
    except Exception as e:
        return False, str(e)

def verify_deployment(base_url):
    """Verify complete deployment"""
    print(f"🔍 Verifying CivicFix Backend Deployment")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    api_base = f"{base_url}/api/v1"
    results = []
    
    # Test basic endpoints
    tests = [
        ("Health Check", f"{base_url}/health", "GET", None, None, 200),
        ("Home Endpoint", base_url, "GET", None, None, 200),
        ("Categories", f"{api_base}/categories", "GET", None, None, 200),
        ("Status Options", f"{api_base}/status-options", "GET", None, None, 200),
        ("Priority Options", f"{api_base}/priority-options", "GET", None, None, 200),
        ("System Stats", f"{api_base}/stats", "GET", None, None, 200),
        ("Issues List", f"{api_base}/issues", "GET", None, None, 200),
        ("Issues Pagination", f"{api_base}/issues?page=1&per_page=5", "GET", None, None, 200),
        ("Nearby Issues", f"{api_base}/issues/nearby?latitude=40.7128&longitude=-74.0060", "GET", None, None, 200),
        ("Unauthorized Access", f"{api_base}/users/me", "GET", None, None, 401),
        ("Invalid Endpoint", f"{api_base}/invalid", "GET", None, None, 404),
    ]
    
    for test_name, url, method, data, headers, expected_status in tests:
        success, response = test_endpoint(url, method, data, headers, expected_status)
        
        if success:
            print(f"✅ {test_name}")
            if hasattr(response, 'json'):
                try:
                    json_data = response.json()
                    if 'version' in json_data:
                        print(f"   Version: {json_data['version']}")
                    elif 'total_issues' in json_data:
                        print(f"   Total Issues: {json_data['total_issues']}")
                    elif 'categories' in json_data:
                        print(f"   Categories: {len(json_data['categories'])}")
                except:
                    pass
        else:
            print(f"❌ {test_name}")
            if isinstance(response, str):
                print(f"   Error: {response}")
            else:
                print(f"   Status: {response.status_code}")
        
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ Failed Tests:")
        for test_name, success in results:
            if not success:
                print(f"   - {test_name}")
    
    # Additional checks
    print(f"\n🔍 Additional Checks:")
    
    # Check if running behind reverse proxy
    try:
        direct_response = requests.get(f"{base_url.replace(':80', ':5000')}/health", timeout=5)
        if direct_response.status_code == 200:
            print("✅ Direct backend access working (port 5000)")
        else:
            print("⚠️ Direct backend access not available")
    except:
        print("⚠️ Direct backend access not available")
    
    # Check response times
    try:
        start_time = time.time()
        requests.get(f"{base_url}/health", timeout=10)
        response_time = (time.time() - start_time) * 1000
        print(f"⏱️ Health endpoint response time: {response_time:.2f}ms")
        
        if response_time < 500:
            print("✅ Response time is good")
        elif response_time < 1000:
            print("⚠️ Response time is acceptable")
        else:
            print("❌ Response time is slow")
    except:
        print("❌ Could not measure response time")
    
    print(f"\n🎉 Deployment verification completed!")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return failed_tests == 0

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = input("Enter the base URL of your deployed backend (e.g., http://your-ec2-ip): ").rstrip('/')
    
    if not base_url:
        print("❌ Base URL is required")
        sys.exit(1)
    
    print("CivicFix Backend Deployment Verification")
    print("Waiting 3 seconds before starting tests...")
    time.sleep(3)
    
    success = verify_deployment(base_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
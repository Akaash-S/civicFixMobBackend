"""
Test Render Deployment
Quick script to verify your backend is working on Render
"""

import requests
import sys

def test_deployment(base_url):
    """Test the deployed backend"""
    
    print("=" * 60)
    print("Testing CivicFix Backend on Render")
    print("=" * 60)
    print(f"URL: {base_url}")
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health endpoint
    print("Test 1: Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ PASS - Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            tests_passed += 1
        else:
            print(f"✗ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except requests.exceptions.Timeout:
        print("✗ FAIL - Request timed out (cold start? try again)")
        tests_failed += 1
    except Exception as e:
        print(f"✗ FAIL - Error: {e}")
        tests_failed += 1
    
    print()
    
    # Test 2: Categories endpoint
    print("Test 2: Categories Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/categories", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ PASS - Found {len(data.get('categories', []))} categories")
            tests_passed += 1
        else:
            print(f"✗ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ FAIL - Error: {e}")
        tests_failed += 1
    
    print()
    
    # Test 3: CORS headers
    print("Test 3: CORS Headers...")
    try:
        headers = {"Origin": "http://localhost:3000"}
        response = requests.options(f"{base_url}/health", headers=headers, timeout=10)
        if "access-control-allow-origin" in response.headers:
            print("✓ PASS - CORS enabled")
            tests_passed += 1
        else:
            print("✗ FAIL - CORS not configured")
            tests_failed += 1
    except Exception as e:
        print(f"✗ FAIL - Error: {e}")
        tests_failed += 1
    
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Passed: {tests_passed}/3")
    print(f"Failed: {tests_failed}/3")
    print()
    
    if tests_passed == 3:
        print("✓ All tests passed! Your backend is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter your Render backend URL (e.g., https://civicfix-backend.onrender.com): ")
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    exit_code = test_deployment(url)
    sys.exit(exit_code)

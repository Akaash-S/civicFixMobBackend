#!/usr/bin/env python3
"""
Test script for search functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://3.110.42.224:80"  # Production backend URL
API_BASE = f"{BASE_URL}/api/v1"

def test_search_functionality():
    """Test the search functionality"""
    print("🔍 Testing Search Functionality")
    print("=" * 50)
    
    # Test 1: Basic search
    print("\n1. Testing basic search...")
    response = requests.get(f"{API_BASE}/issues?search=road")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search for 'road' returned {len(data['issues'])} issues")
        for issue in data['issues'][:3]:  # Show first 3
            print(f"   - {issue['title']}")
    else:
        print(f"❌ Search failed: {response.status_code}")
    
    # Test 2: Category filter
    print("\n2. Testing category filter...")
    response = requests.get(f"{API_BASE}/issues?category=Infrastructure")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Category filter 'Infrastructure' returned {len(data['issues'])} issues")
    else:
        print(f"❌ Category filter failed: {response.status_code}")
    
    # Test 3: Combined search and category
    print("\n3. Testing combined search and category...")
    response = requests.get(f"{API_BASE}/issues?search=broken&category=Infrastructure")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Combined search returned {len(data['issues'])} issues")
    else:
        print(f"❌ Combined search failed: {response.status_code}")
    
    # Test 4: Empty search
    print("\n4. Testing empty search...")
    response = requests.get(f"{API_BASE}/issues?search=")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Empty search returned {len(data['issues'])} issues")
    else:
        print(f"❌ Empty search failed: {response.status_code}")
    
    # Test 5: Case insensitive search
    print("\n5. Testing case insensitive search...")
    response = requests.get(f"{API_BASE}/issues?search=ROAD")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Case insensitive search returned {len(data['issues'])} issues")
    else:
        print(f"❌ Case insensitive search failed: {response.status_code}")

def test_categories_endpoint():
    """Test the categories endpoint"""
    print("\n🏷️ Testing Categories Endpoint")
    print("=" * 50)
    
    response = requests.get(f"{API_BASE}/categories")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Categories endpoint returned {len(data['categories'])} categories:")
        for category in data['categories']:
            print(f"   - {category}")
    else:
        print(f"❌ Categories endpoint failed: {response.status_code}")

if __name__ == "__main__":
    try:
        test_search_functionality()
        test_categories_endpoint()
        print("\n🎉 All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
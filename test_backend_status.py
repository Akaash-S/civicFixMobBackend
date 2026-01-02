#!/usr/bin/env python3
"""
Test backend status and check if updated code is deployed
"""

import requests
import json

def test_backend_endpoints():
    """Test various backend endpoints to check deployment status"""
    base_url = "https://civicfix-server.asolvitra.tech"
    
    print("🔍 Testing Backend Deployment Status")
    print("=" * 50)
    
    # Test 1: Health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data.get('status', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Services: {data.get('services', {})}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Check if auth test endpoint exists (new code)
    print("\n2. Testing auth test endpoint (indicates new code)...")
    try:
        # This endpoint should return 401 without auth, but 404 if not deployed
        response = requests.get(f"{base_url}/api/v1/auth/test")
        if response.status_code == 401:
            print("✅ Auth test endpoint exists (new code deployed)")
        elif response.status_code == 404:
            print("❌ Auth test endpoint not found (old code)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Auth test error: {e}")
    
    # Test 3: Test users/me endpoint without auth
    print("\n3. Testing users/me endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/users/me")
        if response.status_code == 401:
            error_data = response.json()
            print(f"✅ Users/me requires auth: {error_data.get('error', 'unknown')}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Users/me test error: {e}")
    
    # Test 4: Test with invalid token to see error message
    print("\n4. Testing with invalid token...")
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{base_url}/api/v1/users/me", headers=headers)
        if response.status_code == 401:
            error_data = response.json()
            error_msg = error_data.get('error', 'unknown')
            print(f"✅ Invalid token rejected: {error_msg}")
            
            # Check if it's the new error message
            if "Invalid or expired token" in error_msg:
                print("✅ New authentication code is deployed")
            elif "Invalid token" in error_msg:
                print("⚠️ Might be old authentication code")
            else:
                print("⚠️ Unknown error message format")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")

def main():
    test_backend_endpoints()
    
    print("\n" + "=" * 50)
    print("Backend Status Check Complete!")
    print("\nNext steps:")
    print("- If auth test endpoint exists: New code is deployed")
    print("- If 404 on auth test: Need to redeploy backend")
    print("- Check server logs for JWT verification errors")

if __name__ == "__main__":
    main()
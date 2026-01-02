#!/usr/bin/env python3
"""
Simple test for media upload functionality
"""

import requests
import json

# Test the deployed backend
BASE_URL = "https://civicfix-server.asolvitra.tech"
API_BASE = f"{BASE_URL}/api/v1"

def test_media_endpoint():
    """Test if media upload endpoint exists"""
    print("🔍 Testing Media Upload Endpoint")
    print("=" * 40)
    
    try:
        # Test endpoint without auth (should return 401)
        response = requests.post(f"{API_BASE}/issues/upload-media", timeout=10)
        
        if response.status_code == 401:
            print("✅ Media upload endpoint exists and requires auth")
            return True
        elif response.status_code == 404:
            print("❌ Media upload endpoint not found")
            return False
        else:
            print(f"✅ Media upload endpoint exists (status: {response.status_code})")
            return True
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be down")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint")
    print("=" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data.get('status', 'unknown')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if 'healthy' in str(status) else "❌"
                print(f"   {status_icon} {service}: {status}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    health_ok = test_health()
    media_ok = test_media_endpoint()
    
    if health_ok and media_ok:
        print("\n🎉 Backend endpoints are working!")
    else:
        print("\n❌ Some issues found with backend")
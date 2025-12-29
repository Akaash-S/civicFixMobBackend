#!/usr/bin/env python3
"""
Test script to verify media upload endpoints are working
"""

import requests
import json
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:5000"  # Local backend URL for testing
API_BASE = f"{BASE_URL}/api/v1"

def create_test_image():
    """Create a simple test image"""
    # This is a minimal 1x1 red PNG
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,
        0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42,
        0x60, 0x82
    ])

def test_endpoints():
    """Test all media upload endpoints"""
    print("🔍 Testing Media Upload Endpoints")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data.get('status', 'unknown')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {service}: {'OK' if status else 'Failed'}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Check if new endpoint exists
    print("\n2. Testing issue media upload endpoint availability...")
    try:
        # Try without authentication first to see if endpoint exists
        response = requests.post(f"{API_BASE}/issues/upload-media")
        
        if response.status_code == 401:
            print("✅ Issue media upload endpoint exists (returns 401 - auth required)")
        elif response.status_code == 404:
            print("❌ Issue media upload endpoint not found (404)")
        else:
            print(f"✅ Issue media upload endpoint exists (returns {response.status_code})")
            
    except Exception as e:
        print(f"❌ Endpoint test error: {e}")
    
    # Test 3: Check regular upload endpoint
    print("\n3. Testing regular upload endpoint...")
    try:
        response = requests.post(f"{API_BASE}/upload")
        
        if response.status_code == 401:
            print("✅ Regular upload endpoint exists (returns 401 - auth required)")
        elif response.status_code == 404:
            print("❌ Regular upload endpoint not found (404)")
        else:
            print(f"✅ Regular upload endpoint exists (returns {response.status_code})")
            
    except Exception as e:
        print(f"❌ Regular upload endpoint test error: {e}")
    
    # Test 4: Check multiple upload endpoint
    print("\n4. Testing multiple upload endpoint...")
    try:
        response = requests.post(f"{API_BASE}/upload/multiple")
        
        if response.status_code == 401:
            print("✅ Multiple upload endpoint exists (returns 401 - auth required)")
        elif response.status_code == 404:
            print("❌ Multiple upload endpoint not found (404)")
        else:
            print(f"✅ Multiple upload endpoint exists (returns {response.status_code})")
            
    except Exception as e:
        print(f"❌ Multiple upload endpoint test error: {e}")

def test_backend_syntax():
    """Test if backend has syntax errors"""
    print("\n🔍 Testing Backend Syntax")
    print("=" * 30)
    
    try:
        # Try to import the backend module
        import sys
        import os
        
        # Add backend directory to path
        backend_path = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, backend_path)
        
        # Try to compile the app.py file
        with open('app.py', 'r') as f:
            code = f.read()
        
        compile(code, 'app.py', 'exec')
        print("✅ Backend syntax is valid")
        
    except SyntaxError as e:
        print(f"❌ Backend syntax error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
    except Exception as e:
        print(f"❌ Backend test error: {e}")

if __name__ == "__main__":
    try:
        test_backend_syntax()
        test_endpoints()
        print("\n🎉 All endpoint tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
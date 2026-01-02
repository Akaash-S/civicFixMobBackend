#!/usr/bin/env python3
"""
Debug test for media upload functionality
"""

import requests
import json
from io import BytesIO

# Test the deployed backend
BASE_URL = "https://civicfix-server.asolvitra.tech"
API_BASE = f"{BASE_URL}/api/v1"

# Test JWT token (you'll need to get this from your app)
TEST_TOKEN = "your_jwt_token_here"  # Replace with actual token

def create_test_image():
    """Create a minimal test image (1x1 red PNG)"""
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

def test_media_upload_with_auth():
    """Test media upload with authentication"""
    print("🔍 Testing Media Upload with Authentication")
    print("=" * 50)
    
    if TEST_TOKEN == "your_jwt_token_here":
        print("❌ Please set a valid JWT token in TEST_TOKEN variable")
        return False
    
    try:
        # Create test image
        image_data = create_test_image()
        
        # Prepare files for upload
        files = {
            'files': ('test_image.png', BytesIO(image_data), 'image/png')
        }
        
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}'
        }
        
        print("📤 Uploading test image...")
        response = requests.post(
            f"{API_BASE}/issues/upload-media",
            files=files,
            headers=headers,
            timeout=30
        )
        
        print(f"📤 Response status: {response.status_code}")
        print(f"📤 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"   Media URLs: {result.get('media_urls', [])}")
            print(f"   Summary: {result.get('summary', {})}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False

def test_endpoint_without_auth():
    """Test endpoint without authentication"""
    print("\n🔍 Testing Endpoint Without Auth")
    print("=" * 40)
    
    try:
        response = requests.post(f"{API_BASE}/issues/upload-media", timeout=10)
        
        if response.status_code == 401:
            print("✅ Endpoint correctly requires authentication")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Media Upload Debug Test")
    print("=" * 60)
    
    # Test 1: Endpoint availability
    endpoint_ok = test_endpoint_without_auth()
    
    # Test 2: Upload with auth (requires valid token)
    upload_ok = test_media_upload_with_auth()
    
    print("\n" + "=" * 60)
    if endpoint_ok:
        print("✅ Endpoint is working and requires auth")
        if upload_ok:
            print("✅ Media upload is working!")
        else:
            print("❌ Media upload failed (check token and logs)")
    else:
        print("❌ Endpoint issues found")
    
    print("\n💡 To test with real auth:")
    print("1. Get JWT token from your app logs")
    print("2. Replace TEST_TOKEN in this script")
    print("3. Run the test again")
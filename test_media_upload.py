#!/usr/bin/env python3
"""
Test script for media upload functionality
"""

import requests
import json
import os
from io import BytesIO

# Configuration
BASE_URL =  "http://localhost:5000" #"http://3.110.42.224:80"  # Production backend URL
API_BASE = f"{BASE_URL}/api/v1"

# Test authentication token (you'll need to get this from your app)
# For testing, you can use a Supabase JWT token
TEST_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjVjMjM5ZTUwLTkxM2MtNGM2Ni04MjRlLTBiMTExYjMxOGFhYSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3hibnFvdWp4cm15b3JlZHp1anF4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1YmFjMTVhMC0yZDgyLTQ5NzgtODQ1Mi03MjI5ZmY0NGIyNDIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY2OTk4MTAyLCJpYXQiOjE3NjY5OTQ1MDIsImVtYWlsIjoibWF0dHBlcnNvbmFsMzIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSlIyY0NiZHk5Z3ZHOERFLTJNTWpFdk85eUROeXA3dDB3SkJFMmtMazFVd190UFRMdz1zOTYtYyIsImVtYWlsIjoibWF0dHBlcnNvbmFsMzIxQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWUiOiJtYXR0IG11cmRvY2siLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoibWF0dCBtdXJkb2NrIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSlIyY0NiZHk5Z3ZHOERFLTJNTWpFdk85eUROeXA3dDB3SkJFMmtMazFVd190UFRMdz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA1Mjc3MzUyMTc3MTIwMzg5ODkzIiwic3ViIjoiMTA1Mjc3MzUyMTc3MTIwMzg5ODkzIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NjY5MzE3Nzl9XSwic2Vzc2lvbl9pZCI6ImZmYmYyNDA3LTQ3NWItNGNlNi1hYTYxLTNmMDI1Y2Y3NGJkYSIsImlzX2Fub255bW91cyI6ZmFsc2V9.Xsy2MepOaJLyQSYy52nPjlVXqKgkh-JxLA5mZlP1NpAa7s46exXNtgi7FY6ag9Gy1dnMQ57A2Yd15-CxQZeWUA"

def create_test_image():
    """Create a simple test image"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST", fill='white')
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    except ImportError:
        # Fallback: create a minimal PNG
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

def test_media_upload():
    """Test the media upload functionality"""
    print("📤 Testing Media Upload Functionality")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {TEST_TOKEN}'
    }
    
    # Test 1: Single file upload
    print("\n1. Testing single file upload...")
    try:
        test_image = create_test_image()
        
        files = {
            'file': ('test_image.png', test_image, 'image/png')
        }
        
        response = requests.post(f"{API_BASE}/upload", headers=headers, files=files)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Single file upload successful:")
            print(f"   File URL: {data['file_url']}")
            print(f"   File size: {data['file_size']} bytes")
            print(f"   File type: {data.get('file_type', 'unknown')}")
        else:
            print(f"❌ Single file upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Single file upload error: {e}")
    
    # Test 2: Issue media upload
    print("\n2. Testing issue media upload...")
    try:
        test_image1 = create_test_image()
        test_image2 = create_test_image()
        
        files = [
            ('files', ('test_image1.png', test_image1, 'image/png')),
            ('files', ('test_image2.jpg', test_image2, 'image/jpeg'))
        ]
        
        response = requests.post(f"{API_BASE}/issues/upload-media", headers=headers, files=files)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Issue media upload successful:")
            print(f"   Message: {data['message']}")
            print(f"   Media URLs: {len(data['media_urls'])} files")
            print(f"   Summary: {data['summary']}")
            print(f"   Total size: {data['total_size']} bytes")
            
            for i, url in enumerate(data['media_urls']):
                print(f"   File {i+1}: {url}")
                
        else:
            print(f"❌ Issue media upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Issue media upload error: {e}")
    
    # Test 3: Create issue with media
    print("\n3. Testing issue creation with media...")
    try:
        # First upload media
        test_image = create_test_image()
        files = [('files', ('issue_test.png', test_image, 'image/png'))]
        
        upload_response = requests.post(f"{API_BASE}/issues/upload-media", headers=headers, files=files)
        
        if upload_response.status_code == 201:
            upload_data = upload_response.json()
            media_urls = upload_data['media_urls']
            
            # Create issue with uploaded media
            issue_data = {
                'title': 'Test Issue with Media',
                'description': 'This is a test issue with uploaded media files',
                'category': 'Other',
                'latitude': 28.6139,
                'longitude': 77.209,
                'address': 'Test Location, New Delhi',
                'priority': 'medium',
                'image_urls': media_urls
            }
            
            create_response = requests.post(
                f"{API_BASE}/issues", 
                headers={**headers, 'Content-Type': 'application/json'},
                json=issue_data
            )
            
            if create_response.status_code == 201:
                issue = create_response.json()['issue']
                print(f"✅ Issue created with media:")
                print(f"   Issue ID: {issue['id']}")
                print(f"   Title: {issue['title']}")
                print(f"   Image URLs: {len(issue['image_urls'])} files")
                
                for i, url in enumerate(issue['image_urls']):
                    print(f"   Media {i+1}: {url}")
            else:
                print(f"❌ Issue creation failed: {create_response.status_code}")
                print(f"   Error: {create_response.text}")
        else:
            print(f"❌ Media upload for issue creation failed: {upload_response.status_code}")
    
    except Exception as e:
        print(f"❌ Issue creation with media error: {e}")

def test_s3_connectivity():
    """Test S3 connectivity"""
    print("\n🔗 Testing S3 Connectivity")
    print("=" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend health check: {data.get('status', 'unknown')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {service}: {'OK' if status else 'Failed'}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    try:
        test_s3_connectivity()
        test_media_upload()
        print("\n🎉 All media upload tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
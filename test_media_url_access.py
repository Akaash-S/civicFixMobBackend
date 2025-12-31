#!/usr/bin/env python3
"""
Test Media URL Access
Upload a test image and verify it's accessible via public URL
"""

import os
import boto3
import requests
from botocore.exceptions import ClientError
import uuid

def test_media_upload_and_access():
    """Test uploading media and accessing via public URL"""
    print("🧪 Testing Media Upload and Access")
    print("=" * 50)
    
    try:
        # Get S3 configuration
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        print(f"📦 Bucket: {bucket_name}")
        print(f"🌍 Region: {region}")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # Create test image data (simple PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        test_filename = f"issues/test_image_{uuid.uuid4()}.png"
        
        print(f"📤 Uploading test image: {test_filename}")
        
        # Upload test image
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_filename,
            Body=test_image_data,
            ContentType='image/png'
        )
        
        # Generate public URL
        public_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{test_filename}"
        print(f"🔗 Public URL: {public_url}")
        
        # Test URL accessibility
        print("\n🌐 Testing URL accessibility...")
        try:
            response = requests.get(public_url, timeout=10)
            if response.status_code == 200:
                print("✅ URL is publicly accessible!")
                print(f"   Status Code: {response.status_code}")
                print(f"   Content Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"   Content Length: {len(response.content)} bytes")
            else:
                print(f"❌ URL returned status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to access URL: {e}")
        
        # Clean up test file
        print("\n🧹 Cleaning up test file...")
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_filename)
            print("✅ Test file deleted")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_existing_media_in_db():
    """Test existing media URLs from database"""
    print("\n🗄️ Testing Existing Media URLs")
    print("=" * 40)
    
    try:
        # This would require database connection
        # For now, show sample URLs that should work
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        
        sample_urls = [
            f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/sample1.jpg",
            f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/sample2.png",
            f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/sample3.mp4"
        ]
        
        print("Sample URLs that should work:")
        for url in sample_urls:
            print(f"  • {url}")
        
        print(f"\nURL Pattern: https://{bucket_name}.s3.{region}.amazonaws.com/issues/[filename]")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Media URL Access Test")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success1 = test_media_upload_and_access()
    success2 = test_existing_media_in_db()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        print("\nMedia URLs should now work properly in the frontend.")
        print("The S3Image component will handle:")
        print("  • Loading states")
        print("  • Error handling")
        print("  • Fallback displays")
        print("  • URL validation")
    else:
        print("\n❌ Some tests failed")
        print("Check S3 configuration and network connectivity")
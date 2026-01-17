#!/usr/bin/env python3
"""
Test script for Supabase Storage upload functionality
Run this to verify that media uploads are working correctly
"""

import os
import sys
import uuid
import logging
from io import BytesIO
from PIL import Image
import requests

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our storage service
from app import SupabaseStorageService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_image(width=800, height=600, format='JPEG'):
    """Create a test image in memory"""
    # Create a simple test image
    img = Image.new('RGB', (width, height), color='red')
    
    # Add some text or pattern
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    draw.rectangle([50, 50, width-50, height-50], outline='blue', width=5)
    draw.ellipse([100, 100, width-100, height-100], fill='green')
    
    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def create_test_video_placeholder():
    """Create a small test file to simulate video upload"""
    # Create a small binary file to simulate video
    test_data = b"FAKE_VIDEO_DATA_FOR_TESTING" * 1000  # ~27KB
    return test_data

def test_storage_service():
    """Test the Supabase Storage service"""
    logger.info("🧪 Starting Supabase Storage tests...")
    
    try:
        # Initialize storage service
        logger.info("📦 Initializing Supabase Storage service...")
        storage_service = SupabaseStorageService()
        logger.info("✅ Storage service initialized successfully")
        
        # Test 1: Upload a test image
        logger.info("🖼️ Test 1: Uploading test image...")
        test_image_data = create_test_image()
        image_url, image_error = storage_service.upload_file(
            test_image_data, 
            "test_image.jpg", 
            "image/jpeg"
        )
        
        if image_error:
            logger.error(f"❌ Image upload failed: {image_error}")
            return False
        else:
            logger.info(f"✅ Image uploaded successfully: {image_url}")
        
        # Test 2: Upload a test video placeholder
        logger.info("🎥 Test 2: Uploading test video placeholder...")
        test_video_data = create_test_video_placeholder()
        video_url, video_error = storage_service.upload_file(
            test_video_data, 
            "test_video.mp4", 
            "video/mp4"
        )
        
        if video_error:
            logger.error(f"❌ Video upload failed: {video_error}")
            return False
        else:
            logger.info(f"✅ Video uploaded successfully: {video_url}")
        
        # Test 3: Verify files are publicly accessible
        logger.info("🌐 Test 3: Verifying public access...")
        
        # Test image URL
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Image is publicly accessible (status: {response.status_code})")
            else:
                logger.error(f"❌ Image not accessible (status: {response.status_code})")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to access image URL: {e}")
            return False
        
        # Test video URL
        try:
            response = requests.get(video_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Video is publicly accessible (status: {response.status_code})")
            else:
                logger.error(f"❌ Video not accessible (status: {response.status_code})")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to access video URL: {e}")
            return False
        
        # Test 4: Large file upload (simulate)
        logger.info("📏 Test 4: Testing larger file upload...")
        large_image_data = create_test_image(1920, 1080)  # Larger image
        large_url, large_error = storage_service.upload_file(
            large_image_data, 
            "test_large_image.jpg", 
            "image/jpeg"
        )
        
        if large_error:
            logger.error(f"❌ Large file upload failed: {large_error}")
            return False
        else:
            logger.info(f"✅ Large file uploaded successfully: {large_url}")
        
        logger.info("🎉 All tests passed! Supabase Storage is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

def test_environment_variables():
    """Test that all required environment variables are set"""
    logger.info("🔧 Checking environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_STORAGE_BUCKET'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show partial value for security
            display_value = value[:20] + '...' if len(value) > 20 else value
            logger.info(f"✅ {var}: {display_value}")
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def main():
    """Main test function"""
    logger.info("🚀 Starting Supabase Storage test suite...")
    
    # Test environment variables first
    if not test_environment_variables():
        logger.error("❌ Environment variable check failed")
        sys.exit(1)
    
    # Test storage service
    if not test_storage_service():
        logger.error("❌ Storage service tests failed")
        sys.exit(1)
    
    logger.info("🎉 All tests completed successfully!")
    logger.info("📝 Summary:")
    logger.info("  ✅ Environment variables configured")
    logger.info("  ✅ Storage service initialized")
    logger.info("  ✅ Image upload working")
    logger.info("  ✅ Video upload working")
    logger.info("  ✅ Public access working")
    logger.info("  ✅ Large file upload working")
    logger.info("")
    logger.info("🚀 Your Supabase Storage is ready for production!")

if __name__ == "__main__":
    main()
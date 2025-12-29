#!/usr/bin/env python3
"""
Test S3 upload without ACL to fix AccessControlListNotSupported error
"""

import os
import boto3
from botocore.exceptions import ClientError
import uuid

def test_s3_upload_without_acl():
    """Test S3 upload without ACL setting"""
    print("🔍 Testing S3 Upload Without ACL")
    print("=" * 40)
    
    try:
        # Get S3 configuration from environment
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        if not all([bucket_name, aws_access_key, aws_secret_key]):
            print("❌ Missing AWS configuration")
            print(f"   Bucket: {'✅' if bucket_name else '❌'}")
            print(f"   Access Key: {'✅' if aws_access_key else '❌'}")
            print(f"   Secret Key: {'✅' if aws_secret_key else '❌'}")
            return False
        
        print(f"📤 Testing upload to bucket: {bucket_name}")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # Test data
        test_data = b"Test file content for S3 upload"
        test_filename = f"test/upload_test_{uuid.uuid4()}.txt"
        
        print(f"📤 Uploading test file: {test_filename}")
        
        # Upload WITHOUT ACL
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_filename,
            Body=test_data,
            ContentType='text/plain'
            # No ACL parameter - this should fix the AccessControlListNotSupported error
        )
        
        # Generate URL
        file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{test_filename}"
        
        print("✅ Upload successful!")
        print(f"   File URL: {file_url}")
        
        # Clean up test file
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_filename)
            print("✅ Test file cleaned up")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ S3 ClientError: {error_code}")
        print(f"   Message: {error_message}")
        
        if error_code == 'AccessControlListNotSupported':
            print("   🔧 This error should be fixed by removing ACL parameter")
        elif error_code == 'AccessDenied':
            print("   🔧 Check AWS credentials and bucket permissions")
        elif error_code == 'NoSuchBucket':
            print("   🔧 Check bucket name and region")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 S3 Upload Fix Test")
    print("=" * 50)
    
    success = test_s3_upload_without_acl()
    
    if success:
        print("\n🎉 S3 upload test passed!")
        print("   The ACL fix should resolve the upload issue.")
    else:
        print("\n❌ S3 upload test failed")
        print("   Check AWS configuration and bucket settings.")
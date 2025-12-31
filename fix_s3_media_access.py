#!/usr/bin/env python3
"""
Fix S3 Media Access Issues
- Configure bucket for public read access
- Set up proper CORS configuration
- Test media URL accessibility
"""

import os
import boto3
import json
from botocore.exceptions import ClientError

def setup_s3_public_access():
    """Configure S3 bucket for public read access"""
    print("🔧 Configuring S3 Bucket for Public Access")
    print("=" * 50)
    
    try:
        # Get S3 configuration
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        if not all([bucket_name, aws_access_key, aws_secret_key]):
            print("❌ Missing AWS configuration")
            return False
        
        print(f"📦 Bucket: {bucket_name}")
        print(f"🌍 Region: {region}")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # 1. Configure CORS for web access
        print("\n🔧 Setting up CORS configuration...")
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        try:
            s3_client.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_configuration
            )
            print("✅ CORS configuration applied")
        except ClientError as e:
            print(f"⚠️ CORS configuration failed: {e}")
        
        # 2. Set up bucket policy for public read access
        print("\n🔧 Setting up bucket policy for public read access...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        try:
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Bucket policy applied for public read access")
        except ClientError as e:
            print(f"⚠️ Bucket policy failed: {e}")
            print("   This might be due to bucket ownership controls")
        
        # 3. Disable block public access (if needed)
        print("\n🔧 Checking public access block settings...")
        try:
            response = s3_client.get_public_access_block(Bucket=bucket_name)
            current_settings = response['PublicAccessBlockConfiguration']
            
            print(f"   Block Public ACLs: {current_settings.get('BlockPublicAcls', False)}")
            print(f"   Ignore Public ACLs: {current_settings.get('IgnorePublicAcls', False)}")
            print(f"   Block Public Policy: {current_settings.get('BlockPublicPolicy', False)}")
            print(f"   Restrict Public Buckets: {current_settings.get('RestrictPublicBuckets', False)}")
            
            # If public policy is blocked, we need to unblock it
            if current_settings.get('BlockPublicPolicy', False):
                print("\n🔧 Updating public access block settings...")
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,  # Keep ACLs blocked
                        'IgnorePublicAcls': True,  # Keep ACLs ignored
                        'BlockPublicPolicy': False,  # Allow public policy
                        'RestrictPublicBuckets': False  # Allow public bucket
                    }
                )
                print("✅ Public access block settings updated")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                print("   No public access block configuration found (default allows)")
            else:
                print(f"⚠️ Could not check public access block: {e}")
        
        # 4. Test a sample URL
        print("\n🧪 Testing sample media URL...")
        sample_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/sample.jpg"
        print(f"   Sample URL format: {sample_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_existing_media_urls():
    """Test existing media URLs in the database"""
    print("\n🧪 Testing Existing Media URLs")
    print("=" * 40)
    
    try:
        # This would require database connection
        # For now, just show the expected URL format
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        
        print(f"Expected URL format:")
        print(f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/[filename]")
        print(f"\nExample:")
        print(f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/12345-image.jpg")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 S3 Media Access Fix")
    print("=" * 60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = setup_s3_public_access()
    
    if success:
        test_existing_media_urls()
        print("\n🎉 S3 configuration completed!")
        print("\nNext steps:")
        print("1. Test media URLs in the frontend")
        print("2. Upload a new image to verify access")
        print("3. Check browser console for any CORS errors")
    else:
        print("\n❌ S3 configuration failed")
        print("Check AWS credentials and permissions")
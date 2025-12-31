#!/usr/bin/env python3
"""
Apply S3 Bucket Policy for Public Read Access
Now that public access block has been updated
"""

import os
import boto3
import json
from botocore.exceptions import ClientError

def apply_bucket_policy():
    """Apply bucket policy for public read access"""
    print("🔧 Applying S3 Bucket Policy")
    print("=" * 40)
    
    try:
        # Get S3 configuration
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        print(f"📦 Bucket: {bucket_name}")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # Set up bucket policy for public read access
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
        
        print("🔧 Applying bucket policy...")
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✅ Bucket policy applied successfully!")
        
        # Verify policy
        print("\n🔍 Verifying bucket policy...")
        try:
            response = s3_client.get_bucket_policy(Bucket=bucket_name)
            policy = json.loads(response['Policy'])
            print("✅ Bucket policy verified:")
            print(f"   Effect: {policy['Statement'][0]['Effect']}")
            print(f"   Action: {policy['Statement'][0]['Action']}")
            print(f"   Principal: {policy['Statement'][0]['Principal']}")
        except Exception as e:
            print(f"⚠️ Could not verify policy: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Failed to apply bucket policy: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 S3 Bucket Policy Application")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = apply_bucket_policy()
    
    if success:
        print("\n🎉 Bucket policy applied successfully!")
        print("\nMedia URLs should now be publicly accessible:")
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'ap-south-1')
        print(f"https://{bucket_name}.s3.{region}.amazonaws.com/issues/[filename]")
    else:
        print("\n❌ Failed to apply bucket policy")
        print("Check AWS permissions and try again")
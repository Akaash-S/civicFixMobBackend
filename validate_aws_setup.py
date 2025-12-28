#!/usr/bin/env python3
"""
CivicFix Backend - Supabase + AWS Setup Validation Script
Validates Supabase authentication, AWS RDS and S3 connectivity before starting the application
"""

import os
import sys
import boto3
import psycopg2
from botocore.exceptions import ClientError, NoCredentialsError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables only")

def validate_environment_variables():
    """Validate required environment variables"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_BUCKET_NAME',
        'AWS_REGION',
        'SUPABASE_JWT_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def validate_rds_connection():
    """Validate AWS RDS PostgreSQL connection"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        # Parse connection string for psycopg2
        if database_url.startswith('postgresql://'):
            # Set connection timeout
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print(f"✅ RDS PostgreSQL connection successful")
            print(f"   Database version: {version.split(',')[0]}")
            return True
        else:
            print("❌ Invalid DATABASE_URL format")
            return False
            
    except psycopg2.OperationalError as e:
        if "timeout expired" in str(e):
            print("❌ RDS connection timeout - check security groups and network connectivity")
        else:
            print(f"❌ RDS connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ RDS connection failed: {e}")
        return False

def validate_s3_connection():
    """Validate AWS S3 connection and bucket access"""
    try:
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        region = os.environ.get('AWS_REGION')
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        # Test bucket access
        s3_client.head_bucket(Bucket=bucket_name)
        
        # Test list objects permission
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        
        print(f"✅ S3 connection successful")
        print(f"   Bucket: {bucket_name}")
        print(f"   Region: {region}")
        
        # Check bucket policy for public read
        try:
            policy = s3_client.get_bucket_policy(Bucket=bucket_name)
            print("✅ Bucket policy configured")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print("⚠️ No bucket policy found - files may not be publicly accessible")
            else:
                print(f"⚠️ Could not check bucket policy: {e}")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ S3 bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to S3 bucket '{bucket_name}'")
        else:
            print(f"❌ S3 error: {e}")
        return False
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def validate_supabase_config():
    """Validate Supabase JWT secret configuration"""
    try:
        jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        
        if not jwt_secret:
            print("❌ SUPABASE_JWT_SECRET not configured")
            return False
        
        # Check if it looks like a valid Supabase JWT secret
        if not jwt_secret.startswith('sb_secret_'):
            print("⚠️ JWT secret doesn't look like a Supabase secret (should start with 'sb_secret_')")
            print("   This might still work if it's a valid secret")
        
        # Check minimum length
        if len(jwt_secret) < 32:
            print("❌ JWT secret is too short (should be at least 32 characters)")
            return False
        
        print("✅ Supabase JWT secret configured")
        print(f"   Secret: {jwt_secret[:20]}... (length: {len(jwt_secret)})")
        return True
        
    except Exception as e:
        print(f"❌ Supabase configuration validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 CivicFix Backend - Supabase + AWS Setup Validation")
    print("=" * 50)
    
    validations = [
        ("Environment Variables", validate_environment_variables),
        ("AWS RDS Connection", validate_rds_connection),
        ("AWS S3 Connection", validate_s3_connection),
        ("Supabase Configuration", validate_supabase_config)
    ]
    
    all_passed = True
    
    for name, validator in validations:
        print(f"\n📋 Validating {name}...")
        if not validator():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All validations passed! Backend is ready to start.")
        print("✅ Supabase authentication configured")
        print("✅ AWS RDS database connected")
        print("✅ AWS S3 storage accessible")
        print("\nYou can now run:")
        print("  python app.py")
        sys.exit(0)
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        print("\nRefer to SUPABASE_AUTH_IMPLEMENTATION.md for setup instructions.")
        sys.exit(1)

if __name__ == "__main__":
    main()
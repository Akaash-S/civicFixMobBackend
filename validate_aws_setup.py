#!/usr/bin/env python3
"""
CivicFix Backend - AWS Setup Validation Script
Validates AWS RDS and S3 connectivity before starting the application
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
        'FIREBASE_SERVICE_ACCOUNT_B64',
        'FIREBASE_PROJECT_ID'
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

def validate_firebase_config():
    """Validate Firebase configuration by actually initializing Firebase"""
    try:
        import base64
        import json
        
        b64_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT_B64')
        project_id = os.environ.get('FIREBASE_PROJECT_ID')
        
        if not b64_creds or not project_id:
            print("❌ Firebase configuration incomplete")
            return False
        
        # Try to decode base64 credentials
        try:
            json_str = base64.b64decode(b64_creds).decode('utf-8')
            cred_dict = json.loads(json_str)
            
            if 'project_id' not in cred_dict:
                print("❌ Invalid Firebase service account JSON")
                return False
            
            # Actually test Firebase initialization
            try:
                import firebase_admin
                from firebase_admin import credentials
                
                # Try to initialize Firebase with the credentials
                cred = credentials.Certificate(cred_dict)
                
                # Check if Firebase is already initialized
                try:
                    firebase_admin.get_app()
                    firebase_admin.delete_app(firebase_admin.get_app())
                except ValueError:
                    pass  # No app initialized yet
                
                # Initialize Firebase
                app = firebase_admin.initialize_app(cred)
                
                # Test basic functionality
                from firebase_admin import auth
                # This will fail if credentials are invalid
                auth.get_user_by_email("nonexistent@example.com")
                
            except firebase_admin.exceptions.FirebaseError as e:
                if "USER_NOT_FOUND" in str(e):
                    # This is expected - means Firebase is working
                    print("✅ Firebase configuration valid and working")
                    print(f"   Project ID: {project_id}")
                    return True
                else:
                    print(f"❌ Firebase error: {e}")
                    return False
            except Exception as e:
                if "Unable to load PEM file" in str(e) or "InvalidData" in str(e):
                    print(f"❌ Firebase private key is malformed: {e}")
                    print("   The private key in your service account JSON may be corrupted")
                    return False
                else:
                    print(f"❌ Firebase initialization failed: {e}")
                    return False
            
            print("✅ Firebase configuration valid")
            print(f"   Project ID: {project_id}")
            return True
            
        except Exception as e:
            print(f"❌ Invalid Firebase credentials format: {e}")
            return False
            
    except ImportError:
        print("⚠️ Firebase Admin SDK not installed - authentication will be disabled")
        return True

def main():
    """Main validation function"""
    print("🔍 CivicFix Backend - AWS Setup Validation")
    print("=" * 50)
    
    validations = [
        ("Environment Variables", validate_environment_variables),
        ("AWS RDS Connection", validate_rds_connection),
        ("AWS S3 Connection", validate_s3_connection),
        ("Firebase Configuration", validate_firebase_config)
    ]
    
    all_passed = True
    
    for name, validator in validations:
        print(f"\n📋 Validating {name}...")
        if not validator():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All validations passed! Backend is ready to start.")
        print("\nYou can now run:")
        print("  python app.py")
        sys.exit(0)
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        print("\nRefer to AWS_SETUP_GUIDE.md for setup instructions.")
        sys.exit(1)

if __name__ == "__main__":
    main()
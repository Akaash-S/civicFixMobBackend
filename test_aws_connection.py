#!/usr/bin/env python3
"""
Test AWS Connection Script
Quick test to verify AWS credentials and database connection
"""

import os
import sys
import boto3
import psycopg2
from urllib.parse import urlparse

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'

def log(message, color=Colors.RESET):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def test_environment_variables():
    """Test if all required environment variables are present"""
    log("🔍 Testing Environment Variables", Colors.BLUE)
    log("=" * 40, Colors.BLUE)
    
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        log("✅ .env file loaded", Colors.GREEN)
    except ImportError:
        log("⚠️  python-dotenv not installed, using system environment", Colors.YELLOW)
    except Exception as e:
        log(f"⚠️  Could not load .env file: {str(e)}", Colors.YELLOW)
    
    # Check required variables
    required_vars = {
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'AWS_S3_BUCKET_NAME': os.environ.get('AWS_S3_BUCKET_NAME'),
        'AWS_REGION': os.environ.get('AWS_REGION', 'ap-south-1')
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            if var_name in ['AWS_SECRET_ACCESS_KEY']:
                # Hide sensitive values
                display_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else "***"
            else:
                display_value = var_value
            log(f"✅ {var_name}: {display_value}", Colors.GREEN)
        else:
            log(f"❌ {var_name}: Not set", Colors.RED)
            missing_vars.append(var_name)
    
    if missing_vars:
        log(f"\n❌ Missing variables: {', '.join(missing_vars)}", Colors.RED)
        return False
    
    log("\n✅ All environment variables are set", Colors.GREEN)
    return True

def test_aws_connection():
    """Test AWS S3 connection"""
    log("\n🪣 Testing AWS S3 Connection", Colors.BLUE)
    log("=" * 40, Colors.BLUE)
    
    try:
        # Get credentials
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        s3_bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        aws_region = os.environ.get('AWS_REGION', 'ap-south-1')
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        log("✅ S3 client created successfully", Colors.GREEN)
        
        # Test bucket access
        log(f"🔍 Testing bucket access: {s3_bucket_name}", Colors.BLUE)
        
        try:
            response = s3_client.head_bucket(Bucket=s3_bucket_name)
            log("✅ Bucket is accessible", Colors.GREEN)
            
            # List some objects
            try:
                response = s3_client.list_objects_v2(Bucket=s3_bucket_name, MaxKeys=5)
                if 'Contents' in response:
                    object_count = len(response['Contents'])
                    log(f"📊 Found {object_count} objects (showing first 5)", Colors.GREEN)
                    for obj in response['Contents']:
                        size_kb = round(obj['Size'] / 1024, 2)
                        log(f"   • {obj['Key']} ({size_kb} KB)", Colors.RESET)
                else:
                    log("📊 Bucket is empty", Colors.BLUE)
                    
            except Exception as e:
                log(f"⚠️  Could not list objects: {str(e)}", Colors.YELLOW)
                
        except Exception as e:
            log(f"❌ Cannot access bucket: {str(e)}", Colors.RED)
            return False
            
        return True
        
    except Exception as e:
        log(f"❌ AWS connection failed: {str(e)}", Colors.RED)
        return False

def test_database_connection():
    """Test database connection"""
    log("\n🗄️  Testing Database Connection", Colors.BLUE)
    log("=" * 40, Colors.BLUE)
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        # Parse database URL
        parsed_url = urlparse(database_url)
        if parsed_url.scheme == 'postgres':
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
        db_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password
        }
        
        log(f"🔍 Connecting to: {db_config['host']}:{db_config['port']}/{db_config['database']}", Colors.BLUE)
        
        # Test connection
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        log("✅ Database connection successful", Colors.GREEN)
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        log(f"📊 PostgreSQL version: {version.split(',')[0]}", Colors.GREEN)
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        if tables:
            log(f"📊 Found {len(tables)} tables:", Colors.GREEN)
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                log(f"   • {table}: {count} records", Colors.RESET)
        else:
            log("📊 No tables found", Colors.BLUE)
            
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        log(f"❌ Database connection failed: {str(e)}", Colors.RED)
        return False

def main():
    """Main test function"""
    log("🧪 AWS Connection Test", Colors.BLUE)
    log("=" * 50, Colors.BLUE)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        log("\n❌ Environment variables test failed. Please check your .env file.", Colors.RED)
        return
    
    # Test AWS connection
    aws_ok = test_aws_connection()
    
    # Test database connection
    db_ok = test_database_connection()
    
    # Summary
    log("\n📋 Test Summary", Colors.BLUE)
    log("=" * 20, Colors.BLUE)
    
    if env_ok:
        log("✅ Environment Variables: PASS", Colors.GREEN)
    else:
        log("❌ Environment Variables: FAIL", Colors.RED)
        
    if aws_ok:
        log("✅ AWS S3 Connection: PASS", Colors.GREEN)
    else:
        log("❌ AWS S3 Connection: FAIL", Colors.RED)
        
    if db_ok:
        log("✅ Database Connection: PASS", Colors.GREEN)
    else:
        log("❌ Database Connection: FAIL", Colors.RED)
        
    if env_ok and aws_ok and db_ok:
        log("\n🎉 All tests passed! You can now run the cleanup scripts.", Colors.GREEN)
    else:
        log("\n⚠️  Some tests failed. Please fix the issues before running cleanup scripts.", Colors.YELLOW)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}❌ Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.RESET}")
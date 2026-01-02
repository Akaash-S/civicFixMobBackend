#!/usr/bin/env python3
"""
CivicFix AWS Data Cleanup Script
Safely delete all data from RDS PostgreSQL database and S3 bucket

⚠️  WARNING: This script will permanently delete ALL data!
Use with extreme caution and only in development/testing environments.
"""

import os
import sys
import boto3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
from datetime import datetime
from urllib.parse import urlparse
import json

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class AWSDataCleaner:
    def __init__(self):
        # Initialize cleanup_log first
        self.cleanup_log = []
        self.load_environment()
        self.setup_aws_clients()
        self.setup_database_connection()
        
    def load_environment(self):
        """Load environment variables"""
        # Try to load from .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
            
        # Required environment variables
        self.database_url = os.environ.get('DATABASE_URL')
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        self.aws_region = os.environ.get('AWS_REGION', 'ap-south-1')
        
        # Validate required variables
        missing_vars = []
        if not self.database_url:
            missing_vars.append('DATABASE_URL')
        if not self.aws_access_key:
            missing_vars.append('AWS_ACCESS_KEY_ID')
        if not self.aws_secret_key:
            missing_vars.append('AWS_SECRET_ACCESS_KEY')
        if not self.s3_bucket_name:
            missing_vars.append('AWS_S3_BUCKET_NAME')
            
        if missing_vars:
            self.log(f"❌ Missing required environment variables: {', '.join(missing_vars)}", Colors.RED)
            sys.exit(1)
            
    def setup_aws_clients(self):
        """Setup AWS clients"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            self.log("✅ AWS S3 client initialized", Colors.GREEN)
        except Exception as e:
            self.log(f"❌ Failed to initialize AWS S3 client: {str(e)}", Colors.RED)
            sys.exit(1)
            
    def setup_database_connection(self):
        """Setup database connection"""
        try:
            # Parse database URL
            parsed_url = urlparse(self.database_url)
            
            # Handle postgres:// vs postgresql:// schemes
            if parsed_url.scheme == 'postgres':
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
                
            self.db_config = {
                'host': parsed_url.hostname,
                'port': parsed_url.port or 5432,
                'database': parsed_url.path[1:],  # Remove leading slash
                'user': parsed_url.username,
                'password': parsed_url.password
            }
            
            self.log("✅ Database configuration loaded", Colors.GREEN)
            
        except Exception as e:
            self.log(f"❌ Failed to parse database URL: {str(e)}", Colors.RED)
            sys.exit(1)
            
    def log(self, message, color=Colors.WHITE):
        """Print colored log message and store in log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(f"{color}{log_entry}{Colors.RESET}")
        self.cleanup_log.append(log_entry)
        
    def confirm_action(self, action_description):
        """Get user confirmation for dangerous actions"""
        self.log(f"\n⚠️  {action_description}", Colors.YELLOW)
        self.log("This action cannot be undone!", Colors.RED)
        
        confirmation = input(f"\nType 'DELETE' to confirm (case-sensitive): ")
        
        if confirmation != 'DELETE':
            self.log("❌ Action cancelled by user", Colors.YELLOW)
            return False
            
        # Double confirmation for extra safety
        final_confirm = input(f"\nAre you absolutely sure? Type 'YES' to proceed: ")
        
        if final_confirm != 'YES':
            self.log("❌ Action cancelled by user", Colors.YELLOW)
            return False
            
        return True
        
    def get_database_tables(self):
        """Get list of all tables in the database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Get all user tables (excluding system tables)
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return tables
            
        except Exception as e:
            self.log(f"❌ Failed to get database tables: {str(e)}", Colors.RED)
            return []
            
    def get_table_row_count(self, table_name):
        """Get row count for a specific table"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            self.log(f"⚠️  Could not count rows in {table_name}: {str(e)}", Colors.YELLOW)
            return 0
            
    def cleanup_database(self):
        """Delete all data from RDS PostgreSQL database"""
        self.log("\n🗄️  Database Cleanup", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Get list of tables
        tables = self.get_database_tables()
        
        if not tables:
            self.log("ℹ️  No tables found in database", Colors.BLUE)
            return True
            
        # Show table information
        self.log(f"📊 Found {len(tables)} tables:", Colors.WHITE)
        total_rows = 0
        
        for table in tables:
            row_count = self.get_table_row_count(table)
            total_rows += row_count
            self.log(f"   • {table}: {row_count} rows", Colors.WHITE)
            
        if total_rows == 0:
            self.log("ℹ️  All tables are already empty", Colors.BLUE)
            return True
            
        # Confirm deletion
        if not self.confirm_action(f"Delete ALL data from {len(tables)} database tables ({total_rows} total rows)?"):
            return False
            
        # Delete data from tables
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Disable foreign key checks temporarily
            cursor.execute("SET session_replication_role = replica;")
            
            deleted_tables = 0
            for table in tables:
                try:
                    self.log(f"🗑️  Deleting data from table: {table}", Colors.YELLOW)
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                    deleted_tables += 1
                    self.log(f"   ✅ Cleared table: {table}", Colors.GREEN)
                except Exception as e:
                    self.log(f"   ❌ Failed to clear table {table}: {str(e)}", Colors.RED)
                    
            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            cursor.close()
            conn.close()
            
            self.log(f"\n✅ Database cleanup completed: {deleted_tables}/{len(tables)} tables cleared", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Database cleanup failed: {str(e)}", Colors.RED)
            return False
            
    def get_s3_objects(self):
        """Get list of all objects in S3 bucket"""
        try:
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.s3_bucket_name):
                if 'Contents' in page:
                    objects.extend(page['Contents'])
                    
            return objects
            
        except Exception as e:
            self.log(f"❌ Failed to list S3 objects: {str(e)}", Colors.RED)
            return []
            
    def cleanup_s3_bucket(self):
        """Delete all objects from S3 bucket"""
        self.log("\n🪣 S3 Bucket Cleanup", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Check if bucket exists and is accessible
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
        except Exception as e:
            self.log(f"❌ Cannot access S3 bucket '{self.s3_bucket_name}': {str(e)}", Colors.RED)
            return False
            
        # Get list of objects
        objects = self.get_s3_objects()
        
        if not objects:
            self.log("ℹ️  S3 bucket is already empty", Colors.BLUE)
            return True
            
        # Calculate total size
        total_size = sum(obj['Size'] for obj in objects)
        size_mb = round(total_size / (1024 * 1024), 2)
        
        self.log(f"📊 Found {len(objects)} objects in S3 bucket:", Colors.WHITE)
        self.log(f"   • Total size: {size_mb} MB", Colors.WHITE)
        
        # Show some example files
        self.log("   • Sample files:", Colors.WHITE)
        for obj in objects[:5]:  # Show first 5 files
            obj_size_kb = round(obj['Size'] / 1024, 2)
            self.log(f"     - {obj['Key']} ({obj_size_kb} KB)", Colors.WHITE)
            
        if len(objects) > 5:
            self.log(f"     ... and {len(objects) - 5} more files", Colors.WHITE)
            
        # Confirm deletion
        if not self.confirm_action(f"Delete ALL {len(objects)} objects from S3 bucket '{self.s3_bucket_name}' ({size_mb} MB)?"):
            return False
            
        # Delete objects in batches
        try:
            batch_size = 1000  # S3 delete limit
            deleted_count = 0
            
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                
                # Prepare delete request
                delete_keys = [{'Key': obj['Key']} for obj in batch]
                
                self.log(f"🗑️  Deleting batch {i//batch_size + 1}: {len(delete_keys)} objects", Colors.YELLOW)
                
                response = self.s3_client.delete_objects(
                    Bucket=self.s3_bucket_name,
                    Delete={'Objects': delete_keys}
                )
                
                # Check for errors
                if 'Errors' in response and response['Errors']:
                    for error in response['Errors']:
                        self.log(f"   ❌ Failed to delete {error['Key']}: {error['Message']}", Colors.RED)
                else:
                    deleted_count += len(delete_keys)
                    self.log(f"   ✅ Deleted {len(delete_keys)} objects", Colors.GREEN)
                    
            self.log(f"\n✅ S3 cleanup completed: {deleted_count}/{len(objects)} objects deleted", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ S3 cleanup failed: {str(e)}", Colors.RED)
            return False
            
    def save_cleanup_log(self):
        """Save cleanup log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"cleanup_log_{timestamp}.txt"
        
        try:
            with open(log_file, 'w') as f:
                f.write("CivicFix AWS Data Cleanup Log\n")
                f.write("=" * 50 + "\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Database: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}\n")
                f.write(f"S3 Bucket: {self.s3_bucket_name}\n")
                f.write(f"AWS Region: {self.aws_region}\n\n")
                
                for entry in self.cleanup_log:
                    # Remove color codes for file output
                    clean_entry = entry
                    for color in [Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE, 
                                Colors.PURPLE, Colors.CYAN, Colors.WHITE, Colors.BOLD, Colors.RESET]:
                        clean_entry = clean_entry.replace(color, '')
                    f.write(clean_entry + "\n")
                    
            self.log(f"📄 Cleanup log saved to: {log_file}", Colors.BLUE)
            
        except Exception as e:
            self.log(f"⚠️  Failed to save log file: {str(e)}", Colors.YELLOW)
            
    def run_cleanup(self):
        """Run the complete cleanup process"""
        self.log(f"🧹 CivicFix AWS Data Cleanup", Colors.BOLD)
        self.log("=" * 50, Colors.BOLD)
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)
        self.log(f"Database: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}", Colors.WHITE)
        self.log(f"S3 Bucket: {self.s3_bucket_name}", Colors.WHITE)
        self.log(f"AWS Region: {self.aws_region}", Colors.WHITE)
        
        # Warning message
        self.log(f"\n⚠️  WARNING: This will permanently delete ALL data!", Colors.RED)
        self.log(f"⚠️  Make sure you have backups if needed!", Colors.RED)
        
        # Final confirmation
        if not self.confirm_action("Proceed with complete data cleanup?"):
            self.log("❌ Cleanup cancelled by user", Colors.YELLOW)
            return
            
        # Run cleanup operations
        db_success = self.cleanup_database()
        s3_success = self.cleanup_s3_bucket()
        
        # Summary
        self.log(f"\n📋 Cleanup Summary", Colors.CYAN)
        self.log("=" * 30, Colors.CYAN)
        
        if db_success:
            self.log("✅ Database cleanup: SUCCESS", Colors.GREEN)
        else:
            self.log("❌ Database cleanup: FAILED", Colors.RED)
            
        if s3_success:
            self.log("✅ S3 bucket cleanup: SUCCESS", Colors.GREEN)
        else:
            self.log("❌ S3 bucket cleanup: FAILED", Colors.RED)
            
        if db_success and s3_success:
            self.log(f"\n🎉 Complete cleanup successful!", Colors.GREEN)
        else:
            self.log(f"\n⚠️  Cleanup completed with errors. Check the log above.", Colors.YELLOW)
            
        # Save log
        self.save_cleanup_log()
        
        self.log(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)

def main():
    """Main function"""
    try:
        cleaner = AWSDataCleaner()
        cleaner.run_cleanup()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}❌ Cleanup interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.RESET}")

if __name__ == "__main__":
    main()
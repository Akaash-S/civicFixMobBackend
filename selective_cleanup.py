#!/usr/bin/env python3
"""
CivicFix Selective Data Cleanup Script
Safely delete specific types of data from RDS and S3

This script allows you to selectively clean up:
- Issues and related data
- User data (except admin users)
- Media files
- Comments
- Specific S3 folders
"""

import os
import sys
import boto3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
from datetime import datetime, timedelta
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

class SelectiveDataCleaner:
    def __init__(self):
        self.load_environment()
        self.setup_aws_clients()
        self.setup_database_connection()
        
    def load_environment(self):
        """Load environment variables"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
            
        self.database_url = os.environ.get('DATABASE_URL')
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        self.aws_region = os.environ.get('AWS_REGION', 'ap-south-1')
        
        if not all([self.database_url, self.aws_access_key, self.aws_secret_key, self.s3_bucket_name]):
            print(f"{Colors.RED}❌ Missing required environment variables{Colors.RESET}")
            sys.exit(1)
            
    def setup_aws_clients(self):
        """Setup AWS clients"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )
        
    def setup_database_connection(self):
        """Setup database connection"""
        parsed_url = urlparse(self.database_url)
        if parsed_url.scheme == 'postgres':
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            
        self.db_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password
        }
        
    def log(self, message, color=Colors.WHITE):
        """Print colored log message"""
        print(f"{color}{message}{Colors.RESET}")
        
    def confirm_action(self, action_description):
        """Get user confirmation"""
        self.log(f"\n⚠️  {action_description}", Colors.YELLOW)
        confirmation = input(f"Type 'yes' to confirm: ").lower()
        return confirmation == 'yes'
        
    def get_db_connection(self):
        """Get database connection"""
        conn = psycopg2.connect(**self.db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
        
    def cleanup_issues_data(self):
        """Delete all issues and related data"""
        self.log("\n🗂️  Issues Data Cleanup", Colors.CYAN)
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get counts first
            cursor.execute("SELECT COUNT(*) FROM issues;")
            issues_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM comments;")
            comments_count = cursor.fetchone()[0]
            
            if issues_count == 0 and comments_count == 0:
                self.log("ℹ️  No issues or comments to delete", Colors.BLUE)
                return True
                
            self.log(f"📊 Found: {issues_count} issues, {comments_count} comments", Colors.WHITE)
            
            if not self.confirm_action(f"Delete all {issues_count} issues and {comments_count} comments?"):
                return False
                
            # Delete in correct order (foreign key constraints)
            cursor.execute("DELETE FROM comments;")
            deleted_comments = cursor.rowcount
            
            cursor.execute("DELETE FROM issues;")
            deleted_issues = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            self.log(f"✅ Deleted {deleted_issues} issues and {deleted_comments} comments", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to cleanup issues: {str(e)}", Colors.RED)
            return False
            
    def cleanup_user_data(self, keep_admin=True):
        """Delete user data (optionally keep admin users)"""
        self.log("\n👥 User Data Cleanup", Colors.CYAN)
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if keep_admin:
                # Count non-admin users
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE email NOT LIKE '%admin%' 
                    AND email NOT LIKE '%@asolvitra.tech';
                """)
                user_count = cursor.fetchone()[0]
                
                if user_count == 0:
                    self.log("ℹ️  No non-admin users to delete", Colors.BLUE)
                    return True
                    
                self.log(f"📊 Found: {user_count} non-admin users", Colors.WHITE)
                
                if not self.confirm_action(f"Delete {user_count} non-admin users (keeping admin accounts)?"):
                    return False
                    
                cursor.execute("""
                    DELETE FROM users 
                    WHERE email NOT LIKE '%admin%' 
                    AND email NOT LIKE '%@asolvitra.tech';
                """)
            else:
                cursor.execute("SELECT COUNT(*) FROM users;")
                user_count = cursor.fetchone()[0]
                
                if user_count == 0:
                    self.log("ℹ️  No users to delete", Colors.BLUE)
                    return True
                    
                if not self.confirm_action(f"Delete ALL {user_count} users?"):
                    return False
                    
                cursor.execute("DELETE FROM users;")
                
            deleted_users = cursor.rowcount
            cursor.close()
            conn.close()
            
            self.log(f"✅ Deleted {deleted_users} users", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to cleanup users: {str(e)}", Colors.RED)
            return False
            
    def cleanup_old_data(self, days=30):
        """Delete data older than specified days"""
        self.log(f"\n📅 Old Data Cleanup (older than {days} days)", Colors.CYAN)
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count old issues
            cursor.execute("""
                SELECT COUNT(*) FROM issues 
                WHERE created_at < %s;
            """, (cutoff_date,))
            old_issues = cursor.fetchone()[0]
            
            # Count old comments
            cursor.execute("""
                SELECT COUNT(*) FROM comments 
                WHERE created_at < %s;
            """, (cutoff_date,))
            old_comments = cursor.fetchone()[0]
            
            if old_issues == 0 and old_comments == 0:
                self.log(f"ℹ️  No data older than {days} days", Colors.BLUE)
                return True
                
            self.log(f"📊 Found: {old_issues} old issues, {old_comments} old comments", Colors.WHITE)
            
            if not self.confirm_action(f"Delete data older than {days} days?"):
                return False
                
            # Delete old comments first
            cursor.execute("""
                DELETE FROM comments 
                WHERE created_at < %s;
            """, (cutoff_date,))
            deleted_comments = cursor.rowcount
            
            # Delete old issues
            cursor.execute("""
                DELETE FROM issues 
                WHERE created_at < %s;
            """, (cutoff_date,))
            deleted_issues = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            self.log(f"✅ Deleted {deleted_issues} old issues and {deleted_comments} old comments", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to cleanup old data: {str(e)}", Colors.RED)
            return False
            
    def cleanup_s3_folder(self, folder_prefix):
        """Delete all objects in a specific S3 folder"""
        self.log(f"\n🗂️  S3 Folder Cleanup: {folder_prefix}", Colors.CYAN)
        
        try:
            # List objects with prefix
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.s3_bucket_name, Prefix=folder_prefix):
                if 'Contents' in page:
                    objects.extend(page['Contents'])
                    
            if not objects:
                self.log(f"ℹ️  No objects found in folder: {folder_prefix}", Colors.BLUE)
                return True
                
            total_size = sum(obj['Size'] for obj in objects)
            size_mb = round(total_size / (1024 * 1024), 2)
            
            self.log(f"📊 Found: {len(objects)} objects ({size_mb} MB)", Colors.WHITE)
            
            if not self.confirm_action(f"Delete {len(objects)} objects from {folder_prefix}?"):
                return False
                
            # Delete objects in batches
            batch_size = 1000
            deleted_count = 0
            
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                delete_keys = [{'Key': obj['Key']} for obj in batch]
                
                response = self.s3_client.delete_objects(
                    Bucket=self.s3_bucket_name,
                    Delete={'Objects': delete_keys}
                )
                
                deleted_count += len(delete_keys)
                
            self.log(f"✅ Deleted {deleted_count} objects from {folder_prefix}", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to cleanup S3 folder: {str(e)}", Colors.RED)
            return False
            
    def cleanup_media_files(self):
        """Delete all media files from S3"""
        media_folders = ['issues/', 'uploads/', 'media/', 'images/']
        
        self.log("\n🖼️  Media Files Cleanup", Colors.CYAN)
        
        success = True
        for folder in media_folders:
            if not self.cleanup_s3_folder(folder):
                success = False
                
        return success
        
    def show_data_summary(self):
        """Show summary of current data"""
        self.log("\n📊 Current Data Summary", Colors.CYAN)
        self.log("=" * 40, Colors.CYAN)
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Database summary
            tables = ['users', 'issues', 'comments']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    self.log(f"📋 {table.capitalize()}: {count} records", Colors.WHITE)
                except:
                    self.log(f"📋 {table.capitalize()}: Table not found", Colors.YELLOW)
                    
            cursor.close()
            conn.close()
            
            # S3 summary
            try:
                objects = []
                paginator = self.s3_client.get_paginator('list_objects_v2')
                
                for page in paginator.paginate(Bucket=self.s3_bucket_name):
                    if 'Contents' in page:
                        objects.extend(page['Contents'])
                        
                total_size = sum(obj['Size'] for obj in objects)
                size_mb = round(total_size / (1024 * 1024), 2)
                
                self.log(f"🪣 S3 Objects: {len(objects)} files ({size_mb} MB)", Colors.WHITE)
                
            except Exception as e:
                self.log(f"🪣 S3 Objects: Error accessing bucket", Colors.YELLOW)
                
        except Exception as e:
            self.log(f"❌ Failed to get data summary: {str(e)}", Colors.RED)
            
    def interactive_cleanup(self):
        """Interactive cleanup menu"""
        self.log(f"🧹 CivicFix Selective Data Cleanup", Colors.BOLD)
        self.log("=" * 50, Colors.BOLD)
        
        while True:
            self.show_data_summary()
            
            self.log(f"\n🔧 Cleanup Options:", Colors.CYAN)
            self.log("1. Delete all issues and comments", Colors.WHITE)
            self.log("2. Delete non-admin users", Colors.WHITE)
            self.log("3. Delete ALL users", Colors.WHITE)
            self.log("4. Delete old data (30+ days)", Colors.WHITE)
            self.log("5. Delete media files (S3)", Colors.WHITE)
            self.log("6. Delete specific S3 folder", Colors.WHITE)
            self.log("7. Show data summary", Colors.WHITE)
            self.log("0. Exit", Colors.WHITE)
            
            choice = input(f"\nSelect option (0-7): ").strip()
            
            if choice == '0':
                self.log("👋 Goodbye!", Colors.GREEN)
                break
            elif choice == '1':
                self.cleanup_issues_data()
            elif choice == '2':
                self.cleanup_user_data(keep_admin=True)
            elif choice == '3':
                self.cleanup_user_data(keep_admin=False)
            elif choice == '4':
                days = input("Enter number of days (default 30): ").strip()
                days = int(days) if days.isdigit() else 30
                self.cleanup_old_data(days)
            elif choice == '5':
                self.cleanup_media_files()
            elif choice == '6':
                folder = input("Enter S3 folder prefix (e.g., 'uploads/'): ").strip()
                if folder:
                    self.cleanup_s3_folder(folder)
            elif choice == '7':
                continue  # Will show summary at top of loop
            else:
                self.log("❌ Invalid option", Colors.RED)
                
            input(f"\nPress Enter to continue...")

def main():
    """Main function"""
    try:
        cleaner = SelectiveDataCleaner()
        cleaner.interactive_cleanup()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}❌ Cleanup interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {str(e)}{Colors.RESET}")

if __name__ == "__main__":
    main()
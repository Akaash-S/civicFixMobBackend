#!/usr/bin/env python3
"""
Database Initialization Script for CivicFix
Automatically creates all tables and indexes using SQLAlchemy
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables and indexes"""
    try:
        # Import app and db after environment is loaded
        from app import app, db
        
        logger.info("=" * 60)
        logger.info("CivicFix Database Initialization")
        logger.info("=" * 60)
        logger.info("")
        
        # Check database connection
        logger.info("🔌 Testing database connection...")
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found in environment variables")
            return False
        
        # Hide password in log
        safe_url = database_url.split('@')[1] if '@' in database_url else database_url
        logger.info(f"   Database: {safe_url}")
        
        with app.app_context():
            # Test connection
            try:
                db.session.execute(db.text('SELECT 1'))
                logger.info("✅ Database connection successful")
                logger.info("")
            except Exception as e:
                logger.error(f"❌ Database connection failed: {e}")
                return False
            
            # Check existing tables
            logger.info("📋 Checking existing tables...")
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                logger.info(f"   Found {len(existing_tables)} existing tables:")
                for table in existing_tables:
                    logger.info(f"   - {table}")
            else:
                logger.info("   No existing tables found")
            logger.info("")
            
            # Create tables
            logger.info("🔨 Creating tables...")
            db.create_all()
            logger.info("✅ Tables created successfully")
            logger.info("")
            
            # Create indexes
            logger.info("🔧 Creating indexes...")
            indexes_created = 0
            indexes_skipped = 0
            
            indexes_to_create = [
                ("idx_users_firebase_uid", "users", "firebase_uid"),
                ("idx_users_email", "users", "email"),
                ("idx_issues_created_by", "issues", "created_by"),
                ("idx_issues_category", "issues", "category"),
                ("idx_issues_status", "issues", "status"),
                ("idx_comments_issue_id", "comments", "issue_id"),
                ("idx_comments_user_id", "comments", "user_id"),
            ]
            
            for index_name, table_name, column_name in indexes_to_create:
                try:
                    # Use a new connection for each index to avoid transaction issues
                    with db.engine.begin() as conn:
                        # Check if index exists
                        result = conn.execute(db.text(f"""
                            SELECT 1 FROM pg_indexes 
                            WHERE indexname = '{index_name}'
                        """))
                        
                        if not result.fetchone():
                            # Create index
                            conn.execute(db.text(f"""
                                CREATE INDEX IF NOT EXISTS {index_name} 
                                ON {table_name}({column_name})
                            """))
                            logger.info(f"   ✅ Created: {index_name}")
                            indexes_created += 1
                        else:
                            logger.info(f"   ⏭️  Skipped: {index_name} (already exists)")
                            indexes_skipped += 1
                except Exception as idx_error:
                    logger.warning(f"   ⚠️  Failed: {index_name} - {idx_error}")
            
            logger.info("")
            logger.info(f"📊 Index Summary: {indexes_created} created, {indexes_skipped} skipped")
            logger.info("")
            
            # Verify final state
            logger.info("🔍 Verifying database structure...")
            inspector = db.inspect(db.engine)
            final_tables = inspector.get_table_names()
            
            logger.info(f"✅ Database has {len(final_tables)} tables:")
            for table in final_tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                logger.info(f"   📊 {table}:")
                logger.info(f"      - Columns: {len(columns)}")
                logger.info(f"      - Indexes: {len(indexes)}")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ Database initialization completed successfully!")
            logger.info("=" * 60)
            
            return True
            
    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False

def check_supabase_storage():
    """Check Supabase Storage configuration"""
    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Supabase Storage Check")
        logger.info("=" * 60)
        logger.info("")
        
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        supabase_service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'civicfix-media')
        
        if not supabase_url or not supabase_key:
            logger.warning("⚠️  Supabase credentials not configured")
            logger.info("   Set SUPABASE_URL and SUPABASE_KEY in .env")
            return False
        
        logger.info(f"🔌 Connecting to Supabase...")
        logger.info(f"   URL: {supabase_url}")
        
        from supabase import create_client
        
        storage_key = supabase_service_key or supabase_key
        supabase = create_client(supabase_url, storage_key)
        storage = supabase.storage
        
        # List buckets
        logger.info("📦 Checking storage buckets...")
        buckets = storage.list_buckets()
        
        if buckets:
            logger.info(f"   Found {len(buckets)} buckets:")
            for bucket in buckets:
                logger.info(f"   - {bucket.name} (public: {bucket.public})")
        else:
            logger.info("   No buckets found")
        
        # Check if our bucket exists
        bucket_exists = any(b.name == bucket_name for b in buckets)
        
        if bucket_exists:
            logger.info(f"✅ Bucket '{bucket_name}' exists")
        else:
            logger.warning(f"⚠️  Bucket '{bucket_name}' not found")
            logger.info(f"   Creating bucket '{bucket_name}'...")
            
            try:
                storage.create_bucket(
                    bucket_name,
                    options={'public': True}
                )
                logger.info(f"✅ Created public bucket: {bucket_name}")
            except Exception as e:
                logger.error(f"❌ Failed to create bucket: {e}")
                logger.info("   Please create the bucket manually in Supabase dashboard:")
                logger.info(f"   1. Go to {supabase_url}")
                logger.info("   2. Navigate to Storage")
                logger.info(f"   3. Create bucket '{bucket_name}' and make it public")
                return False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Supabase Storage check completed!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase Storage check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    logger.info("")
    logger.info("🚀 CivicFix Initialization Script")
    logger.info("")
    
    # Initialize database
    db_success = init_database()
    
    # Check Supabase Storage
    storage_success = check_supabase_storage()
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Initialization Summary")
    logger.info("=" * 60)
    logger.info(f"Database: {'✅ Success' if db_success else '❌ Failed'}")
    logger.info(f"Storage:  {'✅ Success' if storage_success else '❌ Failed'}")
    logger.info("=" * 60)
    logger.info("")
    
    if db_success and storage_success:
        logger.info("✅ All systems initialized successfully!")
        logger.info("   You can now start the application.")
        sys.exit(0)
    else:
        logger.error("❌ Initialization incomplete. Please fix the errors above.")
        sys.exit(1)

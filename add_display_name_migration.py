#!/usr/bin/env python3
"""
Database Migration: Add Display Name Column
Adds display_name column to the users table for user-customizable names
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Handle PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url)

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def add_display_name_column():
    """Add display_name column to users table"""
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Check if display_name column exists
        logger.info("Checking if display_name column exists...")
        
        if check_column_exists(cursor, 'users', 'display_name'):
            logger.info("✅ Column 'display_name' already exists")
        else:
            logger.info("➕ Adding display_name column...")
            
            # Add the column
            alter_sql = "ALTER TABLE users ADD COLUMN display_name VARCHAR(255);"
            cursor.execute(alter_sql)
            
            logger.info("✅ Successfully added display_name column")
        
        # Set default display_name values for existing users (copy from name)
        logger.info("🔄 Setting default display_name values for existing users...")
        
        update_sql = """
            UPDATE users 
            SET display_name = name 
            WHERE display_name IS NULL OR display_name = '';
        """
        cursor.execute(update_sql)
        
        # Get count of users updated
        cursor.execute("SELECT COUNT(*) FROM users WHERE display_name IS NOT NULL;")
        user_count = cursor.fetchone()[0]
        logger.info(f"📊 Set display_name for {user_count} users")
        
        # Verify the column exists and has data
        logger.info("\n🔍 Verifying display_name column:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'display_name';
        """)
        
        column_info = cursor.fetchone()
        if column_info:
            column_name, data_type, is_nullable, default_value = column_info
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {default_value}" if default_value else ""
            logger.info(f"  {column_name}: {data_type} {nullable}{default}")
        
        # Show sample data
        logger.info("\n📋 Sample display_name data:")
        cursor.execute("SELECT name, display_name FROM users LIMIT 5;")
        samples = cursor.fetchall()
        for name, display_name in samples:
            logger.info(f"  name: '{name}' -> display_name: '{display_name}'")
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("Display name column has been added to the users table.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def rollback_migration():
    """Rollback the migration by removing display_name column"""
    
    try:
        logger.info("🔄 Rolling back display_name column migration...")
        
        # Connect to database
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        if check_column_exists(cursor, 'users', 'display_name'):
            logger.info("➖ Removing display_name column...")
            cursor.execute("ALTER TABLE users DROP COLUMN display_name;")
            logger.info("✅ Removed display_name column")
        else:
            logger.info("⚠️ Column 'display_name' doesn't exist, skipping")
        
        logger.info("🎉 Rollback completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Display Name Database Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Display Name Database Migration")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        if args.rollback:
            rollback_migration()
        else:
            add_display_name_column()
            
    except Exception as e:
        logger.error(f"💥 Migration script failed: {e}")
        sys.exit(1)
    
    logger.info("✨ Migration script completed successfully!")
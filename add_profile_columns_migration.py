#!/usr/bin/env python3
"""
Database Migration: Add Profile Management Columns
Adds bio and settings columns to the users table
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

def add_profile_columns():
    """Add profile management columns to users table"""
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # List of columns to add
        columns_to_add = [
            {
                'name': 'bio',
                'definition': 'TEXT',
                'description': 'User biography'
            },
            {
                'name': 'notifications_enabled',
                'definition': 'BOOLEAN DEFAULT TRUE',
                'description': 'Push notifications setting'
            },
            {
                'name': 'dark_mode',
                'definition': 'BOOLEAN DEFAULT FALSE',
                'description': 'Dark mode preference'
            },
            {
                'name': 'anonymous_reporting',
                'definition': 'BOOLEAN DEFAULT FALSE',
                'description': 'Anonymous reporting setting'
            },
            {
                'name': 'satellite_view',
                'definition': 'BOOLEAN DEFAULT FALSE',
                'description': 'Satellite map view preference'
            },
            {
                'name': 'save_to_gallery',
                'definition': 'BOOLEAN DEFAULT TRUE',
                'description': 'Save photos to gallery setting'
            }
        ]
        
        # Check and add each column
        for column in columns_to_add:
            column_name = column['name']
            column_definition = column['definition']
            description = column['description']
            
            logger.info(f"Checking column: {column_name}")
            
            if check_column_exists(cursor, 'users', column_name):
                logger.info(f"✅ Column '{column_name}' already exists")
            else:
                logger.info(f"➕ Adding column '{column_name}' ({description})")
                
                # Add the column
                alter_sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_definition};"
                cursor.execute(alter_sql)
                
                logger.info(f"✅ Successfully added column '{column_name}'")
        
        # Verify all columns exist
        logger.info("\n🔍 Verifying all columns exist:")
        for column in columns_to_add:
            column_name = column['name']
            exists = check_column_exists(cursor, 'users', column_name)
            status = "✅ EXISTS" if exists else "❌ MISSING"
            logger.info(f"  {column_name}: {status}")
        
        # Get table structure
        logger.info("\n📋 Current users table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            column_name, data_type, is_nullable, default_value = col
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {default_value}" if default_value else ""
            logger.info(f"  {column_name}: {data_type} {nullable}{default}")
        
        # Update existing users with default values
        logger.info("\n🔄 Setting default values for existing users...")
        
        update_queries = [
            "UPDATE users SET bio = '' WHERE bio IS NULL;",
            "UPDATE users SET notifications_enabled = TRUE WHERE notifications_enabled IS NULL;",
            "UPDATE users SET dark_mode = FALSE WHERE dark_mode IS NULL;",
            "UPDATE users SET anonymous_reporting = FALSE WHERE anonymous_reporting IS NULL;",
            "UPDATE users SET satellite_view = FALSE WHERE satellite_view IS NULL;",
            "UPDATE users SET save_to_gallery = TRUE WHERE save_to_gallery IS NULL;"
        ]
        
        for query in update_queries:
            cursor.execute(query)
            logger.info(f"✅ Executed: {query}")
        
        # Get count of users updated
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"📊 Updated {user_count} existing users with default values")
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("All profile management columns have been added to the users table.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def rollback_migration():
    """Rollback the migration by removing added columns"""
    
    try:
        logger.info("🔄 Rolling back profile columns migration...")
        
        # Connect to database
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Columns to remove
        columns_to_remove = [
            'bio',
            'notifications_enabled', 
            'dark_mode',
            'anonymous_reporting',
            'satellite_view',
            'save_to_gallery'
        ]
        
        for column_name in columns_to_remove:
            if check_column_exists(cursor, 'users', column_name):
                logger.info(f"➖ Removing column: {column_name}")
                cursor.execute(f"ALTER TABLE users DROP COLUMN {column_name};")
                logger.info(f"✅ Removed column: {column_name}")
            else:
                logger.info(f"⚠️ Column '{column_name}' doesn't exist, skipping")
        
        logger.info("🎉 Rollback completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Profile Management Database Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Profile Management Database Migration")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        if args.rollback:
            rollback_migration()
        else:
            add_profile_columns()
            
    except Exception as e:
        logger.error(f"💥 Migration script failed: {e}")
        sys.exit(1)
    
    logger.info("✨ Migration script completed successfully!")
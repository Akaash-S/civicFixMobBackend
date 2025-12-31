#!/usr/bin/env python3
"""
Database Migration: Add Onboarding Fields
Adds password_hash, language, and onboarding_completed fields to users table
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

def add_onboarding_fields():
    """Add onboarding fields to users table"""
    
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
                'name': 'password_hash',
                'definition': 'VARCHAR(255)',
                'description': 'Hashed password for account security'
            },
            {
                'name': 'language',
                'definition': "VARCHAR(10) DEFAULT 'en'",
                'description': 'User preferred language (en, ta, etc.)'
            },
            {
                'name': 'onboarding_completed',
                'definition': 'BOOLEAN DEFAULT FALSE',
                'description': 'Whether user has completed onboarding flow'
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
        
        # Set default values for existing users
        logger.info("🔄 Setting default values for existing users...")
        
        update_queries = [
            "UPDATE users SET language = 'en' WHERE language IS NULL;",
            "UPDATE users SET onboarding_completed = TRUE WHERE onboarding_completed IS NULL;",  # Existing users skip onboarding
        ]
        
        for query in update_queries:
            cursor.execute(query)
            logger.info(f"✅ Executed: {query}")
        
        # Verify all columns exist
        logger.info("\n🔍 Verifying all columns exist:")
        for column in columns_to_add:
            column_name = column['name']
            exists = check_column_exists(cursor, 'users', column_name)
            status = "✅ EXISTS" if exists else "❌ MISSING"
            logger.info(f"  {column_name}: {status}")
        
        # Get table structure for onboarding fields
        logger.info("\n📋 Onboarding fields in users table:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('password_hash', 'language', 'onboarding_completed')
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            column_name, data_type, is_nullable, default_value = col
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {default_value}" if default_value else ""
            logger.info(f"  {column_name}: {data_type} {nullable}{default}")
        
        # Get count of users
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"📊 Total users in database: {user_count}")
        
        # Show sample data
        logger.info("\n📋 Sample onboarding data:")
        cursor.execute("SELECT name, language, onboarding_completed FROM users LIMIT 5;")
        samples = cursor.fetchall()
        for name, language, onboarding_completed in samples:
            status = "✅ Completed" if onboarding_completed else "❌ Pending"
            logger.info(f"  {name}: language={language}, onboarding={status}")
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("Onboarding fields have been added to the users table.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def rollback_migration():
    """Rollback the migration by removing onboarding fields"""
    
    try:
        logger.info("🔄 Rolling back onboarding fields migration...")
        
        # Connect to database
        conn = get_database_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Columns to remove
        columns_to_remove = [
            'password_hash',
            'language', 
            'onboarding_completed'
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
    
    parser = argparse.ArgumentParser(description='Onboarding Fields Database Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Onboarding Fields Database Migration")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        if args.rollback:
            rollback_migration()
        else:
            add_onboarding_fields()
            
    except Exception as e:
        logger.error(f"💥 Migration script failed: {e}")
        sys.exit(1)
    
    logger.info("✨ Migration script completed successfully!")
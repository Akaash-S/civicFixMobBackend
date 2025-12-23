#!/usr/bin/env python3
"""
CivicFix Backend - Database Cleanup Script
Safely removes all data from AWS RDS database while preserving table structure
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def confirm_deletion():
    """Ask for user confirmation before deleting data"""
    print("⚠️  WARNING: This will DELETE ALL DATA from the database!")
    print("   This action cannot be undone.")
    print("   Tables will remain but all records will be deleted.")
    print()
    
    database_url = os.environ.get('DATABASE_URL', 'Not configured')
    if 'civicfix-db.ctousuwme9up.ap-south-1.rds.amazonaws.com' in database_url:
        print(f"🎯 Target Database: AWS RDS Production Database")
        print(f"   Host: civicfix-db.ctousuwme9up.ap-south-1.rds.amazonaws.com")
        print(f"   Database: civicfix-db")
    else:
        print(f"🎯 Target Database: {database_url}")
    
    print()
    response = input("Type 'DELETE ALL DATA' to confirm (case sensitive): ")
    
    if response != 'DELETE ALL DATA':
        print("❌ Operation cancelled - confirmation text did not match")
        return False
    
    print()
    final_confirm = input("Are you absolutely sure? Type 'YES' to proceed: ")
    
    if final_confirm != 'YES':
        print("❌ Operation cancelled")
        return False
    
    return True

def get_table_deletion_order():
    """Define the order to delete tables to respect foreign key constraints"""
    # Delete in reverse dependency order to avoid foreign key violations
    return [
        'issues',      # Has foreign key to users
        'users',       # Base table
        # Add other tables here in proper order if they exist
    ]

def clear_database():
    """Clear all data from the database"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is required")
        return False
    
    # Handle PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("🔄 Connecting to AWS RDS database...")
    
    try:
        engine = create_engine(database_url, connect_args={
            "connect_timeout": 30,
            "application_name": "civicfix_cleanup"
        })
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("📊 Analyzing database structure...")
                
                # Get all table names
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                
                existing_tables = [row[0] for row in result.fetchall()]
                print(f"   Found tables: {', '.join(existing_tables)}")
                
                if not existing_tables:
                    print("✅ No tables found - database is already empty")
                    return True
                
                # Get deletion order
                deletion_order = get_table_deletion_order()
                
                # Filter to only existing tables and add any missing ones
                tables_to_clear = []
                for table in deletion_order:
                    if table in existing_tables:
                        tables_to_clear.append(table)
                
                # Add any tables not in our predefined order
                for table in existing_tables:
                    if table not in tables_to_clear:
                        tables_to_clear.append(table)
                
                print(f"📝 Deletion order: {' → '.join(tables_to_clear)}")
                print()
                
                # Disable foreign key checks temporarily (PostgreSQL)
                print("🔓 Temporarily disabling foreign key constraints...")
                conn.execute(text("SET session_replication_role = replica;"))
                
                # Clear each table
                total_deleted = 0
                for table_name in tables_to_clear:
                    print(f"🗑️  Clearing table: {table_name}")
                    
                    # Get count before deletion
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    record_count = count_result.fetchone()[0]
                    
                    if record_count > 0:
                        # Delete all records
                        conn.execute(text(f"DELETE FROM {table_name}"))
                        
                        # Reset auto-increment sequences if they exist
                        try:
                            conn.execute(text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1"))
                            print(f"   ↻ Reset sequence for {table_name}")
                        except SQLAlchemyError:
                            # Sequence might not exist, that's okay
                            pass
                        
                        print(f"   ✅ Deleted {record_count} records from {table_name}")
                        total_deleted += record_count
                    else:
                        print(f"   ℹ️  Table {table_name} was already empty")
                
                # Re-enable foreign key checks
                print("🔒 Re-enabling foreign key constraints...")
                conn.execute(text("SET session_replication_role = DEFAULT;"))
                
                # Commit transaction
                trans.commit()
                
                print()
                print("✅ Database cleanup completed successfully!")
                print(f"📊 Summary:")
                print(f"   - Tables processed: {len(tables_to_clear)}")
                print(f"   - Total records deleted: {total_deleted}")
                print(f"   - Table structure preserved: ✅")
                print(f"   - Sequences reset: ✅")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Database cleanup failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def verify_cleanup():
    """Verify that the database is empty"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        return False
    
    # Handle PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        engine = create_engine(database_url, connect_args={
            "connect_timeout": 30,
            "application_name": "civicfix_cleanup_verify"
        })
        
        with engine.connect() as conn:
            print("🔍 Verifying database cleanup...")
            
            # Get all table names and their record counts
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins - n_tup_del as record_count
                FROM pg_stat_user_tables
                ORDER BY tablename
            """))
            
            tables_info = result.fetchall()
            
            if not tables_info:
                print("✅ No user tables found - database is clean")
                return True
            
            all_empty = True
            for schema, table, count in tables_info:
                # Double-check with direct count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                actual_count = count_result.fetchone()[0]
                
                if actual_count > 0:
                    print(f"⚠️  Table {table} still has {actual_count} records")
                    all_empty = False
                else:
                    print(f"✅ Table {table} is empty")
            
            if all_empty:
                print("🎉 All tables are empty - cleanup verified!")
                return True
            else:
                print("❌ Some tables still contain data")
                return False
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("🗑️  CivicFix Backend - Database Cleanup Tool")
    print("=" * 50)
    
    # Check if database URL is configured
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable is not configured")
        print("   Please ensure your .env file is properly set up")
        sys.exit(1)
    
    # Get user confirmation
    if not confirm_deletion():
        sys.exit(0)
    
    print("\n🚀 Starting database cleanup...")
    print("-" * 30)
    
    # Clear the database
    success = clear_database()
    
    if success:
        print("\n🔍 Verifying cleanup...")
        print("-" * 20)
        verify_cleanup()
        
        print("\n🎉 Database cleanup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart your backend: python app.py")
        print("   2. Tables will be recreated automatically")
        print("   3. Database will be ready for fresh data")
    else:
        print("\n❌ Database cleanup failed!")
        print("   Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
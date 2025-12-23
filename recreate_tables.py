#!/usr/bin/env python3
"""
CivicFix Backend - Recreate Tables Script
Drops existing tables and recreates them with correct schema
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def recreate_tables():
    """Drop and recreate all tables"""
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
            "application_name": "civicfix_recreate"
        })
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("🗑️  Dropping existing tables...")
                
                # Drop tables in correct order (reverse dependency)
                tables_to_drop = ['issues', 'users']
                
                for table in tables_to_drop:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                        print(f"   ✅ Dropped table: {table}")
                    except Exception as e:
                        print(f"   ⚠️  Could not drop {table}: {e}")
                
                # Drop sequences if they exist
                sequences_to_drop = ['users_id_seq', 'issues_id_seq']
                for seq in sequences_to_drop:
                    try:
                        conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq} CASCADE"))
                        print(f"   ✅ Dropped sequence: {seq}")
                    except Exception as e:
                        print(f"   ⚠️  Could not drop sequence {seq}: {e}")
                
                # Drop custom types if they exist
                custom_types = ['user_role', 'issue_category', 'issue_status', 'issue_priority']
                for custom_type in custom_types:
                    try:
                        conn.execute(text(f"DROP TYPE IF EXISTS {custom_type} CASCADE"))
                        print(f"   ✅ Dropped type: {custom_type}")
                    except Exception as e:
                        print(f"   ⚠️  Could not drop type {custom_type}: {e}")
                
                print("\n🏗️  Creating new tables with correct schema...")
                
                # Create users table
                conn.execute(text("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        firebase_uid VARCHAR(128) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        phone VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("   ✅ Created users table")
                
                # Create issues table
                conn.execute(text("""
                    CREATE TABLE issues (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        category VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'OPEN',
                        priority VARCHAR(50) DEFAULT 'MEDIUM',
                        latitude FLOAT NOT NULL,
                        longitude FLOAT NOT NULL,
                        address VARCHAR(500),
                        image_url VARCHAR(500),
                        image_urls TEXT,
                        created_by INTEGER NOT NULL REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("   ✅ Created issues table")
                
                # Create indexes for better performance
                conn.execute(text("CREATE INDEX idx_users_firebase_uid ON users(firebase_uid)"))
                conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))
                conn.execute(text("CREATE INDEX idx_issues_created_by ON issues(created_by)"))
                conn.execute(text("CREATE INDEX idx_issues_status ON issues(status)"))
                conn.execute(text("CREATE INDEX idx_issues_category ON issues(category)"))
                conn.execute(text("CREATE INDEX idx_issues_location ON issues(latitude, longitude)"))
                print("   ✅ Created indexes")
                
                # Commit transaction
                trans.commit()
                
                print("\n✅ Tables recreated successfully!")
                
                # Show final schema
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position
                """))
                print("\n📊 New schema:")
                print("   Users table:")
                for row in result:
                    print(f"     {row[0]} - {row[1]} - nullable: {row[2]}")
                
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'issues' 
                    ORDER BY ordinal_position
                """))
                print("   Issues table:")
                for row in result:
                    print(f"     {row[0]} - {row[1]} - nullable: {row[2]}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Table recreation failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🏗️  CivicFix Backend - Recreate Tables Tool")
    print("=" * 50)
    
    # Check if database URL is configured
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable is not configured")
        print("   Please ensure your .env file is properly set up")
        sys.exit(1)
    
    print("⚠️  WARNING: This will DROP ALL TABLES and recreate them!")
    print("   ALL DATA WILL BE LOST!")
    print("   Tables will be recreated with the correct schema")
    print()
    
    database_url = os.environ.get('DATABASE_URL', 'Not configured')
    if 'civicfix-db.ctousuwme9up.ap-south-1.rds.amazonaws.com' in database_url:
        print(f"🎯 Target Database: AWS RDS Production Database")
        print(f"   Host: civicfix-db.ctousuwme9up.ap-south-1.rds.amazonaws.com")
        print(f"   Database: civicfix-db")
    else:
        print(f"🎯 Target Database: {database_url}")
    
    print()
    response = input("Type 'RECREATE TABLES' to confirm (case sensitive): ")
    
    if response != 'RECREATE TABLES':
        print("❌ Operation cancelled - confirmation text did not match")
        sys.exit(0)
    
    print("\n🚀 Starting table recreation...")
    print("-" * 30)
    
    # Recreate the tables
    success = recreate_tables()
    
    if success:
        print("\n🎉 Tables recreated successfully!")
        print("\n📝 Next steps:")
        print("   1. Start your backend: python app.py")
        print("   2. Test API endpoints: python test-api-endpoints.py")
        print("   3. Database now has correct schema matching current models")
    else:
        print("\n❌ Table recreation failed!")
        print("   Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
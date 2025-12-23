#!/usr/bin/env python3
"""
CivicFix Backend - Database Migration Script
Migrates AWS RDS database schema for new features
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def migrate_database():
    """Migrate database schema"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is required")
        return False
    
    # Handle PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔄 Migrating AWS RDS database...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if phone column exists in users table
            try:
                result = conn.execute(text("SELECT phone FROM users LIMIT 1"))
                print("✅ users.phone column already exists")
            except SQLAlchemyError:
                print("📝 Adding phone column to users table...")
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                    conn.commit()
                    print("✅ Added phone column to users table")
                except SQLAlchemyError as e:
                    if "already exists" in str(e):
                        print("✅ phone column already exists")
                    else:
                        print(f"⚠️ Could not add phone column: {e}")
            
            # Check if image_urls column exists in issues table
            try:
                result = conn.execute(text("SELECT image_urls FROM issues LIMIT 1"))
                print("✅ issues.image_urls column already exists")
            except SQLAlchemyError:
                print("📝 Adding image_urls column to issues table...")
                try:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN image_urls TEXT"))
                    conn.commit()
                    print("✅ Added image_urls column to issues table")
                    
                    # Migrate data from image_url to image_urls
                    result = conn.execute(text("SELECT id, image_url FROM issues WHERE image_url IS NOT NULL AND image_url != ''"))
                    rows = result.fetchall()
                    
                    for row in rows:
                        issue_id, image_url = row
                        # Convert single URL to JSON array
                        image_urls_json = json.dumps([image_url])
                        conn.execute(
                            text("UPDATE issues SET image_urls = :image_urls WHERE id = :id"),
                            {"image_urls": image_urls_json, "id": issue_id}
                        )
                    
                    conn.commit()
                    print(f"✅ Migrated {len(rows)} issues with image URLs")
                except SQLAlchemyError as e:
                    if "already exists" in str(e):
                        print("✅ image_urls column already exists")
                    else:
                        print(f"⚠️ Could not add image_urls column: {e}")
            
            print("✅ Database migration completed successfully!")
            return True
                
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

def main():
    """Main function"""
    print("CivicFix Database Migration")
    print("=" * 40)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now start the backend with: python app.py")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
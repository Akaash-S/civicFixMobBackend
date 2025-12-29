#!/usr/bin/env python3
"""
Add updated_at column to comments table
This script adds the missing updated_at column to match the backend model
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def add_updated_at_column():
    """Add updated_at column to comments table"""
    try:
        with app.app_context():
            # Check current schema
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'comments' 
                ORDER BY ordinal_position;
            """))
            
            columns = [row[0] for row in result]
            print("📋 Current comments table columns:")
            for col in columns:
                print(f"  - {col}")
            
            # Add updated_at column if it doesn't exist
            if 'updated_at' not in columns:
                print("\n🔄 Adding updated_at column...")
                db.session.execute(text("""
                    ALTER TABLE comments 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """))
                
                # Update existing records to have updated_at = created_at
                db.session.execute(text("""
                    UPDATE comments 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL;
                """))
                
                db.session.commit()
                print("✅ updated_at column added successfully!")
                
            else:
                print("✅ updated_at column already exists")
            
            # Verify the addition
            result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'comments' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Updated comments table schema:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error adding updated_at column: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("🔧 Adding updated_at column to comments table")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success = add_updated_at_column()
    
    if success:
        print("\n🎉 Column addition completed successfully!")
        print("💡 Comments table now has updated_at column")
    else:
        print("\n💥 Column addition failed!")
        sys.exit(1)
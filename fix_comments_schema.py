#!/usr/bin/env python3
"""
Fix Comments Table Schema
This script fixes the column name mismatch in the comments table
Changes 'text' column to 'content' to match the backend model
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def fix_comments_schema():
    """Fix the comments table schema to match backend expectations"""
    try:
        with app.app_context():
            # Check if comments table exists and what columns it has
            result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'comments' 
                ORDER BY ordinal_position;
            """))
            
            columns = {row[0]: row[1] for row in result}
            print("📋 Current comments table schema:")
            for col_name, col_type in columns.items():
                print(f"  - {col_name}: {col_type}")
            
            # Check if we need to rename 'text' to 'content'
            if 'text' in columns and 'content' not in columns:
                print("\n🔄 Renaming 'text' column to 'content'...")
                db.session.execute(text("""
                    ALTER TABLE comments RENAME COLUMN text TO content;
                """))
                db.session.commit()
                print("✅ Column renamed successfully!")
                
            elif 'content' in columns:
                print("✅ Comments table already has 'content' column")
                
            else:
                print("❌ Comments table structure is unexpected")
                return False
            
            # Verify the fix
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
        print(f"❌ Error fixing comments schema: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("🔧 Fixing Comments Table Schema")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success = fix_comments_schema()
    
    if success:
        print("\n🎉 Comments schema fix completed successfully!")
        print("💡 Comments functionality should now work properly")
    else:
        print("\n💥 Comments schema fix failed!")
        sys.exit(1)
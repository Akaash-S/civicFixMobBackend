#!/usr/bin/env python3
"""
Create comments table migration script
Run this to add the comments table to your database
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def create_comments_table():
    """Create the comments table with proper schema"""
    try:
        with app.app_context():
            # Create the comments table with raw SQL to ensure proper schema
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes for better performance
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_comments_issue_id ON comments(issue_id);
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
            """))
            
            # Commit the changes
            db.session.commit()
            
            print("✅ Comments table created successfully!")
            print("📊 Database schema updated")
            
            # Verify the table was created
            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'comments';"))
            if result.fetchone():
                print("✅ Comments table verified in database")
                
                # Show table structure
                columns_result = db.session.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'comments' 
                    ORDER BY ordinal_position;
                """))
                
                print("\n📋 Comments table structure:")
                for row in columns_result:
                    print(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ Comments table not found after creation")
                return False
                
            return True
            
    except Exception as e:
        print(f"❌ Error creating comments table: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("🚀 Creating comments table...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success = create_comments_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("💡 You can now use the commenting functionality")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
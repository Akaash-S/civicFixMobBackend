#!/usr/bin/env python3
"""
Add upvotes column to issues table and reset all upvotes to 0
"""

import os
import psycopg2
from dotenv import load_dotenv

def add_upvotes_column():
    """Add upvotes column to issues table"""
    print("🔧 Adding upvotes column to issues table")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False
        
        print(f"📊 Connecting to database...")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if upvotes column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'issues' AND column_name = 'upvotes'
        """)
        
        if cursor.fetchone():
            print("✅ upvotes column already exists")
            
            # Reset all upvotes to 0
            print("🔄 Resetting all upvotes to 0...")
            cursor.execute("UPDATE issues SET upvotes = 0")
            affected_rows = cursor.rowcount
            print(f"✅ Reset upvotes for {affected_rows} issues")
            
        else:
            # Add upvotes column
            print("➕ Adding upvotes column...")
            cursor.execute("""
                ALTER TABLE issues 
                ADD COLUMN upvotes INTEGER DEFAULT 0 NOT NULL
            """)
            print("✅ upvotes column added successfully")
            
            # Update all existing records to have 0 upvotes
            cursor.execute("UPDATE issues SET upvotes = 0")
            affected_rows = cursor.rowcount
            print(f"✅ Set upvotes to 0 for {affected_rows} existing issues")
        
        # Commit changes
        conn.commit()
        
        # Verify the column
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'issues' AND column_name = 'upvotes'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Column verified:")
            print(f"   Name: {result[0]}")
            print(f"   Type: {result[1]}")
            print(f"   Default: {result[2]}")
            print(f"   Nullable: {result[3]}")
        
        # Show sample data
        cursor.execute("SELECT id, title, upvotes FROM issues LIMIT 5")
        sample_issues = cursor.fetchall()
        
        if sample_issues:
            print(f"\n📋 Sample issues with upvotes:")
            for issue in sample_issues:
                print(f"   ID {issue[0]}: '{issue[1][:30]}...' - {issue[2]} upvotes")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🗄️ Database Migration: Add Upvotes Column")
    print("=" * 60)
    
    success = add_upvotes_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ upvotes column added to issues table")
        print("✅ All upvotes reset to 0")
        print("\nNext steps:")
        print("1. Update the Issue model in app.py")
        print("2. Remove like icons from frontend components")
        print("3. Redesign my-reports screen")
    else:
        print("\n❌ Migration failed")
        print("Check database connection and try again")
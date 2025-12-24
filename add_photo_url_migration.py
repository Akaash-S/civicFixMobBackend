#!/usr/bin/env python3
"""
Database Migration: Add photo_url column to users table
Run this script to add the photo_url column to existing users table
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is required")
        sys.exit(1)
    
    # Handle PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if column already exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'photo_url'
            """))
            
            if result.fetchone():
                print("Column 'photo_url' already exists in users table")
                return
            
            # Add the column
            conn.execute(text("ALTER TABLE users ADD COLUMN photo_url VARCHAR(500)"))
            conn.commit()
            
            print("Successfully added 'photo_url' column to users table")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
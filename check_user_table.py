"""
Check User table structure in Neon database
"""
from app import app, db, User
from sqlalchemy import inspect

with app.app_context():
    print("=" * 60)
    print("USER TABLE STRUCTURE CHECK")
    print("=" * 60)
    print()
    
    # Get table inspector
    inspector = inspect(db.engine)
    
    # Check if users table exists
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")
    print()
    
    if 'users' in tables:
        print("✅ Users table exists")
        print()
        
        # Get columns
        columns = inspector.get_columns('users')
        print(f"Columns in users table ({len(columns)} total):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default}")
        print()
        
        # Check if password_hash column exists
        column_names = [col['name'] for col in columns]
        if 'password_hash' in column_names:
            print("✅ password_hash column exists")
        else:
            print("❌ password_hash column MISSING!")
            print("   This is the problem! The column needs to be added.")
        print()
        
        # Get indexes
        indexes = inspector.get_indexes('users')
        print(f"Indexes on users table ({len(indexes)} total):")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['column_names']}")
        print()
        
        # Try to query users
        try:
            user_count = User.query.count()
            print(f"✅ Can query users table: {user_count} users found")
        except Exception as e:
            print(f"❌ Error querying users table: {e}")
        print()
        
    else:
        print("❌ Users table does NOT exist!")
        print("   Run init_db.py to create it.")
        print()
    
    print("=" * 60)

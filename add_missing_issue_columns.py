"""
Add missing AI verification columns to issues table
"""
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    print("=" * 60)
    print("ADDING MISSING COLUMNS TO ISSUES TABLE")
    print("=" * 60)
    print()
    
    # Get current columns
    inspector = inspect(db.engine)
    existing_columns = [col['name'] for col in inspector.get_columns('issues')]
    
    print(f"Current columns ({len(existing_columns)}): {', '.join(existing_columns)}")
    print()
    
    # Define all AI verification columns that should exist
    required_columns = {
        'ai_verification_status': "VARCHAR(20) DEFAULT 'PENDING'",
        'ai_confidence_score': "FLOAT DEFAULT 0.0",
        'government_images': "TEXT",
        'government_notes': "TEXT",
        'citizen_verification_status': "VARCHAR(20)",
        'escalation_status': "VARCHAR(20) DEFAULT 'NONE'",
        'escalation_date': "TIMESTAMP",
        'resolution_date': "TIMESTAMP",
    }
    
    # Find missing columns
    missing_columns = {col: definition for col, definition in required_columns.items() 
                      if col not in existing_columns}
    
    if not missing_columns:
        print("✅ All AI verification columns exist! No migration needed.")
        print()
    else:
        print(f"Found {len(missing_columns)} missing columns:")
        for col in missing_columns:
            print(f"  - {col}")
        print()
        
        print("Adding missing columns...")
        print()
        
        # Add each missing column
        for col_name, col_definition in missing_columns.items():
            try:
                sql = f"ALTER TABLE issues ADD COLUMN IF NOT EXISTS {col_name} {col_definition}"
                print(f"  Executing: {sql}")
                db.session.execute(text(sql))
                db.session.commit()
                print(f"  ✅ Added: {col_name}")
            except Exception as e:
                print(f"  ❌ Failed to add {col_name}: {e}")
                db.session.rollback()
        
        print()
        print("=" * 60)
        print("MIGRATION COMPLETED")
        print("=" * 60)
        print()
        
        # Verify
        inspector = inspect(db.engine)
        final_columns = [col['name'] for col in inspector.get_columns('issues')]
        print(f"Final column count: {len(final_columns)}")
        print()
        
        # Test query
        try:
            from app import Issue
            issue_count = Issue.query.count()
            print(f"✅ Can now query issues table: {issue_count} issues found")
        except Exception as e:
            print(f"❌ Still error querying issues table: {e}")
    
    print()
    print("=" * 60)

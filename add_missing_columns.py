"""
Add missing columns to users table
"""
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    print("=" * 60)
    print("ADDING MISSING COLUMNS TO USERS TABLE")
    print("=" * 60)
    print()
    
    # Get current columns
    inspector = inspect(db.engine)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    print(f"Current columns ({len(existing_columns)}): {', '.join(existing_columns)}")
    print()
    
    # Define all columns that should exist
    required_columns = {
        'theme_color': "VARCHAR(20) DEFAULT 'blue'",
        'font_size': "VARCHAR(20) DEFAULT 'medium'",
        'issue_updates_notifications': "BOOLEAN DEFAULT TRUE",
        'community_activity_notifications': "BOOLEAN DEFAULT TRUE",
        'system_alerts_notifications': "BOOLEAN DEFAULT TRUE",
        'photo_quality': "VARCHAR(20) DEFAULT 'high'",
        'video_quality': "VARCHAR(20) DEFAULT 'high'",
        'auto_upload': "BOOLEAN DEFAULT FALSE",
        'cache_auto_clear': "BOOLEAN DEFAULT TRUE",
        'backup_sync': "BOOLEAN DEFAULT FALSE",
        'location_services': "BOOLEAN DEFAULT TRUE",
        'data_collection': "BOOLEAN DEFAULT TRUE",
        'high_contrast': "BOOLEAN DEFAULT FALSE",
        'large_text': "BOOLEAN DEFAULT FALSE",
        'voice_over': "BOOLEAN DEFAULT FALSE",
    }
    
    # Find missing columns
    missing_columns = {col: definition for col, definition in required_columns.items() 
                      if col not in existing_columns}
    
    if not missing_columns:
        print("✅ All columns exist! No migration needed.")
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
                sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_definition}"
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
        final_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Final column count: {len(final_columns)}")
        print()
        
        # Test query
        try:
            from app import User
            user_count = User.query.count()
            print(f"✅ Can now query users table: {user_count} users found")
        except Exception as e:
            print(f"❌ Still error querying users table: {e}")
    
    print()
    print("=" * 60)

#!/usr/bin/env python3
"""
Database Initialization Script for CivicFix
Initializes database tables and seeds initial data
"""

import os
import sys
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade

def init_database():
    """Initialize database with migrations"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from app import create_app
        from app.config import config
        from app.extensions import db
        
        # Get environment
        env = os.environ.get('FLASK_ENV', 'development')
        app, socketio = create_app(config.get(env, config['default']))
        
        with app.app_context():
            print("🔄 Initializing database...")
            
            # Check if migrations directory exists
            migrations_dir = Path('migrations')
            if not migrations_dir.exists():
                print("📁 Creating migrations directory...")
                from flask_migrate import init
                init()
                print("✅ Migrations directory created")
            
            # Create migration
            print("🔄 Creating database migration...")
            try:
                from flask_migrate import migrate
                migrate(message='Initial migration')
                print("✅ Migration created")
            except Exception as e:
                print(f"⚠️  Migration creation: {e}")
            
            # Apply migrations
            print("🔄 Applying database migrations...")
            from flask_migrate import upgrade
            upgrade()
            print("✅ Database migrations applied")
            
            # Seed initial data
            print("🔄 Seeding initial data...")
            from app.seed import seed_initial_data
            seed_initial_data()
            print("✅ Initial data seeded")
            
            print("\n🎉 Database initialization completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from app import create_app
        from app.config import config
        from app.extensions import db
        
        env = os.environ.get('FLASK_ENV', 'development')
        app, socketio = create_app(config.get(env, config['default']))
        
        with app.app_context():
            # Test connection
            result = db.engine.execute(db.text('SELECT 1')).scalar()
            print("✅ Database connection successful")
            
            # Check tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📊 Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_admin_user():
    """Create an admin user"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from app import create_app
        from app.config import config
        from app.extensions import db
        
        env = os.environ.get('FLASK_ENV', 'development')
        app, socketio = create_app(config.get(env, config['default']))
        
        with app.app_context():
            from app.models.user import User, UserRole
            
            # Check if admin exists
            admin = User.query.filter_by(role=UserRole.ADMIN).first()
            if admin:
                print("⚠️  Admin user already exists")
                return True
            
            # Create admin user
            admin_email = input("Enter admin email: ")
            admin_name = input("Enter admin name: ")
            firebase_uid = input("Enter Firebase UID (or 'temp' for temporary): ")
            
            if firebase_uid == 'temp':
                firebase_uid = f"temp-admin-{admin_email.replace('@', '-').replace('.', '-')}"
            
            admin_user = User.create_user(
                firebase_uid=firebase_uid,
                name=admin_name,
                email=admin_email,
                role=UserRole.ADMIN
            )
            
            print(f"✅ Admin user created: {admin_email}")
            print(f"   Firebase UID: {firebase_uid}")
            print("   Note: Update Firebase UID when user first logs in")
            
            return True
            
    except Exception as e:
        print(f"❌ Admin user creation failed: {e}")
        return False

def main():
    """Main function"""
    print("🗄️  CivicFix Database Initialization")
    print("=" * 40)
    
    # Check environment
    env = os.environ.get('FLASK_ENV', 'development')
    print(f"Environment: {env}")
    
    # Test database connection first
    print("\n🔍 Testing database connection...")
    if not test_database_connection():
        print("\n❌ Cannot connect to database. Please check your configuration.")
        print("Make sure your .env file has correct database settings.")
        return False
    
    # Initialize database
    if not init_database():
        return False
    
    # Ask if user wants to create admin
    try:
        create_admin = input("\nDo you want to create an admin user? (y/n): ").lower().strip()
        if create_admin == 'y':
            create_admin_user()
    except KeyboardInterrupt:
        print("\nSkipping admin user creation...")
    
    print("\n🎉 Database setup completed!")
    print("\n📋 Next steps:")
    print("1. Start the backend: python run.py")
    print("2. Test the API: curl http://localhost:5000/health")
    print("3. Connect your React Native app")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
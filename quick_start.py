#!/usr/bin/env python3
"""
Quick Start Script for CivicFix Backend
Bypasses slow AWS/Firebase initialization for faster development
"""

import os
import sys
from pathlib import Path

def main():
    """Quick start with minimal services"""
    
    # Set environment for quick start
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DATABASE_URL'] = 'sqlite:///civicfix.db'
    
    # Disable slow services for quick start
    os.environ['AWS_ACCESS_KEY_ID'] = ''
    os.environ['AWS_SECRET_ACCESS_KEY'] = ''
    os.environ['FIREBASE_SERVICE_ACCOUNT_PATH'] = ''
    
    print("Starting CivicFix backend in quick mode...")
    print("- Using SQLite database")
    print("- Skipping AWS S3 initialization")
    print("- Skipping Firebase initialization")
    print("")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from app import create_app
        from app.config import DevelopmentConfig
        
        # Create app with minimal config
        app, socketio = create_app(DevelopmentConfig)
        
        print("Backend started successfully!")
        print("Server running at: http://localhost:5000")
        print("Health check: http://localhost:5000/health")
        print("Press Ctrl+C to stop")
        print("")
        
        # Run the server
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"Failed to start backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
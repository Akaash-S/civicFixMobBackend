#!/usr/bin/env python3
"""
Quick Start Script for CivicFix Backend
Optimized for fast startup with minimal initialization
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_minimal_logging():
    """Setup minimal logging for faster startup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_environment():
    """Quick environment check"""
    print("Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        return False
    
    # Check virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: Not running in virtual environment")
    
    # Check database URL
    db_url = os.getenv('DATABASE_URL', '')
    if 'sqlite' in db_url:
        print("Using SQLite database (development mode)")
    elif 'postgresql' in db_url:
        print("Using PostgreSQL database")
    else:
        print("WARNING: No database configured")
    
    return True

def main():
    """Main startup function"""
    print("=" * 50)
    print("CivicFix Backend - Quick Start")
    print("=" * 50)
    
    # Setup logging
    setup_minimal_logging()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    try:
        # Import and create app
        print("Initializing Flask application...")
        from app import create_app
        from app.config import config
        
        # Get environment
        env = os.environ.get('FLASK_ENV', 'development')
        
        # Create app with minimal initialization
        app, socketio = create_app(config.get(env, config['default']))
        
        # Get server settings
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"Starting server on {host}:{port}")
        print(f"Environment: {env}")
        print(f"Debug mode: {app.config.get('DEBUG', False)}")
        print("=" * 50)
        print("Backend is ready!")
        print(f"API available at: http://localhost:{port}")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=app.config.get('DEBUG', False),
            use_reloader=False,  # Disable reloader for faster startup
            log_output=True,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"ERROR: Failed to start backend: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
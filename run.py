#!/usr/bin/env python3
"""
CivicFix Backend Server
Production-ready Flask application for civic issue reporting
"""

import os
import sys
from app import create_app
from app.config import config

def main():
    """Main application entry point"""
    
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    
    try:
        # Create application
        app, socketio = create_app(config.get(env, config['default']))
        
        # Get port from environment
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        # Log startup information
        app.logger.info(f"🚀 Starting CivicFix backend server")
        app.logger.info(f"Environment: {env}")
        app.logger.info(f"Host: {host}:{port}")
        app.logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
        
        # Run the application
        if env == 'development':
            # Development server with auto-reload
            socketio.run(
                app,
                host=host,
                port=port,
                debug=True,
                use_reloader=True,
                log_output=True,
                allow_unsafe_werkzeug=True
            )
        else:
            # Production server
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,
                use_reloader=False
            )
            
    except Exception as e:
        print(f"❌ Failed to start CivicFix backend: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
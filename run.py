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
        app.logger.info("Starting CivicFix backend server")
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
            # Production: This should not be called directly in production
            # Use Gunicorn instead: gunicorn --config gunicorn.conf.py run:socketio
            app.logger.warning("Production mode detected. Use Gunicorn for production deployment.")
            app.logger.info("Command: gunicorn --config gunicorn.conf.py run:socketio")
            
            # Fallback for testing
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,
                use_reloader=False
            )
            
    except Exception as e:
        print(f"Failed to start CivicFix backend: {str(e)}")
        sys.exit(1)

# WSGI application callable for Gunicorn
class WSGIApplication:
    """WSGI application wrapper for lazy initialization"""
    
    def __init__(self):
        self._app = None
    
    def __call__(self, environ, start_response):
        if self._app is None:
            env = os.environ.get('FLASK_ENV', 'development')
            app, socketio = create_app(config.get(env, config['default']))
            # For Gunicorn with SocketIO, use the Flask app directly
            # SocketIO middleware is automatically attached
            self._app = app
        return self._app(environ, start_response)

# For Gunicorn: gunicorn run:application
application = WSGIApplication()

# For direct execution
if __name__ == '__main__':
    main()
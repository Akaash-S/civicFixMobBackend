from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os

from app.config import Config
from app.extensions import db, migrate, ma
from app.services.aws_service import AWSService
from app.services.firebase_service import FirebaseService
from app.utils.logger import setup_logging

def get_aws_service(app):
    """Lazy initialization of AWS service"""
    if not hasattr(app, '_aws_service_initialized'):
        try:
            aws_service = AWSService()
            aws_initialized = aws_service.initialize()
            
            if aws_initialized:
                app.aws_service = aws_service
                app.logger.info("AWS services initialized on demand")
            else:
                app.aws_service = None
                app.logger.warning("AWS services not available - file uploads will be disabled")
                
        except Exception as e:
            app.logger.warning(f"AWS services not available: {str(e)}")
            app.aws_service = None
        app._aws_service_initialized = True
    return app.aws_service

def get_firebase_service(app):
    """Lazy initialization of Firebase service"""
    if not hasattr(app, '_firebase_service_initialized'):
        try:
            firebase_service = FirebaseService()
            firebase_service.initialize()
            app.firebase_service = firebase_service
            app.logger.info("Firebase services initialized on demand")
        except Exception as e:
            app.logger.warning(f"Firebase services not available: {str(e)}")
            app.firebase_service = None
        app._firebase_service_initialized = True
    return app.firebase_service

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    
    # Initialize rate limiter - use Redis in production, memory in development
    storage_uri = app.config.get('REDIS_URL', 'memory://') if not app.config.get('DEBUG') else 'memory://'
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["1000 per day", "100 per hour"] if not app.config.get('DEBUG') else ["200 per day", "50 per hour"]
    )
    
    # Initialize Socket.IO with production settings
    socketio_config = {
        'cors_allowed_origins': app.config['CORS_ORIGINS'],
        'logger': app.config.get('DEBUG', False),
        'engineio_logger': False
    }
    
    # Use eventlet in production for better performance (if available)
    if not app.config.get('DEBUG'):
        try:
            import eventlet
            socketio_config['async_mode'] = 'eventlet'
        except ImportError:
            app.logger.warning("eventlet not available, using threading mode")
            socketio_config['async_mode'] = 'threading'
    else:
        socketio_config['async_mode'] = 'threading'
    
    socketio = SocketIO(app, **socketio_config)
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize services based on environment
    with app.app_context():
        try:
            # Initialize database first (required)
            try:
                # Test database connection
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                    conn.commit()
                
                # Create tables
                db.create_all()
                app.logger.info("Database connected and tables created")
                
                # Seed initial data (non-blocking)
                try:
                    from app.seed import seed_initial_data
                    seed_initial_data()
                except Exception as seed_error:
                    app.logger.warning(f"Seeding failed (non-critical): {str(seed_error)}")
                
            except Exception as db_error:
                app.logger.error(f"Database connection failed: {str(db_error)}")
                if not app.config.get('DEBUG'):
                    # In production, database failure is critical
                    raise db_error
                else:
                    app.logger.warning("Continuing in development mode without database")
            
            # Initialize services based on environment
            if not app.config.get('DEBUG'):
                # Production: Initialize services immediately
                try:
                    aws_service = AWSService()
                    aws_initialized = aws_service.initialize()
                    
                    if aws_initialized:
                        app.aws_service = aws_service
                        app.logger.info("AWS services initialized for production")
                    else:
                        app.aws_service = None
                        app.logger.warning("AWS services not available - file uploads will be disabled")
                        
                except Exception as e:
                    app.logger.warning(f"AWS initialization failed - file uploads will be disabled: {str(e)}")
                    app.aws_service = None
                
                try:
                    firebase_service = FirebaseService()
                    firebase_service.initialize()
                    app.firebase_service = firebase_service
                    app.logger.info("Firebase services initialized for production")
                except Exception as e:
                    app.logger.error(f"Firebase initialization failed in production: {str(e)}")
                    raise e
            else:
                # Development: Lazy loading
                app.aws_service = None
                app.firebase_service = None
                app.logger.info("Services will initialize on first use (development mode)")
            
            app.logger.info("CivicFix backend initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Critical initialization failure: {str(e)}")
            if not app.config.get('DEBUG'):
                raise e
            else:
                app.logger.warning("Continuing in development mode with limited functionality")
    
    # Register blueprints
    from app.routes import register_routes
    register_routes(app)
    
    # Register Socket.IO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)
    
    # Store socketio instance for use in other modules
    app.socketio = socketio
    
    return app, socketio
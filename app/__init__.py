from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os

from app.config import Config
from app.extensions import db, migrate, ma
from app.utils.logger import setup_logging

def create_app(config_class=Config):
    """Application factory pattern - recursion-free"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging first (no dependencies)
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    
    # Initialize rate limiter
    storage_uri = app.config.get('REDIS_URL', 'memory://') if not app.config.get('DEBUG') else 'memory://'
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["1000 per day", "100 per hour"] if not app.config.get('DEBUG') else ["200 per day", "50 per hour"]
    )
    
    # Initialize Socket.IO
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
    
    # Initialize services in app context (no recursion)
    with app.app_context():
        # Initialize database
        initialize_database(app)
        
        # Initialize services
        initialize_services(app)
    
    # Register blueprints
    from app.routes import register_routes
    register_routes(app)
    
    # Register Socket.IO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)
    
    # Store socketio instance
    app.socketio = socketio
    
    app.logger.info("CivicFix backend initialized successfully")
    return app, socketio

def initialize_database(app):
    """Initialize database - separate function to avoid recursion"""
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
            raise db_error
        else:
            app.logger.warning("Continuing in development mode without database")

def initialize_services(app):
    """Initialize AWS and Firebase services - no recursion"""
    
    # Initialize AWS Service
    try:
        from app.services.aws_service import AWSService, AWSServiceError
        
        aws_service = AWSService()
        aws_config = {
            'S3_BUCKET_NAME': app.config.get('S3_BUCKET_NAME'),
            'AWS_REGION': app.config.get('AWS_REGION'),
            'AWS_ACCESS_KEY_ID': app.config.get('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': app.config.get('AWS_SECRET_ACCESS_KEY')
        }
        
        aws_service.initialize(aws_config)
        app.aws_service = aws_service
        app.logger.info("AWS services initialized successfully")
        
    except Exception as e:
        app.logger.error(f"AWS initialization failed: {str(e)}")
        if not app.config.get('DEBUG'):
            raise e
        else:
            app.aws_service = None
            app.logger.warning("Continuing without AWS services (development mode)")
    
    # Initialize Firebase Service
    try:
        from app.services.firebase_service import FirebaseService
        
        firebase_service = FirebaseService()
        firebase_config = {
            'FIREBASE_SERVICE_ACCOUNT_PATH': app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH'),
            'FIREBASE_PROJECT_ID': app.config.get('FIREBASE_PROJECT_ID')
        }
        
        firebase_service.initialize(firebase_config)
        app.firebase_service = firebase_service
        app.logger.info("Firebase services initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Firebase initialization failed: {str(e)}")
        if not app.config.get('DEBUG'):
            raise e
        else:
            app.firebase_service = None
            app.logger.warning("Continuing without Firebase services (development mode)")

# Helper functions for accessing services (no recursion)
def get_aws_service(app):
    """Get AWS service instance - simple getter"""
    return getattr(app, 'aws_service', None)

def get_firebase_service(app):
    """Get Firebase service instance - simple getter"""
    return getattr(app, 'firebase_service', None)
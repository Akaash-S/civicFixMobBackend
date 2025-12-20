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
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config.get('REDIS_URL', 'memory://'),
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Initialize Socket.IO
    # Use threading mode for better Windows compatibility
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        async_mode='threading',
        logger=True,
        engineio_logger=False
    )
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize services
    with app.app_context():
        try:
            # Initialize AWS services (optional for development)
            try:
                aws_service = AWSService()
                aws_service.initialize()
                app.aws_service = aws_service
                app.logger.info("✅ AWS services initialized")
            except Exception as e:
                app.logger.warning(f"⚠️  AWS services not available: {str(e)}")
                app.aws_service = None
            
            # Initialize Firebase (optional for development)
            try:
                firebase_service = FirebaseService()
                firebase_service.initialize()
                app.firebase_service = firebase_service
                app.logger.info("✅ Firebase services initialized")
            except Exception as e:
                app.logger.warning(f"⚠️  Firebase services not available: {str(e)}")
                app.firebase_service = None
            
            # Create database tables
            db.create_all()
            app.logger.info("✅ Database tables created")
            
            # Seed initial data
            from app.seed import seed_initial_data
            seed_initial_data()
            
            app.logger.info("✅ CivicFix backend initialized successfully")
            
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize backend: {str(e)}")
            # Don't raise in development mode, allow partial initialization
            if not app.config.get('DEBUG'):
                raise e
    
    # Register blueprints
    from app.routes import register_routes
    register_routes(app)
    
    # Register Socket.IO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)
    
    # Store socketio instance for use in other modules
    app.socketio = socketio
    
    return app, socketio
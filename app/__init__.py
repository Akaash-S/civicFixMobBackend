from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
import os

from app.config import Config
from app.extensions import db, migrate, ma
from app.utils.logger import setup_logging

def create_app(config_class=Config):
    """Application factory pattern - never blocks on service initialization"""
    import time
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Track startup time
    app._start_time = time.time()
    
    # Setup logging first (no dependencies)
    setup_logging(app)
    
    app.logger.info("🚀 Starting CivicFix backend server...")
    app.logger.info(f"📊 Environment: {app.config.get('FLASK_ENV', 'unknown')}")
    app.logger.info(f"🐛 Debug mode: {app.config.get('DEBUG', False)}")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    
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
    
    # Initialize services in app context (with timeouts - never block)
    with app.app_context():
        # Initialize database (with timeout)
        initialize_database(app)
        
        # Initialize services (with timeouts)
        initialize_services(app)
    
    # Register blueprints
    from app.routes import register_routes
    register_routes(app)
    
    # Register Socket.IO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)
    
    # Store socketio instance
    app.socketio = socketio
    
    startup_time = time.time() - app._start_time
    app.logger.info(f"✅ CivicFix backend initialized successfully in {startup_time:.2f}s")
    app.logger.info("🌐 Server ready to accept connections")
    
    return app, socketio

def initialize_database(app):
    """Initialize database with timeout - never block server startup"""
    import time
    
    start_time = time.time()
    timeout = 30  # 30 second timeout for database
    
    try:
        app.logger.info(f"Starting database initialization (timeout: {timeout}s)...")
        
        # Test database connection with timeout
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
            conn.commit()
        
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            app.logger.warning(f"Database connection timeout ({timeout}s) - skipping table creation")
            return
        
        # Create tables
        db.create_all()
        elapsed = time.time() - start_time
        app.logger.info(f"✅ Database connected and tables created in {elapsed:.2f}s")
        
        # Seed initial data (non-blocking, with timeout check)
        if elapsed < timeout - 5:  # Leave 5 seconds buffer
            try:
                from app.seed import seed_initial_data
                seed_initial_data()
                app.logger.info("✅ Database seeding completed")
            except Exception as seed_error:
                app.logger.warning(f"⚠️ Database seeding failed (non-critical): {str(seed_error)}")
        else:
            app.logger.info("⚠️ Skipping database seeding due to time constraints")
        
    except Exception as db_error:
        elapsed = time.time() - start_time
        app.logger.error(f"❌ Database connection failed after {elapsed:.2f}s: {str(db_error)}")
        
        # In production, try to continue without database (graceful degradation)
        if not app.config.get('DEBUG'):
            app.logger.warning("🚀 Continuing server startup without database (degraded mode)")
        else:
            app.logger.warning("🚀 Continuing in development mode without database")

def initialize_services(app):
    """
    Initialize AWS and Firebase services with timeouts - never block server startup
    Server will start even if services fail to initialize
    """
    
    # Initialize AWS Service with timeout
    try:
        # Check if AWS dependencies are available
        try:
            import boto3
            import botocore
        except ImportError:
            app.logger.warning("⚠️ AWS dependencies not available - skipping AWS initialization")
            app.aws_service = None
        else:
            from app.services.aws_service import AWSService
            
            app.logger.info("Starting AWS service initialization...")
            aws_service = AWSService()
            aws_config = {
                'S3_BUCKET_NAME': app.config.get('S3_BUCKET_NAME'),
                'AWS_REGION': app.config.get('AWS_REGION'),
                'AWS_ACCESS_KEY_ID': app.config.get('AWS_ACCESS_KEY_ID'),
                'AWS_SECRET_ACCESS_KEY': app.config.get('AWS_SECRET_ACCESS_KEY')
            }
            
            # Try to initialize with 60 second timeout
            aws_success = aws_service.initialize(aws_config, timeout=60)
            
            if aws_success:
                app.aws_service = aws_service
                app.logger.info("✅ AWS services initialized successfully")
            else:
                app.aws_service = None
                app.logger.warning("⚠️ AWS services disabled - file uploads unavailable")
        
    except Exception as e:
        app.logger.error(f"❌ AWS initialization error: {str(e)}")
        app.aws_service = None
        app.logger.warning("⚠️ AWS services disabled due to error")
    
    # Initialize Firebase Service with timeout
    try:
        # Check if Firebase dependencies are available
        try:
            import firebase_admin
        except ImportError:
            app.logger.warning("⚠️ Firebase dependencies not available - skipping Firebase initialization")
            app.firebase_service = None
        else:
            from app.services.firebase_service import FirebaseService
            
            app.logger.info("Starting Firebase service initialization...")
            firebase_service = FirebaseService()
            firebase_config = {
                'FIREBASE_SERVICE_ACCOUNT_PATH': app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH'),
                'FIREBASE_SERVICE_ACCOUNT_JSON': app.config.get('FIREBASE_SERVICE_ACCOUNT_JSON'),
                'FIREBASE_PROJECT_ID': app.config.get('FIREBASE_PROJECT_ID')
            }
            
            # Try to initialize with 30 second timeout
            firebase_success = firebase_service.initialize(firebase_config, timeout=30)
            
            if firebase_success:
                app.firebase_service = firebase_service
                app.logger.info("✅ Firebase services initialized successfully")
            else:
                app.firebase_service = None
                app.logger.warning("⚠️ Firebase services disabled - authentication may be limited")
        
    except Exception as e:
        app.logger.error(f"❌ Firebase initialization error: {str(e)}")
        app.firebase_service = None
        app.logger.warning("⚠️ Firebase services disabled due to error")
    
    # Log final service status
    aws_status = "✅ Available" if getattr(app, 'aws_service', None) and app.aws_service.is_available() else "❌ Disabled"
    firebase_status = "✅ Available" if getattr(app, 'firebase_service', None) and app.firebase_service.is_available() else "❌ Disabled"
    
    app.logger.info("🔧 Service Status Summary:")
    app.logger.info(f"   AWS S3: {aws_status}")
    app.logger.info(f"   Firebase: {firebase_status}")
    app.logger.info("🚀 Server startup continuing regardless of service status...")

# Helper functions for accessing services (no recursion)
def get_aws_service(app):
    """Get AWS service instance - simple getter"""
    return getattr(app, 'aws_service', None)

def get_firebase_service(app):
    """Get Firebase service instance - simple getter"""
    return getattr(app, 'firebase_service', None)
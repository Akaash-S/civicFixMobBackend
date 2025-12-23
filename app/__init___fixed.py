"""
Production-safe Flask app initialization
- No circular imports
- Proper service initialization order
- Clean error handling
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO

# Import extensions (no circular dependencies)
from app.extensions import db, migrate, cors, limiter

# Import services using safe pattern
from app.services.aws_service_fixed import initialize_aws_service, AWSServiceError

def create_app(config_object=None):
    """
    Application factory pattern with safe service initialization
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        from app.config import config
        env = os.environ.get('FLASK_ENV', 'development')
        app.config.from_object(config.get(env, config['default']))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    limiter.init_app(app)
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'),
        async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'),
        logger=app.config.get('DEBUG', False),
        engineio_logger=app.config.get('DEBUG', False)
    )
    
    # Setup logging first (no circular dependencies)
    setup_logging(app)
    
    # Initialize database
    with app.app_context():
        try:
            # Test database connection
            db.engine.connect().close()
            app.logger.info("Database connection successful")
            
            # Create tables
            db.create_all()
            app.logger.info("Database tables created/verified")
            
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            if not app.config.get('DEBUG'):
                raise
    
    # Initialize AWS services (after app context is ready)
    initialize_aws_services(app)
    
    # Initialize Firebase services
    initialize_firebase_services(app)
    
    # Register blueprints (after all services are initialized)
    register_blueprints(app)
    
    # Register Socket.IO events
    register_socketio_events(socketio)
    
    app.logger.info("CivicFix backend initialized successfully")
    
    return app, socketio

def setup_logging(app):
    """Setup application logging (no circular imports)"""
    import sys
    from logging.handlers import RotatingFileHandler
    
    # Set log level
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # File handler (with error handling)
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs', mode=0o777)
        
        file_handler = RotatingFileHandler(
            'logs/civicfix.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        
        app.logger.info("File logging enabled")
        
    except (OSError, PermissionError) as e:
        app.logger.warning(f"File logging disabled: {e}")
    
    # Suppress noisy loggers in production
    if not app.config.get('DEBUG'):
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('boto3').setLevel(logging.WARNING)

def initialize_aws_services(app):
    """
    Initialize AWS services safely (no recursion)
    """
    try:
        # Prepare configuration dictionary (no circular imports)
        aws_config = {
            'S3_BUCKET_NAME': app.config.get('S3_BUCKET_NAME'),
            'AWS_REGION': app.config.get('AWS_REGION'),
            'AWS_ACCESS_KEY_ID': app.config.get('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': app.config.get('AWS_SECRET_ACCESS_KEY')
        }
        
        # Initialize AWS service
        aws_service = initialize_aws_service(aws_config)
        
        # Store in app context (not app.config to avoid circular references)
        app.aws_service = aws_service
        
        app.logger.info("AWS services initialized successfully")
        
    except AWSServiceError as e:
        app.logger.error(f"AWS service initialization failed: {str(e)}")
        
        # In production, AWS is required
        if not app.config.get('DEBUG'):
            raise
        else:
            app.logger.warning("Continuing without AWS services (development mode)")
            app.aws_service = None
    
    except Exception as e:
        app.logger.error(f"Unexpected error initializing AWS: {str(e)}")
        
        if not app.config.get('DEBUG'):
            raise
        else:
            app.aws_service = None

def initialize_firebase_services(app):
    """Initialize Firebase services safely"""
    try:
        from app.services.firebase_service import FirebaseService
        
        firebase_config = {
            'FIREBASE_SERVICE_ACCOUNT_PATH': app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH'),
            'FIREBASE_PROJECT_ID': app.config.get('FIREBASE_PROJECT_ID')
        }
        
        firebase_service = FirebaseService()
        firebase_service.initialize(firebase_config)
        
        app.firebase_service = firebase_service
        app.logger.info("Firebase services initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Firebase initialization failed: {str(e)}")
        
        if not app.config.get('DEBUG'):
            raise
        else:
            app.logger.warning("Continuing without Firebase services (development mode)")
            app.firebase_service = None

def register_blueprints(app):
    """Register all blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.issues import issues_bp
    from app.routes.media import media_bp
    from app.routes.health import health_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(issues_bp, url_prefix='/api/v1/issues')
    app.register_blueprint(media_bp, url_prefix='/api/v1/media')

def register_socketio_events(socketio):
    """Register Socket.IO events"""
    from app.sockets import register_socket_events
    register_socket_events(socketio)
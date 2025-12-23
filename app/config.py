import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration - AWS RDS PostgreSQL REQUIRED
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Validate that DATABASE_URL is provided
    if not DATABASE_URL:
        # Build from individual components if DATABASE_URL not provided
        db_host = os.environ.get('DB_HOST')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME')
        db_user = os.environ.get('DB_USER')
        db_password = os.environ.get('DB_PASSWORD')
        
        if all([db_host, db_name, db_user, db_password]):
            DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            raise ValueError(
                "Database configuration required! Please set DATABASE_URL or "
                "DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD environment variables."
            )
    
    # Handle different PostgreSQL URL formats
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Ensure we're using PostgreSQL
    if not DATABASE_URL.startswith('postgresql://'):
        raise ValueError(
            "Only PostgreSQL databases are supported. "
            "DATABASE_URL must start with 'postgresql://'"
        )
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enhanced database configuration for AWS RDS
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'pool_size': 10,
        'echo': False  # Set to True for SQL debugging
    }
    
    # AWS Configuration - S3 REQUIRED for file storage
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    
    # Validate AWS configuration
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        raise ValueError(
            "AWS configuration required! Please set AWS_ACCESS_KEY_ID, "
            "AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables."
        )
    
    # Firebase Configuration - supports multiple methods
    FIREBASE_SERVICE_ACCOUNT_B64 = os.environ.get('FIREBASE_SERVICE_ACCOUNT_B64')  # Recommended
    FIREBASE_SERVICE_ACCOUNT_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')  # Fallback
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')  # Legacy
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    

    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,mp4,mov').split(',')
    
    # API
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    # Socket.IO
    SOCKETIO_ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    # Faster timeouts for development
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': False,  # Disable SQL logging for faster startup
        'pool_timeout': 5,  # Faster timeout for development
        'connect_args': {
            'connect_timeout': 5,  # 5 second connection timeout
            'options': '-c statement_timeout=10000'  # 10 second query timeout
        } if 'postgresql' in (Config.DATABASE_URL or '') else {}
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production-optimized database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 3600,  # Recycle connections every hour
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 second query timeout
        }
    }
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production CORS settings (should be more restrictive)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # Production logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Health check settings
    HEALTH_CHECK_ENABLED = True
    
    # Performance settings
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Override validation for testing
    def __init__(self):
        # Skip AWS and DB validation for testing
        pass
    
    # Use in-memory PostgreSQL for testing (requires test database)
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/test_civicfix')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': False,
        'echo': False
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Setup application logging"""
    
    # Set log level based on environment
    if app.config.get('DEBUG'):
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(console_handler)
    
    # File handler with rotation (only if logs directory is writable)
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs', mode=0o777)
        
        # Test if we can write to logs directory
        test_file = 'logs/.write_test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # If we can write, add file handler
        file_handler = RotatingFileHandler(
            'logs/civicfix.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        
        # Configure root logger with file handler
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.addHandler(file_handler)
        
        app.logger.info("File logging enabled: logs/civicfix.log")
        
    except (OSError, PermissionError) as e:
        # If we can't write to logs, just use console logging
        app.logger.warning(f"File logging disabled due to permission error: {e}")
        app.logger.warning("Logging to console only")
        
        # Configure root logger with console only
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
    
    # Suppress some noisy loggers in production
    if not app.config.get('DEBUG'):
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('boto3').setLevel(logging.WARNING)
    
    app.logger.info("Logging configured successfully")
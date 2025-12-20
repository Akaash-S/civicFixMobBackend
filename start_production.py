#!/usr/bin/env python3
"""
Production Startup Script for CivicFix Backend
Handles production deployment with proper error handling and monitoring
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def setup_production_logging():
    """Setup production logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/production.log', mode='a')
        ]
    )

def check_production_requirements():
    """Check if all production requirements are met"""
    logger = logging.getLogger(__name__)
    
    # Check environment file
    env_file = Path('.env.production')
    if not env_file.exists():
        logger.error("Production environment file (.env.production) not found")
        return False
    
    # Load production environment
    load_dotenv('.env.production')
    
    # Check critical environment variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'S3_BUCKET_NAME',
        'FIREBASE_SERVICE_ACCOUNT_PATH',
        'REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Check service account file
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    if not Path(service_account_path).exists():
        logger.error(f"Firebase service account file not found: {service_account_path}")
        return False
    
    # Check if logs directory exists
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
        logger.info("Created logs directory")
    
    logger.info("All production requirements satisfied")
    return True

def run_database_migrations():
    """Run database migrations before starting server"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running database migrations...")
        
        # Initialize database if needed
        result = subprocess.run([
            sys.executable, '-c',
            'from app import create_app; from app.config import config; '
            'from app.extensions import db; '
            'app, _ = create_app(config["production"]); '
            'with app.app_context(): db.create_all()'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"Database migration failed: {result.stderr}")
            return False
        
        logger.info("Database migrations completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Database migration timed out")
        return False
    except Exception as e:
        logger.error(f"Database migration error: {str(e)}")
        return False

def start_gunicorn_server():
    """Start the Gunicorn server"""
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration from environment
        workers = os.getenv('GUNICORN_WORKERS', '4')
        port = os.getenv('PORT', '5000')
        
        logger.info(f"Starting Gunicorn server with {workers} workers on port {port}")
        
        # Gunicorn command
        cmd = [
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            '--workers', workers,
            '--bind', f'0.0.0.0:{port}',
            'run:app'
        ]
        
        # Start server
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Gunicorn server failed to start: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        return True
    except Exception as e:
        logger.error(f"Unexpected error starting server: {str(e)}")
        return False

def main():
    """Main production startup function"""
    print("=" * 60)
    print("CivicFix Backend - Production Deployment")
    print("=" * 60)
    
    # Setup logging
    setup_production_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Check production requirements
        if not check_production_requirements():
            logger.error("Production requirements check failed")
            sys.exit(1)
        
        # Run database migrations
        if not run_database_migrations():
            logger.error("Database migration failed")
            sys.exit(1)
        
        # Start server
        logger.info("Starting production server...")
        start_gunicorn_server()
        
    except KeyboardInterrupt:
        logger.info("Production server shutdown completed")
    except Exception as e:
        logger.error(f"Production startup failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
CivicFix Backend Startup Script
Handles environment loading and initialization before starting the app
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        logger.warning("⚠️  .env file not found, using system environment variables")
        return False
    
    logger.info("📄 Loading environment variables from .env file...")
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable
                    os.environ[key] = value
        
        logger.info("✅ Environment variables loaded from .env")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load .env file: {e}")
        return False

def check_required_vars():
    """Check if required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'SUPABASE_JWT_SECRET',
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    missing_vars = []
    
    logger.info("🔍 Checking required environment variables...")
    
    for var in required_vars:
        if var in os.environ and os.environ[var]:
            logger.info(f"   ✅ {var} is set")
        else:
            missing_vars.append(var)
            logger.error(f"   ❌ {var} is missing")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        
        if os.environ.get('SKIP_VALIDATION') != 'true':
            logger.error("Set SKIP_VALIDATION=true to continue anyway (not recommended)")
            return False
        else:
            logger.warning("⚠️  Continuing despite missing variables (SKIP_VALIDATION=true)")
    
    return True

def run_initialization():
    """Run database and storage initialization"""
    if os.environ.get('SKIP_INIT') == 'true':
        logger.info("⚠️  Skipping initialization (SKIP_INIT=true)")
        return True
    
    logger.info("🔧 Running initialization...")
    
    try:
        # Import and run init_db
        import init_db
        
        db_success = init_db.init_database()
        storage_success = init_db.check_supabase_storage()
        
        if db_success and storage_success:
            logger.info("✅ Initialization completed successfully")
            return True
        else:
            logger.warning("⚠️  Initialization had some issues")
            return True  # Continue anyway
            
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        
        if os.environ.get('SKIP_VALIDATION') == 'true':
            logger.warning("⚠️  Continuing despite initialization failure (SKIP_VALIDATION=true)")
            return True
        
        return False

def start_app():
    """Start the Flask application"""
    logger.info("🎯 Starting CivicFix Backend...")
    logger.info(f"   Port: {os.environ.get('PORT', '5000')}")
    logger.info(f"   Environment: {os.environ.get('FLASK_ENV', 'production')}")
    logger.info(f"   Database: Neon PostgreSQL")
    logger.info(f"   Storage: Supabase Storage")
    logger.info("")
    
    # Import and run the app
    try:
        import app as app_module
        logger.info("   Using: app.py (Neon + Supabase)")
        
        app = app_module.app
        port = int(os.environ.get('PORT', 5000))
        
        if os.environ.get('FLASK_ENV') == 'development':
            logger.info("   Mode: Development (Flask dev server)")
            app.run(host='0.0.0.0', port=port, debug=True)
        else:
            logger.info("   Mode: Production (Gunicorn)")
            # Use gunicorn
            import subprocess
            
            # Determine which module to use
            module_name = 'app_new:app' if 'app_new' in sys.modules else 'app:app'
            
            subprocess.run([
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '4',
                '--timeout', '120',
                '--access-logfile', '-',
                '--error-logfile', '-',
                module_name
            ])
            
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main startup sequence"""
    logger.info("")
    logger.info("🚀 CivicFix Backend - Production Startup")
    logger.info("=" * 60)
    logger.info("")
    
    # Step 1: Load environment variables
    load_env_file()
    logger.info("")
    
    # Step 2: Check required variables
    if not check_required_vars():
        logger.error("❌ Startup aborted due to missing environment variables")
        sys.exit(1)
    logger.info("")
    
    # Step 3: Run initialization
    if not run_initialization():
        logger.error("❌ Startup aborted due to initialization failure")
        sys.exit(1)
    logger.info("")
    
    # Step 4: Start the application
    start_app()

if __name__ == '__main__':
    main()

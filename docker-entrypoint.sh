#!/bin/bash
# ================================
# CivicFix Backend - Docker Entrypoint
# ================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to wait for database
wait_for_database() {
    if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
        log_step "Waiting for PostgreSQL database..."
        
        # Extract database connection details
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
            # Wait for database with timeout
            timeout=60
            counter=0
            
            while ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
                counter=$((counter + 1))
                if [ $counter -gt $timeout ]; then
                    log_warn "Database connection timeout after ${timeout}s - continuing anyway"
                    break
                fi
                log_info "Waiting for database... ($counter/${timeout}s)"
                sleep 1
            done
            
            if [ $counter -le $timeout ]; then
                log_info "Database is ready!"
            fi
        else
            log_warn "Could not parse database connection details"
        fi
    else
        log_info "Using SQLite or no database configured"
    fi
}

# Function to validate environment
validate_environment() {
    log_step "Validating environment configuration..."
    
    # Check required environment variables
    required_vars=("FLASK_APP" "SECRET_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_error "Please check your .env.production file"
        exit 1
    fi
    
    # Validate SECRET_KEY
    if [ ${#SECRET_KEY} -lt 32 ]; then
        log_warn "SECRET_KEY is shorter than recommended (32+ characters)"
    fi
    
    # Check AWS configuration
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$S3_BUCKET_NAME" ]; then
        log_info "AWS S3 configuration detected"
    else
        log_warn "AWS S3 configuration incomplete - file uploads may not work"
    fi
    
    # Check Firebase configuration
    if [ -n "$FIREBASE_SERVICE_ACCOUNT_JSON" ] || [ -n "$FIREBASE_SERVICE_ACCOUNT_PATH" ]; then
        if [ -n "$FIREBASE_PROJECT_ID" ]; then
            log_info "Firebase configuration detected"
        else
            log_warn "Firebase project ID missing"
        fi
    else
        log_warn "Firebase configuration missing - authentication may not work"
    fi
    
    log_info "Environment validation completed"
}

# Function to initialize application
initialize_application() {
    log_step "Initializing CivicFix application..."
    
    # Set proper permissions
    chmod -R 777 logs temp uploads 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs temp uploads 2>/dev/null || true
    
    # Initialize Flask application (this will run our timeout-based initialization)
    log_info "Running application initialization check..."
    python3 -c "
import sys
sys.path.append('.')
try:
    from app import create_app
    app, socketio = create_app()
    print('✓ Application initialization successful')
except Exception as e:
    print(f'✗ Application initialization failed: {e}')
    # Don't exit - let the application start anyway
" || log_warn "Application pre-check failed - continuing with startup"
    
    log_info "Application initialization completed"
}

# Function to setup logging
setup_logging() {
    log_step "Setting up logging..."
    
    # Ensure log directory exists
    mkdir -p logs
    
    # Set log file permissions
    touch logs/civicfix.log logs/error.log logs/access.log 2>/dev/null || true
    chmod 666 logs/*.log 2>/dev/null || true
    
    log_info "Logging setup completed"
}

# Main initialization function
main() {
    log_info "🚀 Starting CivicFix Backend Container"
    log_info "======================================"
    
    # Run initialization steps
    setup_logging
    validate_environment
    wait_for_database
    initialize_application
    
    log_info "🎉 Container initialization completed successfully!"
    log_info "Starting application server..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
trap 'log_info "Received shutdown signal, stopping gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
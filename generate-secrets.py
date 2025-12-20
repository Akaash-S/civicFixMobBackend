#!/usr/bin/env python3
"""
CivicFix Backend - Secret Key Generator
Generates secure random keys for production use
"""

import secrets
import string
import os

def generate_secret_key(length=64):
    """Generate a secure random secret key"""
    return secrets.token_hex(length // 2)

def generate_password(length=32):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🔐 CivicFix Backend - Secret Generator")
    print("=" * 50)
    
    # Generate Flask secret key
    flask_secret = generate_secret_key(64)
    print(f"Flask SECRET_KEY:")
    print(f"SECRET_KEY={flask_secret}")
    print()
    
    # Generate database password
    db_password = generate_password(32)
    print(f"Database Password:")
    print(f"DB_PASSWORD={db_password}")
    print()
    
    # Generate Grafana admin password
    grafana_password = generate_password(16)
    print(f"Grafana Admin Password:")
    print(f"GF_SECURITY_ADMIN_PASSWORD={grafana_password}")
    print()
    
    # Generate Redis password (optional)
    redis_password = generate_password(24)
    print(f"Redis Password (optional):")
    print(f"REDIS_PASSWORD={redis_password}")
    print()
    
    print("⚠️  SECURITY REMINDERS:")
    print("- Store these secrets securely")
    print("- Never commit them to version control")
    print("- Use different secrets for different environments")
    print("- Rotate secrets regularly")
    print("- Use environment variables or secret management services")
    
    # Offer to create .env.production template
    create_env = input("\n📝 Create .env.production template with these secrets? (y/N): ")
    if create_env.lower() == 'y':
        create_env_file(flask_secret, db_password, grafana_password, redis_password)

def create_env_file(flask_secret, db_password, grafana_password, redis_password):
    """Create .env.production file with generated secrets"""
    
    if os.path.exists('.env.production'):
        overwrite = input("⚠️  .env.production already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("❌ Cancelled. Secrets not saved to file.")
            return
    
    env_content = f"""# CivicFix Backend Production Environment
# Generated on {os.popen('date').read().strip()}
# IMPORTANT: Never commit this file to version control!

# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY={flask_secret}

# Database Configuration (AWS RDS PostgreSQL)
DATABASE_URL=postgresql://username:{db_password}@your-rds-endpoint:5432/database-name
DB_HOST=your-rds-endpoint
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD={db_password}

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket-name

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Redis Configuration
REDIS_URL=redis://:{redis_password}@your-redis-endpoint:6379/0
REDIS_PASSWORD={redis_password}

# Security Settings
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# File Upload Settings
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov

# API Settings
API_VERSION=v1

# Socket.IO Configuration
SOCKETIO_ASYNC_MODE=eventlet

# Production Settings
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30

# Monitoring (Grafana)
GF_SECURITY_ADMIN_PASSWORD={grafana_password}
"""
    
    try:
        with open('.env.production', 'w') as f:
            f.write(env_content)
        
        # Set secure permissions
        os.chmod('.env.production', 0o600)
        
        print("✅ .env.production created successfully!")
        print("📝 Please edit the file and replace placeholder values:")
        print("   - your-rds-endpoint")
        print("   - your-database-name")
        print("   - your-database-user")
        print("   - your-aws-access-key-id")
        print("   - your-aws-secret-access-key")
        print("   - your-aws-region")
        print("   - your-s3-bucket-name")
        print("   - your-firebase-project-id")
        print("   - your-redis-endpoint")
        print("   - yourdomain.com")
        
    except Exception as e:
        print(f"❌ Error creating .env.production: {e}")

if __name__ == '__main__':
    main()
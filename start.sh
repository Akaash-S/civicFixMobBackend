#!/usr/bin/env bash
# CivicFix Backend - Render Start Script

set -o errexit  # Exit on error

echo "🚀 Starting CivicFix Backend Server"
echo "==================================="

# Run database migrations (if needed)
echo "🗄️ Running database migrations..."
python -c "
try:
    from flask_migrate import upgrade
    from app import create_app
    app, _ = create_app()
    with app.app_context():
        upgrade()
    print('✅ Database migrations completed')
except Exception as e:
    print(f'⚠️ Migration skipped: {e}')
"

# Start the application with Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn --config gunicorn.conf.py run:application
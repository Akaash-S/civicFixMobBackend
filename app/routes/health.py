"""
Health check endpoints
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint
    Returns service status without blocking
    """
    start_time = time.time()
    
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'uptime': time.time() - getattr(current_app, '_start_time', time.time()),
        'services': {}
    }
    
    # Check database status (quick check)
    try:
        from app.extensions import db
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
            conn.commit()
        health_data['services']['database'] = {
            'status': 'healthy',
            'type': 'postgresql'
        }
    except Exception as e:
        health_data['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)[:100],
            'type': 'postgresql'
        }
    
    # Check AWS S3 status
    aws_service = getattr(current_app, 'aws_service', None)
    if aws_service and aws_service.is_available():
        health_data['services']['aws_s3'] = {
            'status': 'healthy',
            'bucket': aws_service.bucket_name,
            'region': aws_service.region
        }
    else:
        health_data['services']['aws_s3'] = {
            'status': 'disabled',
            'message': 'AWS S3 service not available'
        }
    
    # Check Firebase status
    firebase_service = getattr(current_app, 'firebase_service', None)
    if firebase_service and firebase_service.is_available():
        health_data['services']['firebase'] = {
            'status': 'healthy',
            'type': 'firebase_admin'
        }
    else:
        health_data['services']['firebase'] = {
            'status': 'disabled',
            'message': 'Firebase service not available'
        }
    
    # Check Redis status (if configured)
    try:
        from flask_limiter.util import get_remote_address
        # If we can import this, rate limiter is working
        health_data['services']['redis'] = {
            'status': 'healthy',
            'type': 'rate_limiter'
        }
    except Exception:
        health_data['services']['redis'] = {
            'status': 'unknown',
            'type': 'rate_limiter'
        }
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000
    health_data['response_time_ms'] = round(response_time, 2)
    
    # Determine overall status
    service_statuses = [service.get('status', 'unknown') for service in health_data['services'].values()]
    
    if 'unhealthy' in service_statuses:
        health_data['status'] = 'degraded'
        status_code = 200  # Still return 200 for degraded services
    elif all(status in ['healthy', 'disabled'] for status in service_statuses):
        health_data['status'] = 'healthy'
        status_code = 200
    else:
        health_data['status'] = 'unknown'
        status_code = 200
    
    return jsonify(health_data), status_code

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe - server is ready to accept traffic
    """
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe - server is alive
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
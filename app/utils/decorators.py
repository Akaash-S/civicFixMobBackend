from functools import wraps
from flask import request, jsonify, current_app
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

def firebase_required(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header is required'}), 401
        
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Check if Firebase service is available
        firebase_service = getattr(current_app, 'firebase_service', None)
        if not firebase_service:
            # For development without Firebase, create a mock user
            if current_app.config.get('DEBUG'):
                logger.warning("Firebase service not available, using mock authentication")
                mock_user = {
                    'uid': 'dev-user-uid',
                    'email': 'dev@civicfix.com',
                    'name': 'Development User',
                    'email_verified': True
                }
                return f(mock_user, *args, **kwargs)
            else:
                return jsonify({'error': 'Authentication service unavailable'}), 503
        
        # Verify token with Firebase
        user_info = firebase_service.verify_token(token)
        
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Pass user info to the route function
        return f(user_info, *args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin role (use after firebase_required)"""
    @wraps(f)
    def decorated_function(current_user_firebase, *args, **kwargs):
        # Get user from database
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(current_user_firebase, *args, **kwargs)
    
    return decorated_function

def rate_limit_exempt(f):
    """Decorator to exempt a route from rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    # Mark function as rate limit exempt
    decorated_function._rate_limit_exempt = True
    return decorated_function
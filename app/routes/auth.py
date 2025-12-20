from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models.user import User, UserRole
from app.extensions import db
from app.utils.decorators import firebase_required
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/sync-user', methods=['POST'])
@firebase_required
def sync_user(current_user_firebase):
    """Sync user data from Firebase to local database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        firebase_uid = current_user_firebase['uid']
        name = data.get('name') or current_user_firebase.get('name', '')
        email = current_user_firebase.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if user already exists
        user = User.find_by_firebase_uid(firebase_uid)
        
        if user:
            # Update existing user
            user.name = name
            user.email = email
            db.session.commit()
            logger.info(f"Updated existing user: {email}")
        else:
            # Create new user
            role = UserRole.ADMIN if data.get('role') == 'ADMIN' else UserRole.CITIZEN
            user = User.create_user(
                firebase_uid=firebase_uid,
                name=name,
                email=email,
                role=role
            )
            logger.info(f"Created new user: {email}")
        
        return jsonify({
            'message': 'User synced successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error syncing user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@firebase_required
def get_profile(current_user_firebase):
    """Get current user profile"""
    try:
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@firebase_required
def update_profile(current_user_firebase):
    """Update user profile"""
    try:
        data = request.get_json()
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
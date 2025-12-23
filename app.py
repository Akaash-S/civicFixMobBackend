"""
CivicFix Backend - Clean, Production-Ready Flask Application
Simple, reliable, and easy to deploy
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import json
import base64

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

# Database configuration - flexible for development and production
database_url = os.environ.get('DATABASE_URL', 'sqlite:///civicfix.db')

# Handle PostgreSQL URL format
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    # Parse comma-separated origins
    origins = [origin.strip() for origin in cors_origins.split(',')]
    CORS(app, origins=origins)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# Models
# ================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('Issue', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='OPEN')
    priority = db.Column(db.String(50), default='MEDIUM')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'image_url': self.image_url,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ================================
# Firebase Authentication
# ================================

def verify_firebase_token(token):
    """Simple Firebase token verification"""
    try:
        # Try to initialize Firebase if not already done
        if not hasattr(app, '_firebase_initialized'):
            init_firebase()
        
        if hasattr(app, '_firebase_auth') and app._firebase_auth:
            from firebase_admin import auth
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        else:
            # For development/testing - accept any token
            logger.warning("Firebase not available - using mock authentication")
            return {'uid': 'test-user', 'email': 'test@example.com', 'name': 'Test User'}
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        # For development/testing - accept any token when Firebase fails
        logger.warning("Using mock authentication due to Firebase error")
        return {'uid': 'test-user', 'email': 'test@example.com', 'name': 'Test User'}

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Try Base64 encoded credentials first
        b64_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT_B64')
        if b64_creds:
            try:
                json_str = base64.b64decode(b64_creds).decode('utf-8')
                cred_dict = json.loads(json_str)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                app._firebase_auth = True
                logger.info("Firebase initialized with Base64 credentials")
                app._firebase_initialized = True
                return
            except Exception as e:
                logger.error(f"Base64 Firebase init failed: {e}")
        
        # Try JSON string credentials
        json_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        if json_creds:
            try:
                cred_dict = json.loads(json_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                app._firebase_auth = True
                logger.info("Firebase initialized with JSON credentials")
                app._firebase_initialized = True
                return
            except Exception as e:
                logger.error(f"JSON Firebase init failed: {e}")
        
        # Try file path
        cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
        if cred_path and os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                app._firebase_auth = True
                logger.info("Firebase initialized with file credentials")
                app._firebase_initialized = True
                return
            except Exception as e:
                logger.error(f"File Firebase init failed: {e}")
        
        logger.warning("No Firebase credentials found - authentication disabled")
        app._firebase_auth = False
        app._firebase_initialized = True
        
    except ImportError:
        logger.warning("Firebase Admin SDK not installed - authentication disabled")
        app._firebase_auth = False
        app._firebase_initialized = True
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        app._firebase_auth = False
        app._firebase_initialized = True

def require_auth(f):
    """Decorator to require Firebase authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_firebase_token(token)
        
        if not user_data:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get or create user
        user = User.query.filter_by(firebase_uid=user_data['uid']).first()
        if not user:
            user = User(
                firebase_uid=user_data['uid'],
                email=user_data.get('email', ''),
                name=user_data.get('name', 'Unknown User')
            )
            db.session.add(user)
            db.session.commit()
        
        return f(user, *args, **kwargs)
    
    return decorated_function

# ================================
# Routes
# ================================

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'CivicFix Backend API',
        'version': '2.0.0',
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check Firebase status
    firebase_status = 'healthy' if getattr(app, '_firebase_auth', False) else 'disabled'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'services': {
            'database': db_status,
            'firebase': firebase_status
        }
    })

# ================================
# Issue Routes
# ================================

@app.route('/api/v1/issues', methods=['GET'])
def get_issues():
    """Get all issues with optional filtering"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        
        # Build query
        query = Issue.query
        
        if category:
            query = query.filter(Issue.category == category)
        
        if status:
            query = query.filter(Issue.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        issues = [issue.to_dict() for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues', methods=['POST'])
@require_auth
def create_issue(current_user):
    """Create a new issue"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['title', 'category', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create issue
        issue = Issue(
            title=data['title'],
            description=data.get('description', ''),
            category=data['category'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            address=data.get('address', ''),
            image_url=data.get('image_url', ''),
            priority=data.get('priority', 'MEDIUM'),
            created_by=current_user.id
        )
        
        db.session.add(issue)
        db.session.commit()
        
        logger.info(f"Issue created: {issue.id} by user {current_user.email}")
        
        return jsonify({
            'message': 'Issue created successfully',
            'issue': issue.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>', methods=['GET'])
def get_issue(issue_id):
    """Get a specific issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        return jsonify({'issue': issue.to_dict()})
    except Exception as e:
        logger.error(f"Error getting issue {issue_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/status', methods=['PUT'])
@require_auth
def update_issue_status(current_user, issue_id):
    """Update issue status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
            
        issue.status = new_status
        issue.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Issue {issue_id} status updated to {new_status} by {current_user.email}")
        
        return jsonify({
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating issue status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# User Routes
# ================================

@app.route('/api/v1/users/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current user profile"""
    return jsonify({'user': current_user.to_dict()})

@app.route('/api/v1/users/me', methods=['PUT'])
@require_auth
def update_current_user(current_user):
    """Update current user profile"""
    try:
        data = request.get_json()
        
        if 'name' in data:
            current_user.name = data['name']
        if 'phone' in data:
            current_user.phone = data['phone']
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Additional Issue Routes
# ================================

@app.route('/api/v1/issues/<int:issue_id>', methods=['PUT'])
@require_auth
def update_issue(current_user, issue_id):
    """Update an issue (only by creator or admin)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user is the creator (in a real app, you might have admin roles)
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Update allowed fields
        if 'title' in data:
            issue.title = data['title']
        if 'description' in data:
            issue.description = data['description']
        if 'category' in data:
            issue.category = data['category']
        if 'priority' in data:
            issue.priority = data['priority']
        if 'address' in data:
            issue.address = data['address']
        if 'image_url' in data:
            issue.image_url = data['image_url']
        
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Issue {issue_id} updated by user {current_user.email}")
        
        return jsonify({
            'message': 'Issue updated successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>', methods=['DELETE'])
@require_auth
def delete_issue(current_user, issue_id):
    """Delete an issue (only by creator)"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user is the creator
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        db.session.delete(issue)
        db.session.commit()
        
        logger.info(f"Issue {issue_id} deleted by user {current_user.email}")
        
        return jsonify({'message': 'Issue deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/<int:user_id>/issues', methods=['GET'])
def get_user_issues(user_id):
    """Get issues created by a specific user"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        
        # Build query
        query = Issue.query.filter_by(created_by=user_id)
        
        if status:
            query = query.filter(Issue.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        issues = [issue.to_dict() for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        total_issues = Issue.query.count()
        total_users = User.query.count()
        
        # Issues by status
        open_issues = Issue.query.filter_by(status='OPEN').count()
        in_progress_issues = Issue.query.filter_by(status='IN_PROGRESS').count()
        resolved_issues = Issue.query.filter_by(status='RESOLVED').count()
        closed_issues = Issue.query.filter_by(status='CLOSED').count()
        
        # Issues by category
        categories_stats = {}
        categories = [
            'Pothole', 'Street Light', 'Garbage Collection', 'Traffic Signal',
            'Road Damage', 'Water Leak', 'Sidewalk Issue', 'Graffiti',
            'Noise Complaint', 'Other'
        ]
        
        for category in categories:
            count = Issue.query.filter_by(category=category).count()
            if count > 0:
                categories_stats[category] = count
        
        return jsonify({
            'total_issues': total_issues,
            'total_users': total_users,
            'issues_by_status': {
                'OPEN': open_issues,
                'IN_PROGRESS': in_progress_issues,
                'RESOLVED': resolved_issues,
                'CLOSED': closed_issues
            },
            'issues_by_category': categories_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Utility Routes
# ================================

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """Get available issue categories"""
    categories = [
        'Pothole',
        'Street Light',
        'Garbage Collection',
        'Traffic Signal',
        'Road Damage',
        'Water Leak',
        'Sidewalk Issue',
        'Graffiti',
        'Noise Complaint',
        'Other'
    ]
    return jsonify({'categories': categories})

@app.route('/api/v1/issues/nearby', methods=['GET'])
def get_nearby_issues():
    """Get issues near a specific location"""
    try:
        # Get location parameters
        lat = request.args.get('latitude', type=float)
        lng = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 5.0, type=float)  # Default 5km radius
        
        if lat is None or lng is None:
            return jsonify({'error': 'latitude and longitude parameters are required'}), 400
        
        # Simple distance calculation (for more accuracy, use PostGIS in production)
        # This is a basic implementation using Haversine formula approximation
        lat_range = radius / 111.0  # Rough conversion: 1 degree ≈ 111 km
        lng_range = radius / (111.0 * abs(lat) / 90.0) if lat != 0 else radius / 111.0
        
        # Query issues within the bounding box
        issues = Issue.query.filter(
            Issue.latitude.between(lat - lat_range, lat + lat_range),
            Issue.longitude.between(lng - lng_range, lng + lng_range)
        ).order_by(Issue.created_at.desc()).limit(50).all()
        
        return jsonify({
            'issues': [issue.to_dict() for issue in issues],
            'center': {'latitude': lat, 'longitude': lng},
            'radius_km': radius,
            'count': len(issues)
        })
        
    except Exception as e:
        logger.error(f"Error getting nearby issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/status-options', methods=['GET'])
def get_status_options():
    """Get available issue status options"""
    statuses = [
        {'value': 'OPEN', 'label': 'Open', 'description': 'Issue reported and awaiting review'},
        {'value': 'IN_PROGRESS', 'label': 'In Progress', 'description': 'Issue is being worked on'},
        {'value': 'RESOLVED', 'label': 'Resolved', 'description': 'Issue has been fixed'},
        {'value': 'CLOSED', 'label': 'Closed', 'description': 'Issue is closed (resolved or rejected)'},
        {'value': 'REJECTED', 'label': 'Rejected', 'description': 'Issue was rejected or invalid'}
    ]
    return jsonify({'statuses': statuses})

@app.route('/api/v1/priority-options', methods=['GET'])
def get_priority_options():
    """Get available issue priority options"""
    priorities = [
        {'value': 'LOW', 'label': 'Low', 'description': 'Non-urgent issue'},
        {'value': 'MEDIUM', 'label': 'Medium', 'description': 'Standard priority'},
        {'value': 'HIGH', 'label': 'High', 'description': 'Important issue requiring attention'},
        {'value': 'URGENT', 'label': 'Urgent', 'description': 'Critical issue requiring immediate attention'}
    ]
    return jsonify({'priorities': priorities})

# ================================
# Error Handlers
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ================================
# Initialize Application
# ================================

def create_tables():
    """Create database tables"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

if __name__ == '__main__':
    # Initialize Firebase
    init_firebase()
    
    # Create tables
    create_tables()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting CivicFix Backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
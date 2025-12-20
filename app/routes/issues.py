from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import and_, or_, func
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueStatus, IssueSeverity, IssuePriority
from app.models.issue_media import IssueMedia, MediaType
from app.extensions import db
from app.utils.decorators import firebase_required, admin_required
from app.utils.validators import validate_issue_data
import logging
import uuid

issues_bp = Blueprint('issues', __name__)
logger = logging.getLogger(__name__)

@issues_bp.route('', methods=['POST'])
@firebase_required
def create_issue(current_user_firebase):
    """Create a new issue report"""
    try:
        data = request.get_json()
        
        # Validate input data
        validation_error = validate_issue_data(data)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Get user
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create issue
        issue = Issue(
            category=data['category'],
            description=data.get('description', ''),
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            severity=IssueSeverity(data.get('severity', 'MEDIUM')),
            priority=IssuePriority(data.get('priority', 'MEDIUM')),
            address=data.get('address', ''),
            created_by=user.id
        )
        
        db.session.add(issue)
        db.session.flush()  # Get the issue ID
        
        # Add media if provided
        media_urls = data.get('media_urls', [])
        for media_data in media_urls:
            media = IssueMedia(
                issue_id=issue.id,
                s3_url=media_data['url'],
                media_type=MediaType(media_data['type']),
                file_size=media_data.get('size')
            )
            db.session.add(media)
        
        db.session.commit()
        
        # Emit real-time event
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('issue_created', {
                'issue': issue.to_dict(),
                'location': {'lat': issue.latitude, 'lng': issue.longitude}
            })
        
        logger.info(f"Issue created: {issue.id} by user {user.email}")
        
        return jsonify({
            'message': 'Issue created successfully',
            'issue': issue.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@issues_bp.route('', methods=['GET'])
def get_issues():
    """Get issues with filtering and pagination"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        category = request.args.get('category')
        severity = request.args.get('severity')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)  # km
        user_id = request.args.get('user_id')
        
        # Build query
        query = Issue.query
        
        # Apply filters
        if status:
            query = query.filter(Issue.status == IssueStatus(status))
        
        if category:
            query = query.filter(Issue.category == category)
        
        if severity:
            query = query.filter(Issue.severity == IssueSeverity(severity))
        
        if user_id:
            query = query.filter(Issue.created_by == user_id)
        
        # Location-based filtering (approximate)
        if lat and lng:
            lat_range = radius / 111.0  # Rough conversion: 1 degree ≈ 111 km
            lng_range = radius / (111.0 * abs(lat) / 90.0) if lat != 0 else radius / 111.0
            
            query = query.filter(
                and_(
                    Issue.latitude.between(lat - lat_range, lat + lat_range),
                    Issue.longitude.between(lng - lng_range, lng + lng_range)
                )
            )
        
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
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting issues: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@issues_bp.route('/<issue_id>', methods=['GET'])
def get_issue(issue_id):
    """Get a specific issue by ID"""
    try:
        issue = Issue.query.get(issue_id)
        
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Include comments and status history
        issue_data = issue.to_dict()
        issue_data['comments'] = [comment.to_dict() for comment in issue.comments]
        issue_data['status_history'] = [history.to_dict() for history in issue.status_history]
        
        return jsonify({'issue': issue_data}), 200
        
    except Exception as e:
        logger.error(f"Error getting issue {issue_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@issues_bp.route('/<issue_id>/status', methods=['PUT'])
@firebase_required
@admin_required
def update_issue_status(current_user_firebase, issue_id):
    """Update issue status (Admin only)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        try:
            new_status_enum = IssueStatus(new_status)
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        
        # Update status and create history
        history = issue.update_status(new_status_enum, user.id)
        if notes:
            history.notes = notes
            db.session.commit()
        
        # Emit real-time event
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('issue_status_updated', {
                'issue_id': issue.id,
                'old_status': history.old_status.value if history.old_status else None,
                'new_status': new_status,
                'updated_by': user.name
            })
        
        logger.info(f"Issue {issue_id} status updated to {new_status} by {user.email}")
        
        return jsonify({
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating issue status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@issues_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available issue categories"""
    categories = [
        'Pothole',
        'Street Light',
        'Garbage',
        'Graffiti',
        'Traffic Signal',
        'Road Damage',
        'Sidewalk Issue',
        'Water Leak',
        'Noise Complaint',
        'Other'
    ]
    
    return jsonify({'categories': categories}), 200
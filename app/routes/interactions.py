from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.issue import Issue
from app.models.upvote import Upvote
from app.models.comment import Comment
from app.extensions import db
from app.utils.decorators import firebase_required
import logging

interactions_bp = Blueprint('interactions', __name__)
logger = logging.getLogger(__name__)

@interactions_bp.route('/issues/<issue_id>/upvote', methods=['POST'])
@firebase_required
def upvote_issue(current_user_firebase, issue_id):
    """Upvote an issue"""
    try:
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user already upvoted
        existing_upvote = Upvote.query.filter_by(
            issue_id=issue_id,
            user_id=user.id
        ).first()
        
        if existing_upvote:
            # Remove upvote (toggle)
            db.session.delete(existing_upvote)
            issue.upvote_count = max(0, issue.upvote_count - 1)
            action = 'removed'
        else:
            # Add upvote
            upvote = Upvote(
                issue_id=issue_id,
                user_id=user.id
            )
            db.session.add(upvote)
            issue.upvote_count += 1
            action = 'added'
        
        db.session.commit()
        
        # Emit real-time event
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('issue_upvoted', {
                'issue_id': issue_id,
                'upvote_count': issue.upvote_count,
                'action': action,
                'user_name': user.name
            })
        
        logger.info(f"Upvote {action} for issue {issue_id} by user {user.email}")
        
        return jsonify({
            'message': f'Upvote {action} successfully',
            'upvote_count': issue.upvote_count,
            'user_upvoted': action == 'added'
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Upvote already exists'}), 409
    except Exception as e:
        logger.error(f"Error handling upvote: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@interactions_bp.route('/issues/<issue_id>/comment', methods=['POST'])
@firebase_required
def add_comment(current_user_firebase, issue_id):
    """Add a comment to an issue"""
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({'error': 'Comment text is required'}), 400
        
        text = data['text'].strip()
        if len(text) < 1 or len(text) > 1000:
            return jsonify({'error': 'Comment must be between 1 and 1000 characters'}), 400
        
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Create comment
        comment = Comment(
            issue_id=issue_id,
            user_id=user.id,
            text=text
        )
        
        db.session.add(comment)
        
        # Update comment count
        issue.comment_count += 1
        
        db.session.commit()
        
        # Emit real-time event
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('comment_added', {
                'issue_id': issue_id,
                'comment': comment.to_dict(),
                'comment_count': issue.comment_count
            })
        
        logger.info(f"Comment added to issue {issue_id} by user {user.email}")
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@interactions_bp.route('/issues/<issue_id>/comments', methods=['GET'])
def get_comments(issue_id):
    """Get comments for an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get comments with pagination
        pagination = Comment.query.filter_by(issue_id=issue_id)\
            .order_by(Comment.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        comments = [comment.to_dict() for comment in pagination.items]
        
        return jsonify({
            'comments': comments,
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
        logger.error(f"Error getting comments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@interactions_bp.route('/comments/<comment_id>', methods=['DELETE'])
@firebase_required
def delete_comment(current_user_firebase, comment_id):
    """Delete a comment (only by comment author or admin)"""
    try:
        user = User.find_by_firebase_uid(current_user_firebase['uid'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check permissions (comment author or admin)
        if comment.user_id != user.id and user.role.value != 'ADMIN':
            return jsonify({'error': 'Permission denied'}), 403
        
        issue = comment.issue
        
        # Delete comment
        db.session.delete(comment)
        
        # Update comment count
        issue.comment_count = max(0, issue.comment_count - 1)
        
        db.session.commit()
        
        logger.info(f"Comment {comment_id} deleted by user {user.email}")
        
        return jsonify({'message': 'Comment deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
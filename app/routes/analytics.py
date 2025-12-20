from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueStatus, IssueSeverity
from app.models.upvote import Upvote
from app.models.comment import Comment
from app.extensions import db
from app.utils.decorators import firebase_required, admin_required
import logging

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/summary', methods=['GET'])
@firebase_required
@admin_required
def get_analytics_summary(current_user_firebase):
    """Get analytics summary (Admin only)"""
    try:
        # Date range parameters
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic counts
        total_issues = Issue.query.count()
        total_users = User.query.count()
        total_upvotes = Upvote.query.count()
        total_comments = Comment.query.count()
        
        # Issues by status
        status_counts = db.session.query(
            Issue.status,
            func.count(Issue.id)
        ).group_by(Issue.status).all()
        
        status_summary = {status.value: count for status, count in status_counts}
        
        # Issues by severity
        severity_counts = db.session.query(
            Issue.severity,
            func.count(Issue.id)
        ).group_by(Issue.severity).all()
        
        severity_summary = {severity.value: count for severity, count in severity_counts}
        
        # Issues by category
        category_counts = db.session.query(
            Issue.category,
            func.count(Issue.id)
        ).group_by(Issue.category).order_by(func.count(Issue.id).desc()).limit(10).all()
        
        category_summary = {category: count for category, count in category_counts}
        
        # Recent activity (last 30 days)
        recent_issues = Issue.query.filter(
            Issue.created_at >= start_date
        ).count()
        
        recent_users = User.query.filter(
            User.created_at >= start_date
        ).count()
        
        # Issues created per day (last 30 days)
        daily_issues = db.session.query(
            func.date(Issue.created_at).label('date'),
            func.count(Issue.id).label('count')
        ).filter(
            Issue.created_at >= start_date
        ).group_by(
            func.date(Issue.created_at)
        ).order_by('date').all()
        
        daily_issues_data = [
            {
                'date': date.isoformat(),
                'count': count
            }
            for date, count in daily_issues
        ]
        
        # Top reporters
        top_reporters = db.session.query(
            User.name,
            User.email,
            func.count(Issue.id).label('issue_count')
        ).join(Issue, User.id == Issue.created_by)\
        .group_by(User.id, User.name, User.email)\
        .order_by(func.count(Issue.id).desc())\
        .limit(10).all()
        
        top_reporters_data = [
            {
                'name': name,
                'email': email,
                'issue_count': count
            }
            for name, email, count in top_reporters
        ]
        
        # Resolution rate
        resolved_issues = Issue.query.filter(Issue.status == IssueStatus.RESOLVED).count()
        resolution_rate = (resolved_issues / total_issues * 100) if total_issues > 0 else 0
        
        # Average response time (time from REPORTED to IN_PROGRESS)
        # This would require more complex query with status history
        
        return jsonify({
            'summary': {
                'total_issues': total_issues,
                'total_users': total_users,
                'total_upvotes': total_upvotes,
                'total_comments': total_comments,
                'recent_issues': recent_issues,
                'recent_users': recent_users,
                'resolution_rate': round(resolution_rate, 2)
            },
            'status_breakdown': status_summary,
            'severity_breakdown': severity_summary,
            'category_breakdown': category_summary,
            'daily_issues': daily_issues_data,
            'top_reporters': top_reporters_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/issues/heatmap', methods=['GET'])
@firebase_required
@admin_required
def get_issues_heatmap(current_user_firebase):
    """Get issue locations for heatmap visualization"""
    try:
        # Optional filters
        status = request.args.get('status')
        category = request.args.get('category')
        days = request.args.get('days', type=int)
        
        query = db.session.query(
            Issue.latitude,
            Issue.longitude,
            Issue.severity,
            Issue.status,
            Issue.category
        )
        
        # Apply filters
        if status:
            query = query.filter(Issue.status == IssueStatus(status))
        
        if category:
            query = query.filter(Issue.category == category)
        
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Issue.created_at >= start_date)
        
        issues = query.all()
        
        heatmap_data = [
            {
                'lat': float(issue.latitude),
                'lng': float(issue.longitude),
                'severity': issue.severity.value,
                'status': issue.status.value,
                'category': issue.category,
                'weight': 1  # Can be adjusted based on severity or upvotes
            }
            for issue in issues
        ]
        
        return jsonify({
            'heatmap_data': heatmap_data,
            'total_points': len(heatmap_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
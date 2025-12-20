from app.extensions import db
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

def seed_initial_data():
    """Seed initial data for the application"""
    try:
        # Ensure all tables exist first
        db.create_all()
        
        # Check if we already have data
        if User.query.count() > 0:
            logger.info("Database already contains data, skipping seed")
            return
        
        logger.info("Seeding initial data...")
        
        # Create admin user (this would typically be done manually)
        # For demo purposes, we'll create a placeholder admin
        # In production, admin users should be created through a separate process
        
        # Note: This admin user won't be able to login until they authenticate with Firebase
        # and their Firebase UID is updated in the database
        admin_user = User(
            firebase_uid='admin-placeholder-uid',  # This should be updated with real Firebase UID
            name='System Admin',
            email='admin@civicfix.com',
            role=UserRole.ADMIN
        )
        
        db.session.add(admin_user)
        
        # Commit the changes
        db.session.commit()
        
        logger.info("Initial data seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding initial data: {str(e)}")
        db.session.rollback()
        # Don't raise in development mode
        pass

def seed_demo_data():
    """Seed demo data for development/testing"""
    try:
        from app.models.issue import Issue, IssueStatus, IssueSeverity, IssuePriority
        from app.models.issue_media import IssueMedia, MediaType
        from datetime import datetime, timedelta
        import uuid
        
        logger.info("Seeding demo data...")
        
        # Create demo citizen user
        demo_user = User(
            firebase_uid='demo-user-uid',
            name='Demo User',
            email='demo@civicfix.com',
            role=UserRole.CITIZEN
        )
        db.session.add(demo_user)
        db.session.flush()  # Get the user ID
        
        # Create demo issues
        demo_issues = [
            {
                'category': 'Pothole',
                'description': 'Large pothole on Main Street causing traffic issues',
                'latitude': 37.7749,
                'longitude': -122.4194,
                'severity': IssueSeverity.HIGH,
                'status': IssueStatus.REPORTED,
                'priority': IssuePriority.HIGH,
                'address': '123 Main Street, San Francisco, CA'
            },
            {
                'category': 'Street Light',
                'description': 'Broken street light near the park entrance',
                'latitude': 37.7849,
                'longitude': -122.4094,
                'severity': IssueSeverity.MEDIUM,
                'status': IssueStatus.IN_PROGRESS,
                'priority': IssuePriority.MEDIUM,
                'address': '456 Park Avenue, San Francisco, CA'
            },
            {
                'category': 'Graffiti',
                'description': 'Graffiti on public building wall',
                'latitude': 37.7649,
                'longitude': -122.4294,
                'severity': IssueSeverity.LOW,
                'status': IssueStatus.RESOLVED,
                'priority': IssuePriority.LOW,
                'address': '789 Public Square, San Francisco, CA'
            }
        ]
        
        for issue_data in demo_issues:
            issue = Issue(
                category=issue_data['category'],
                description=issue_data['description'],
                latitude=issue_data['latitude'],
                longitude=issue_data['longitude'],
                severity=issue_data['severity'],
                status=issue_data['status'],
                priority=issue_data['priority'],
                address=issue_data['address'],
                created_by=demo_user.id,
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            db.session.add(issue)
        
        db.session.commit()
        logger.info("Demo data seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding demo data: {str(e)}")
        db.session.rollback()
        raise
import uuid
from datetime import datetime
from enum import Enum
from app.extensions import db

class IssueStatus(Enum):
    REPORTED = "REPORTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class IssueSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IssuePriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)
    severity = db.Column(db.Enum(IssueSeverity), nullable=False, default=IssueSeverity.MEDIUM)
    status = db.Column(db.Enum(IssueStatus), nullable=False, default=IssueStatus.REPORTED, index=True)
    priority = db.Column(db.Enum(IssuePriority), nullable=False, default=IssuePriority.MEDIUM)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for better tracking
    address = db.Column(db.String(255), nullable=True)
    upvote_count = db.Column(db.Integer, nullable=False, default=0)
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Relationships
    media = db.relationship('IssueMedia', backref='issue', lazy=True, cascade='all, delete-orphan')
    upvotes = db.relationship('Upvote', backref='issue', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='issue', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('StatusHistory', backref='issue', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Issue {self.id}: {self.category}>'
    
    def to_dict(self, include_reporter=True):
        data = {
            'id': self.id,
            'category': self.category,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'severity': self.severity.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'address': self.address,
            'upvote_count': self.upvote_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'media': [media.to_dict() for media in self.media]
        }
        
        if include_reporter and self.reporter:
            data['reporter'] = {
                'id': self.reporter.id,
                'name': self.reporter.name,
                'email': self.reporter.email
            }
        
        return data
    
    def update_status(self, new_status, updated_by_id):
        """Update issue status and create history record"""
        from app.models.status_history import StatusHistory
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Create status history record
        history = StatusHistory(
            issue_id=self.id,
            old_status=old_status,
            new_status=new_status,
            updated_by=updated_by_id
        )
        db.session.add(history)
        db.session.commit()
        
        return history
import uuid
from datetime import datetime
from app.extensions import db
from app.models.issue import IssueStatus

class StatusHistory(db.Model):
    __tablename__ = 'status_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)
    old_status = db.Column(db.Enum(IssueStatus), nullable=True)  # Null for initial status
    new_status = db.Column(db.Enum(IssueStatus), nullable=False)
    updated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)  # Optional notes about the status change
    
    def __repr__(self):
        return f'<StatusHistory {self.id}: {self.old_status} -> {self.new_status}>'
    
    def to_dict(self, include_user=True):
        data = {
            'id': self.id,
            'issue_id': self.issue_id,
            'old_status': self.old_status.value if self.old_status else None,
            'new_status': self.new_status.value,
            'timestamp': self.timestamp.isoformat(),
            'notes': self.notes
        }
        
        if include_user and self.updated_by_user:
            data['updated_by'] = {
                'id': self.updated_by_user.id,
                'name': self.updated_by_user.name,
                'email': self.updated_by_user.email
            }
        
        return data
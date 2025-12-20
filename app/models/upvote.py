import uuid
from datetime import datetime
from app.extensions import db

class Upvote(db.Model):
    __tablename__ = 'upvotes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Ensure one upvote per user per issue
    __table_args__ = (db.UniqueConstraint('issue_id', 'user_id', name='unique_upvote'),)
    
    def __repr__(self):
        return f'<Upvote {self.id}: Issue {self.issue_id} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }
import uuid
from datetime import datetime
from app.extensions import db

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id}: Issue {self.issue_id}>'
    
    def to_dict(self, include_user=True):
        data = {
            'id': self.id,
            'issue_id': self.issue_id,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }
        
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'name': self.user.name,
                'email': self.user.email
            }
        
        return data
import uuid
from datetime import datetime
from enum import Enum
from app.extensions import db

class MediaType(Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

class IssueMedia(db.Model):
    __tablename__ = 'issue_media'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)
    s3_url = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.Enum(MediaType), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<IssueMedia {self.id}: {self.media_type.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            's3_url': self.s3_url,
            'media_type': self.media_type.value,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat()
        }
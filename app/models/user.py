import uuid
from datetime import datetime
from enum import Enum
from app.extensions import db

class UserRole(Enum):
    CITIZEN = "CITIZEN"
    ADMIN = "ADMIN"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CITIZEN)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('Issue', backref='reporter', lazy=True, cascade='all, delete-orphan')
    upvotes = db.relationship('Upvote', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')
    status_updates = db.relationship('StatusHistory', backref='updated_by_user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def find_by_firebase_uid(cls, firebase_uid):
        return cls.query.filter_by(firebase_uid=firebase_uid).first()
    
    @classmethod
    def create_user(cls, firebase_uid, name, email, role=UserRole.CITIZEN):
        user = cls(
            firebase_uid=firebase_uid,
            name=name,
            email=email,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user
"""
CivicFix Backend - Neon PostgreSQL + Supabase Storage
Production-ready Flask application with modern cloud services
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import json
import uuid
from werkzeug.utils import secure_filename
import jwt
from functools import lru_cache, wraps
import time
import hashlib
import secrets
import asyncio

# Supabase Storage imports
from supabase import create_client, Client
from storage3 import create_client as create_storage_client

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable is required")

# Database configuration - Neon PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required for Neon PostgreSQL")

# Ensure proper PostgreSQL URL format
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure connection pooling for Neon PostgreSQL
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,  # Recycle connections after 5 minutes
    'pool_pre_ping': True,  # Verify connections before using them
    'max_overflow': 20,
    'pool_timeout': 30,
    'connect_args': {
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    }
}

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    origins = [origin.strip() for origin in cors_origins.split(',')]
    CORS(app, origins=origins)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# Supabase Storage Configuration
# ================================

class SupabaseStorageService:
    """Supabase Storage service for media uploads"""
    
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        self.supabase_service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        self.bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'civicfix-media')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        self.init_storage()
    
    def init_storage(self):
        """Initialize Supabase client and storage"""
        try:
            # Use service role key for storage operations (has full access)
            storage_key = self.supabase_service_key or self.supabase_key
            
            self.supabase: Client = create_client(self.supabase_url, storage_key)
            self.storage = self.supabase.storage
            
            # Test connection if not skipping validation
            if os.environ.get('SKIP_VALIDATION') != 'true':
                try:
                    buckets = self.storage.list_buckets()
                    logger.info(f"Supabase Storage initialized. Available buckets: {[b.name for b in buckets]}")
                    
                    # Check if our bucket exists
                    bucket_exists = any(b.name == self.bucket_name for b in buckets)
                    if not bucket_exists:
                        logger.warning(f"Bucket '{self.bucket_name}' not found. Creating it...")
                        try:
                            # Create public bucket
                            self.storage.create_bucket(
                                self.bucket_name,
                                options={'public': True}
                            )
                            logger.info(f"✅ Created public bucket: {self.bucket_name}")
                        except Exception as e:
                            logger.error(f"Failed to create bucket: {e}")
                            logger.info("Please create the bucket manually in Supabase dashboard")
                    else:
                        logger.info(f"✅ Using existing bucket: {self.bucket_name}")
                        
                except Exception as e:
                    logger.warning(f"Could not validate storage: {e}")
            else:
                logger.info(f"Supabase Storage initialized (validation skipped)")
                
        except Exception as e:
            logger.error(f"Supabase Storage initialization failed: {e}")
            if os.environ.get('SKIP_VALIDATION') != 'true':
                raise ValueError(f"Failed to initialize Supabase Storage: {e}")
            else:
                logger.warning("Continuing without Supabase Storage (validation skipped)")
                self.supabase = None
                self.storage = None

    def upload_file(self, file_data, file_name, content_type='application/octet-stream'):
        """Upload file to Supabase Storage"""
        try:
            # Generate unique filename
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            unique_filename = f"issues/{uuid.uuid4()}.{file_extension}" if file_extension else f"issues/{uuid.uuid4()}"
            
            logger.info(f"Uploading file to Supabase Storage: {unique_filename}, size: {len(file_data)} bytes, type: {content_type}")
            
            # Upload file to Supabase Storage with proper options
            result = self.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=file_data,
                file_options={
                    "content-type": content_type, 
                    "upsert": "true",
                    "cache-control": "3600"
                }
            )
            
            # Check if upload was successful
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase upload error: {result.error}")
                return None, str(result.error)
            
            # Generate public URL
            file_url = self.storage.from_(self.bucket_name).get_public_url(unique_filename)
            
            logger.info(f"✅ File uploaded successfully to Supabase Storage: {unique_filename}")
            logger.info(f"📎 Public URL: {file_url}")
            return file_url, None
            
        except Exception as e:
            logger.error(f"❌ Supabase Storage upload failed: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            return None, str(e)
    
    def delete_file(self, file_url):
        """Delete file from Supabase Storage"""
        try:
            # Extract path from URL
            # URL format: https://xxx.supabase.co/storage/v1/object/public/bucket-name/path
            if '/storage/v1/object/public/' in file_url:
                parts = file_url.split('/storage/v1/object/public/')
                if len(parts) == 2:
                    bucket_and_path = parts[1]
                    path_parts = bucket_and_path.split('/', 1)
                    if len(path_parts) == 2:
                        path = path_parts[1]
                        self.storage.from_(self.bucket_name).remove([path])
                        logger.info(f"File deleted from Supabase Storage: {path}")
                        return True
            
            logger.warning(f"Could not parse Supabase Storage URL: {file_url}")
            return False
            
        except Exception as e:
            logger.error(f"Supabase Storage delete failed: {e}")
            return False

# Initialize Supabase Storage service
try:
    storage_service = SupabaseStorageService()
    logger.info("Supabase Storage service initialized successfully")
except Exception as e:
    logger.error(f"Supabase Storage service initialization failed: {e}")
    if os.environ.get('SKIP_VALIDATION') == 'true':
        logger.warning("Continuing without Supabase Storage (validation skipped)")
        storage_service = None
    else:
        raise

# ================================
# AI Service and Timeline Service
# ================================

# Import AI service client and timeline service
from ai_service_client import ai_client
from timeline_service import TimelineService, EventType, ActorType

# Initialize timeline service
timeline_service = TimelineService(db)
logger.info("Timeline service initialized successfully")

# ================================
# Database Initialization
# ================================

def init_database():
    """Initialize database tables using SQLAlchemy"""
    try:
        logger.info("🔧 Initializing database...")
        
        # Create all tables
        with app.app_context():
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                logger.info(f"📋 Found existing tables: {', '.join(existing_tables)}")
            else:
                logger.info("📋 No existing tables found. Creating new tables...")
            
            # Create all tables defined in models
            db.create_all()
            
            # Create indexes for better performance
            try:
                indexes_to_create = [
                    ("idx_users_firebase_uid", "users", "firebase_uid"),
                    ("idx_users_email", "users", "email"),
                    ("idx_issues_created_by", "issues", "created_by"),
                    ("idx_issues_category", "issues", "category"),
                    ("idx_issues_status", "issues", "status"),
                    ("idx_comments_issue_id", "comments", "issue_id"),
                    ("idx_comments_user_id", "comments", "user_id"),
                ]
                
                for index_name, table_name, column_name in indexes_to_create:
                    try:
                        # Use a new connection for each index to avoid transaction issues
                        with db.engine.begin() as conn:
                            # Check if index exists
                            result = conn.execute(db.text(f"""
                                SELECT 1 FROM pg_indexes 
                                WHERE indexname = '{index_name}'
                            """))
                            
                            if not result.fetchone():
                                # Create index
                                conn.execute(db.text(f"""
                                    CREATE INDEX IF NOT EXISTS {index_name} 
                                    ON {table_name}({column_name})
                                """))
                                logger.info(f"   ✅ Created index: {index_name}")
                            else:
                                logger.info(f"   ℹ️  Index already exists: {index_name}")
                    except Exception as idx_error:
                        logger.warning(f"   ⚠️  Could not create index {index_name}: {idx_error}")
                    
            except Exception as idx_error:
                logger.warning(f"⚠️  Index creation failed: {idx_error}")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                logger.info(f"✅ Database initialized successfully with tables: {', '.join(tables)}")
                
                # Log table details
                for table in tables:
                    columns = inspector.get_columns(table)
                    column_names = [col['name'] for col in columns]
                    logger.info(f"   📊 Table '{table}': {len(column_names)} columns")
            else:
                logger.warning("⚠️  No tables found after initialization")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        if os.environ.get('SKIP_VALIDATION') != 'true':
            raise
        else:
            logger.warning("Continuing despite database initialization failure (validation skipped)")

# Initialize database on startup
if os.environ.get('SKIP_VALIDATION') != 'true':
    init_database()
else:
    logger.info("Database initialization skipped (SKIP_VALIDATION=true)")

# ================================
# Models
# ================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    photo_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    password_hash = db.Column(db.String(255))
    language = db.Column(db.String(10), default='en')
    onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Preferences
    notifications_enabled = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)
    anonymous_reporting = db.Column(db.Boolean, default=False)
    satellite_view = db.Column(db.Boolean, default=False)
    save_to_gallery = db.Column(db.Boolean, default=True)
    
    # Appearance settings
    theme_color = db.Column(db.String(20), default='blue')
    font_size = db.Column(db.String(20), default='medium')
    
    # Notification settings
    issue_updates_notifications = db.Column(db.Boolean, default=True)
    community_activity_notifications = db.Column(db.Boolean, default=True)
    system_alerts_notifications = db.Column(db.Boolean, default=True)
    
    # Media settings
    photo_quality = db.Column(db.String(20), default='high')
    video_quality = db.Column(db.String(20), default='high')
    auto_upload = db.Column(db.Boolean, default=False)
    
    # Storage settings
    cache_auto_clear = db.Column(db.Boolean, default=True)
    backup_sync = db.Column(db.Boolean, default=False)
    
    # Privacy settings
    location_services = db.Column(db.Boolean, default=True)
    data_collection = db.Column(db.Boolean, default=True)
    
    # Accessibility settings
    high_contrast = db.Column(db.Boolean, default=False)
    large_text = db.Column(db.Boolean, default=False)
    voice_over = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    issues = db.relationship('Issue', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            'name': self.name,
            'display_name': self.display_name,
            'phone': self.phone,
            'photo_url': self.photo_url,
            'bio': self.bio,
            'language': self.language,
            'onboarding_completed': self.onboarding_completed,
            
            # Preferences
            'notifications_enabled': self.notifications_enabled,
            'dark_mode': self.dark_mode,
            'anonymous_reporting': self.anonymous_reporting,
            'satellite_view': self.satellite_view,
            'save_to_gallery': self.save_to_gallery,
            
            # Appearance settings
            'theme_color': self.theme_color,
            'font_size': self.font_size,
            
            # Notification settings
            'issue_updates_notifications': self.issue_updates_notifications,
            'community_activity_notifications': self.community_activity_notifications,
            'system_alerts_notifications': self.system_alerts_notifications,
            
            # Media settings
            'photo_quality': self.photo_quality,
            'video_quality': self.video_quality,
            'auto_upload': self.auto_upload,
            
            # Storage settings
            'cache_auto_clear': self.cache_auto_clear,
            'backup_sync': self.backup_sync,
            
            # Privacy settings
            'location_services': self.location_services,
            'data_collection': self.data_collection,
            
            # Accessibility settings
            'high_contrast': self.high_contrast,
            'large_text': self.large_text,
            'voice_over': self.voice_over,
            
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'trust_score': self.calculate_trust_score()
        }

    def calculate_trust_score(self):
        """Calculate user trust score based on verified issues"""
        try:
            # Base score
            score = 50
            
            # Get user's issues
            total_issues = 0
            verified_issues = 0
            rejected_issues = 0
            fake_issues = 0
            
            if self.issues:
                total_issues = len(self.issues)
                for issue in self.issues:
                    if issue.status == 'CLOSED' or issue.status == 'RESOLVED':
                        verified_issues += 1
                    elif issue.status == 'REJECTED':
                        rejected_issues += 1
                        # Check if rejected due to fake/manipulation
                        if issue.ai_verification_status == 'REJECTED':
                            fake_issues += 1
            
            # Calculate adjustments
            score += (verified_issues * 5)
            score -= (rejected_issues * 2)
            score -= (fake_issues * 10)
            
            # Cap score between 0 and 100
            return max(0, min(100, score))
        except:
            return 50

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='OPEN')
    priority = db.Column(db.String(50), default='MEDIUM')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    image_urls = db.Column(db.Text)
    upvotes = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Verification fields
    ai_verification_status = db.Column(db.String(20), default='PENDING')
    ai_confidence_score = db.Column(db.Float, default=0.0)
    government_images = db.Column(db.Text)  # JSON array
    government_notes = db.Column(db.Text)
    citizen_verification_status = db.Column(db.String(20))
    escalation_status = db.Column(db.String(20), default='NONE')
    escalation_date = db.Column(db.DateTime)
    resolution_date = db.Column(db.DateTime)
    
    comments = db.relationship('Comment', backref='issue', lazy=True, cascade='all, delete-orphan')
    
    def get_image_urls(self):
        if self.image_urls:
            try:
                return json.loads(self.image_urls)
            except:
                return []
        elif self.image_url:
            return [self.image_url]
        return []
    
    def set_image_urls(self, urls):
        if urls:
            self.image_urls = json.dumps(urls)
            self.image_url = urls[0] if urls else None
        else:
            self.image_urls = None
            self.image_url = None
    
    def get_government_images(self):
        if self.government_images:
            try:
                return json.loads(self.government_images)
            except:
                return []
        return []
    
    def set_government_images(self, urls):
        if urls:
            self.government_images = json.dumps(urls)
        else:
            self.government_images = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'image_urls': self.get_image_urls(),
            'upvotes': self.upvotes,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # AI Verification fields
            'ai_verification_status': self.ai_verification_status,
            'ai_confidence_score': self.ai_confidence_score,
            'government_images': self.get_government_images(),
            'government_notes': self.government_notes,
            'citizen_verification_status': self.citizen_verification_status,
            'escalation_status': self.escalation_status,
            'escalation_date': self.escalation_date.isoformat() if self.escalation_date else None,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.text,
            'issue_id': self.issue_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_display_name': self.user.display_name if self.user else None,
            'user_photo': self.user.photo_url if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.created_at.isoformat() if self.created_at else None
        }

# ================================
# Supabase Authentication
# ================================

@lru_cache(maxsize=1)
def get_supabase_jwt_secret():
    """Get Supabase JWT secret from environment"""
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET not found in environment variables")
        return None
    logger.info(f"Supabase JWT secret loaded: {jwt_secret[:20]}... (length: {len(jwt_secret)})")
    return jwt_secret

def verify_supabase_token(token):
    """Verify Supabase JWT access token"""
    try:
        jwt_secret = get_supabase_jwt_secret()
        if not jwt_secret:
            return None
        
        if not token or not isinstance(token, str):
            return None
        
        token_parts = token.split('.')
        if len(token_parts) != 3:
            return None
        
        try:
            header = jwt.get_unverified_header(token)
            algorithm = header.get('alg', 'HS256')
        except Exception as e:
            logger.error(f"Failed to decode token header: {e}")
            return None
        
        decoded_token = None
        
        if algorithm == 'HS256':
            try:
                decoded_token = jwt.decode(
                    token, jwt_secret, algorithms=['HS256'],
                    options={"verify_exp": True, "verify_aud": False, "verify_iat": False, "verify_nbf": False}
                )
            except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError, jwt.InvalidTokenError) as e:
                logger.error(f"Token verification failed: {e}")
                return None
        elif algorithm in ['ES256', 'RS256']:
            try:
                decoded_token = jwt.decode(
                    token, options={"verify_signature": False, "verify_exp": True, "verify_aud": False, "verify_iat": False, "verify_nbf": False}
                )
                current_time = int(time.time())
                if 'exp' in decoded_token and decoded_token['exp'] < current_time:
                    return None
            except Exception as e:
                logger.error(f"Failed to decode token: {e}")
                return None
        else:
            return None
        
        if not decoded_token or 'sub' not in decoded_token:
            return None
        
        user_data = {
            'uid': decoded_token['sub'],
            'email': decoded_token.get('email', ''),
            'name': (decoded_token.get('user_metadata', {}).get('full_name') or 
                    decoded_token.get('user_metadata', {}).get('name') or
                    decoded_token.get('name') or
                    (decoded_token.get('email', '').split('@')[0] if decoded_token.get('email') else 'User')),
            'provider': 'supabase',
            'user_metadata': decoded_token.get('user_metadata', {})
        }
        
        return user_data
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

def require_auth(f):
    """Decorator to require Supabase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header[7:].strip()
        
        if not token or len(token) > 8192:
            return jsonify({'error': 'Invalid token'}), 401
        
        if len(token.split('.')) != 3:
            return jsonify({'error': 'Malformed JWT token'}), 401
        
        user_data = verify_supabase_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        try:
            user = sync_user_to_database(user_data)
            if not user:
                return jsonify({'error': 'User synchronization failed'}), 500
            
            if not check_user_permissions(user, request.endpoint):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(user, *args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated_function

def sync_user_to_database(user_data):
    """Sync Supabase user data to local database - Performance Optimized"""
    try:
        if not user_data or not user_data.get('uid'):
            return None
        
        uid = user_data['uid']
        
        # Optimized query with specific fields only
        user = db.session.query(User).filter_by(firebase_uid=uid).first()
        
        if not user:
            email = user_data.get('email', '').strip() or f"user_{uid[:16]}@civicfix.temp"
            name = user_data.get('name', '').strip() or f"User_{uid[:8]}"
            
            user = User(
                firebase_uid=uid,
                email=email,
                name=name,
                display_name=name,
                photo_url=user_data.get('user_metadata', {}).get('avatar_url', '')
            )
            db.session.add(user)
            
            # Use bulk insert for better performance if needed
            try:
                db.session.commit()
                logger.info(f"Created new user: {user.email}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to create user: {e}")
                return None
        
        return user
    except Exception as e:
        logger.error(f"Failed to sync user: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return None

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash"""
    try:
        salt, password_hash = stored_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False

def check_user_permissions(user, endpoint):
    """Role-based access control"""
    return True

# ================================
# Routes
# ================================

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'CivicFix Backend API',
        'version': '3.0.0',
        'status': 'running',
        'database': 'Neon PostgreSQL',
        'storage': 'Supabase Storage',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    supabase_status = 'healthy' if get_supabase_jwt_secret() else 'not_configured'
    
    try:
        if storage_service and storage_service.storage:
            storage_service.storage.list_buckets()
            storage_status = 'healthy'
        else:
            storage_status = 'disabled'
    except Exception as e:
        storage_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '3.0.0',
        'services': {
            'database': db_status,
            'supabase_auth': supabase_status,
            'supabase_storage': storage_status
        }
    })

@app.route('/init-db', methods=['POST'])
def manual_init_database():
    """Manually initialize database tables - Use this if tables don't exist"""
    try:
        logger.info("Manual database initialization requested")
        
        # Check if tables already exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"Existing tables before init: {existing_tables}")
        
        # Create all tables
        db.create_all()
        
        # Add missing columns to users table if needed
        logger.info("Checking for missing columns in users table...")
        if 'users' in existing_tables or 'users' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('users')]
            logger.info(f"Existing user columns: {len(existing_columns)}")
            
            user_columns = {
                'theme_color': "VARCHAR(20) DEFAULT 'blue'",
                'font_size': "VARCHAR(20) DEFAULT 'medium'",
                'issue_updates_notifications': "BOOLEAN DEFAULT TRUE",
                'community_activity_notifications': "BOOLEAN DEFAULT TRUE",
                'system_alerts_notifications': "BOOLEAN DEFAULT TRUE",
                'photo_quality': "VARCHAR(20) DEFAULT 'high'",
                'video_quality': "VARCHAR(20) DEFAULT 'high'",
                'auto_upload': "BOOLEAN DEFAULT FALSE",
                'cache_auto_clear': "BOOLEAN DEFAULT TRUE",
                'backup_sync': "BOOLEAN DEFAULT FALSE",
                'location_services': "BOOLEAN DEFAULT TRUE",
                'data_collection': "BOOLEAN DEFAULT TRUE",
                'high_contrast': "BOOLEAN DEFAULT FALSE",
                'large_text': "BOOLEAN DEFAULT FALSE",
                'voice_over': "BOOLEAN DEFAULT FALSE",
            }
            
            missing_user_columns = {col: definition for col, definition in user_columns.items() 
                              if col not in existing_columns}
            
            if missing_user_columns:
                logger.info(f"Adding {len(missing_user_columns)} missing columns to users table...")
                for col_name, col_definition in missing_user_columns.items():
                    try:
                        sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_definition}"
                        db.session.execute(db.text(sql))
                        db.session.commit()
                        logger.info(f"Added column: {col_name}")
                    except Exception as e:
                        logger.error(f"Failed to add column {col_name}: {e}")
                        db.session.rollback()
            else:
                logger.info("All user columns exist")
        
        # Add missing columns to issues table if needed
        logger.info("Checking for missing columns in issues table...")
        if 'issues' in existing_tables or 'issues' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('issues')]
            logger.info(f"Existing issue columns: {len(existing_columns)}")
            
            issue_columns = {
                'ai_verification_status': "VARCHAR(20) DEFAULT 'PENDING'",
                'ai_confidence_score': "FLOAT DEFAULT 0.0",
                'government_images': "TEXT",
                'government_notes': "TEXT",
                'citizen_verification_status': "VARCHAR(20)",
                'escalation_status': "VARCHAR(20) DEFAULT 'NONE'",
                'escalation_date': "TIMESTAMP",
                'resolution_date': "TIMESTAMP",
            }
            
            missing_issue_columns = {col: definition for col, definition in issue_columns.items() 
                              if col not in existing_columns}
            
            if missing_issue_columns:
                logger.info(f"Adding {len(missing_issue_columns)} missing columns to issues table...")
                for col_name, col_definition in missing_issue_columns.items():
                    try:
                        sql = f"ALTER TABLE issues ADD COLUMN IF NOT EXISTS {col_name} {col_definition}"
                        db.session.execute(db.text(sql))
                        db.session.commit()
                        logger.info(f"Added column: {col_name}")
                    except Exception as e:
                        logger.error(f"Failed to add column {col_name}: {e}")
                        db.session.rollback()
            else:
                logger.info("All issue columns exist")
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables_after = inspector.get_table_names()
        
        logger.info(f"Tables after init: {tables_after}")
        
        # Get column counts
        table_info = {}
        for table in tables_after:
            columns = inspector.get_columns(table)
            table_info[table] = len(columns)
        
        return jsonify({
            'message': 'Database initialized successfully',
            'tables_before': existing_tables,
            'tables_after': tables_after,
            'new_tables': list(set(tables_after) - set(existing_tables)),
            'table_info': table_info
        })
    except Exception as e:
        logger.error(f"Manual database initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Database initialization failed: {str(e)}'}), 500

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """Get all issue categories"""
    categories = [
        'Road Infrastructure',
        'Water & Drainage',
        'Street Lighting',
        'Waste Management',
        'Traffic & Transportation',
        'Public Safety',
        'Parks & Recreation',
        'Utilities & Power',
        'Building & Construction',
        'Environmental Issues',
        'Public Health',
        'Community Services',
        'Other'
    ]
    return jsonify({'categories': categories})

# ================================
# File Upload Routes (Supabase Storage)
# ================================

@app.route('/api/v1/upload', methods=['POST'])
@require_auth
def upload_file(current_user):
    """Upload file to Supabase Storage"""
    try:
        if not storage_service:
            return jsonify({'error': 'File upload service not available'}), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'}
        max_size = 50 * 1024 * 1024 if file_extension in video_extensions else 10 * 1024 * 1024
        
        if file_size > max_size:
            return jsonify({'error': f'File too large. Max: {"50MB" if file_extension in video_extensions else "10MB"}'}), 400
        
        file_data = file.read()
        content_type = f'video/{file_extension}' if file_extension in video_extensions else file.content_type or f'image/{file_extension}'
        
        file_url, error = storage_service.upload_file(file_data, file.filename, content_type)
        
        if error:
            return jsonify({'error': f'Upload failed: {error}'}), 500
        
        logger.info(f"File uploaded by {current_user.email}: {file_url}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_url': file_url,
            'file_name': file.filename,
            'file_size': file_size,
            'file_type': 'video' if file_extension in video_extensions else 'image'
        }), 201
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/upload-media', methods=['POST'])
@require_auth
def upload_issue_media(current_user):
    """Upload media files for issues"""
    try:
        if not storage_service:
            logger.error("Storage service not available")
            return jsonify({'error': 'File upload service not available'}), 503
        
        if 'files' not in request.files:
            logger.error("No files provided in request")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            logger.error("No files selected")
            return jsonify({'error': 'No files selected'}), 400
        
        if len(files) > 10:  # Increased from 8 to 10
            logger.error(f"Too many files: {len(files)}")
            return jsonify({'error': 'Maximum 10 files allowed'}), 400
        
        uploaded_files = []
        errors = []
        total_size = 0
        
        # Updated file type restrictions and size limits
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'flv', '3gp'}
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'flv', '3gp'}
        
        logger.info(f"Processing {len(files)} files for user {current_user.email}")
        
        for i, file in enumerate(files):
            if file.filename == '':
                continue
            
            try:
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_extension not in allowed_extensions:
                    error_msg = f"{file.filename}: Invalid file type (.{file_extension})"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Get file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                # Increased size limits significantly
                max_size = 500 * 1024 * 1024 if file_extension in video_extensions else 50 * 1024 * 1024  # 500MB for videos, 50MB for images
                
                if file_size > max_size:
                    max_size_mb = max_size // (1024 * 1024)
                    error_msg = f"{file.filename}: File too large ({file_size // (1024 * 1024)}MB > {max_size_mb}MB limit)"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                total_size += file_size
                
                # Increased total size limit
                if total_size > 1024 * 1024 * 1024:  # 1GB total limit
                    error_msg = f"{file.filename}: Total size exceeds 1GB limit"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Read file data
                file_data = file.read()
                content_type = f'video/{file_extension}' if file_extension in video_extensions else file.content_type or f'image/{file_extension}'
                
                logger.info(f"Uploading file {i+1}/{len(files)}: {file.filename} ({file_size} bytes, {content_type})")
                
                # Upload to Supabase Storage
                file_url, error = storage_service.upload_file(file_data, f"issue_media_{file.filename}", content_type)
                
                if error:
                    error_msg = f"{file.filename}: Upload failed - {error}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                else:
                    uploaded_files.append({
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_size': file_size,
                        'file_type': 'video' if file_extension in video_extensions else 'image'
                    })
                    logger.info(f"✅ Successfully uploaded: {file.filename}")
                    
            except Exception as e:
                error_msg = f"{file.filename}: {str(e)}"
                logger.error(f"Error processing file {file.filename}: {e}")
                errors.append(error_msg)
        
        media_urls = [f['file_url'] for f in uploaded_files]
        
        # Log final results
        logger.info(f"Upload completed for user {current_user.email}: {len(uploaded_files)} files uploaded, {len(errors)} errors")
        if errors:
            logger.warning(f"Upload errors: {errors}")
        
        response_data = {
            'message': f'{len(uploaded_files)} files uploaded successfully',
            'media_urls': media_urls,
            'uploaded_files': uploaded_files,
            'errors': errors,
            'total_size': total_size,
            'summary': {
                'images': len([f for f in uploaded_files if f['file_type'] == 'image']),
                'videos': len([f for f in uploaded_files if f['file_type'] == 'video']),
                'total_files': len(uploaded_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        }
        
        status_code = 201 if uploaded_files else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# ================================
# Issue Routes
# ================================

@app.route('/api/v1/issues', methods=['GET'])
def get_issues():
    """Get all issues with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = Issue.query
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(db.or_(
                Issue.title.ilike(search_term),
                Issue.description.ilike(search_term),
                Issue.address.ilike(search_term)
            ))
        
        if category and category.lower() != 'all':
            query = query.filter(Issue.category == category)
        
        if status:
            query = query.filter(Issue.status == status)
            
        # Location filtering
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', type=float) # in kilometers
        
        if latitude is not None and longitude is not None and radius is not None:
             # Haversine formula for distance calculation
            from sqlalchemy import func
            
            # Earth's radius in kilometers
            R = 6371
            
            # Calculate distance using SQL
            distance_expr = func.acos(
                func.sin(func.radians(latitude)) * func.sin(func.radians(Issue.latitude)) +
                func.cos(func.radians(latitude)) * func.cos(func.radians(Issue.latitude)) *
                func.cos(func.radians(Issue.longitude) - func.radians(longitude))
            ) * R
            
            query = query.filter(distance_expr <= radius)
            
            # Add distance to results if needed, or just order by distance
            # query = query.order_by(distance_expr)
        
        query = query.order_by(Issue.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        issues = [issue.to_dict() for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues', methods=['POST'])
@require_auth
def create_issue(current_user):
    """Create a new issue with AI verification"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        required_fields = ['title', 'category', 'latitude', 'longitude']
        missing = [f for f in required_fields if f not in data or not data[f]]
        
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
        
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid latitude/longitude'}), 400
        
        priority = data.get('priority', 'medium').lower()
        if priority not in ['low', 'medium', 'high', 'critical']:
            priority = 'medium'
        
        issue = Issue(
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            category=data['category'].strip(),
            latitude=latitude,
            longitude=longitude,
            address=data.get('address', '').strip(),
            priority=priority.upper(),
            created_by=current_user.id,
            status='SUBMITTED',
            ai_verification_status='PENDING'
        )
        
        image_urls = data.get('image_urls', [])
        if isinstance(image_urls, str):
            image_urls = [image_urls]
        elif not isinstance(image_urls, list):
            image_urls = []
        
        if 'image_url' in data and data['image_url']:
            if data['image_url'] not in image_urls:
                image_urls.append(data['image_url'])
        
        image_urls = [url for url in image_urls if url and url.strip()]
        issue.set_image_urls(image_urls)
        
        db.session.add(issue)
        db.session.commit()
        
        logger.info(f"Issue created: ID {issue.id} by {current_user.email}")
        
        # Create timeline event for issue creation
        timeline_service.create_event(
            issue_id=issue.id,
            event_type=EventType.ISSUE_CREATED,
            actor_type=ActorType.CITIZEN,
            actor_id=current_user.id,
            description=f"Issue reported: {issue.title}",
            metadata={
                'category': issue.category,
                'priority': issue.priority,
                'location': {
                    'latitude': issue.latitude,
                    'longitude': issue.longitude,
                    'address': issue.address
                }
            },
            image_urls=image_urls
        )
        
        # Trigger AI verification asynchronously if images provided
        if image_urls:
            try:
                # Create timeline event for AI verification start
                timeline_service.create_event(
                    issue_id=issue.id,
                    event_type=EventType.AI_VERIFICATION_STARTED,
                    actor_type=ActorType.AI,
                    actor_id=None,
                    description="AI verification started",
                    metadata={'image_count': len(image_urls)}
                )
                
                # Call AI service
                ai_result = asyncio.run(ai_client.verify_issue_initial(
                    issue_id=issue.id,
                    image_urls=image_urls,
                    category=issue.category,
                    location={
                        'latitude': issue.latitude,
                        'longitude': issue.longitude
                    },
                    description=issue.description
                ))
                
                if ai_result:
                    # Update issue with AI verification result
                    issue.ai_verification_status = ai_result.get('status', 'PENDING')
                    issue.ai_confidence_score = ai_result.get('confidence_score', 0.0)
                    
                    # Update issue status based on AI result
                    if ai_result.get('status') == 'REJECTED':
                        issue.status = 'REJECTED'
                    elif ai_result.get('status') == 'APPROVED':
                        issue.status = 'OPEN'
                        # Create timeline event for issue published
                        timeline_service.create_event(
                            issue_id=issue.id,
                            event_type=EventType.ISSUE_PUBLISHED,
                            actor_type=ActorType.SYSTEM,
                            actor_id=None,
                            description="Issue published after AI approval",
                            metadata={'confidence_score': issue.ai_confidence_score}
                        )
                    
                    db.session.commit()
                    
                    # Create timeline event for AI verification completion
                    timeline_service.create_event(
                        issue_id=issue.id,
                        event_type=EventType.AI_VERIFICATION_COMPLETED,
                        actor_type=ActorType.AI,
                        actor_id=None,
                        description=f"AI verification completed: {ai_result.get('status')}",
                        metadata={
                            'status': ai_result.get('status'),
                            'confidence_score': ai_result.get('confidence_score'),
                            'checks_performed': ai_result.get('checks_performed', {}),
                            'rejection_reasons': ai_result.get('rejection_reasons', [])
                        }
                    )
                    
                    logger.info(f"AI verification completed for issue #{issue.id}: {ai_result.get('status')}")
                else:
                    logger.warning(f"AI verification returned no result for issue #{issue.id}")
                    
            except Exception as e:
                logger.error(f"AI verification failed for issue #{issue.id}: {e}")
                # Continue without AI verification - issue remains in PENDING state
        else:
            # No images, auto-approve
            issue.status = 'OPEN'
            issue.ai_verification_status = 'SKIPPED'
            db.session.commit()
            logger.info(f"Issue #{issue.id} published without images (AI verification skipped)")
        
        return jsonify({
            'message': 'Issue created successfully',
            'issue': issue.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>', methods=['GET'])
def get_issue(issue_id):
    """Get a specific issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        return jsonify({'issue': issue.to_dict()})
    except Exception as e:
        logger.error(f"Error getting issue: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/upvote', methods=['POST'])
@require_auth
def upvote_issue(current_user, issue_id):
    """Upvote an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        issue.upvotes += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Issue upvoted',
            'upvotes': issue.upvotes
        })
    except Exception as e:
        logger.error(f"Error upvoting issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# AI Verification Routes
# ================================

@app.route('/api/v1/issues/<int:issue_id>/ai-verification', methods=['GET'])
@require_auth
def get_ai_verification(current_user, issue_id):
    """Get AI verification details for an issue"""
    try:
        # Check if issue exists
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Get verification status from AI service
        verification = asyncio.run(ai_client.get_verification_status(issue_id))
        
        if not verification:
            # Return basic info from database if AI service unavailable
            return jsonify({
                'issue_id': issue_id,
                'status': issue.ai_verification_status,
                'confidence_score': issue.ai_confidence_score,
                'message': 'Detailed verification data unavailable'
            })
        
        return jsonify(verification)
    except Exception as e:
        logger.error(f"Failed to get AI verification: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/issues/<int:issue_id>/timeline', methods=['GET'])
@require_auth
def get_issue_timeline(current_user, issue_id):
    """Get timeline events for an issue"""
    try:
        # Check if issue exists
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Get timeline events
        events = timeline_service.get_events(issue_id)
        
        return jsonify({
            'issue_id': issue_id,
            'events': events,
            'total_events': len(events)
        })
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/issues/<int:issue_id>/citizen-verify', methods=['POST'])
@require_auth
def submit_citizen_verification(current_user, issue_id):
    """Submit citizen verification for an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Only issue creator can verify
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Only issue creator can verify resolution'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Validate required fields
        if 'verified' not in data:
            return jsonify({'error': 'Missing required field: verified'}), 400
        
        if 'location' not in data or 'latitude' not in data['location'] or 'longitude' not in data['location']:
            return jsonify({'error': 'Missing required field: location'}), 400
        
        # Create citizen verification record
        import json as json_lib
        
        db.session.execute(
            db.text("""
                INSERT INTO citizen_verifications 
                (issue_id, user_id, verification_type, status, image_urls, notes, 
                 location_verified, latitude, longitude, created_at)
                VALUES 
                (:issue_id, :user_id, 'FINAL_VERIFICATION', :status, :image_urls, 
                 :notes, true, :latitude, :longitude, :created_at)
            """),
            {
                'issue_id': issue_id,
                'user_id': current_user.id,
                'status': 'VERIFIED' if data['verified'] else 'NOT_VERIFIED',
                'image_urls': json_lib.dumps(data.get('image_urls', [])),
                'notes': data.get('notes', ''),
                'latitude': data['location']['latitude'],
                'longitude': data['location']['longitude'],
                'created_at': datetime.utcnow()
            }
        )
        
        # Update issue status
        if data['verified']:
            issue.status = 'CLOSED'
            issue.citizen_verification_status = 'VERIFIED'
            issue.resolution_date = datetime.utcnow()
            
            # Create timeline event
            timeline_service.create_event(
                issue_id=issue_id,
                event_type=EventType.CITIZEN_VERIFICATION_COMPLETED,
                actor_type=ActorType.CITIZEN,
                actor_id=current_user.id,
                description="Citizen verified issue resolution",
                metadata={'verified': True},
                image_urls=data.get('image_urls', [])
            )
            
            # Create issue closed event
            timeline_service.create_event(
                issue_id=issue_id,
                event_type=EventType.ISSUE_CLOSED,
                actor_type=ActorType.SYSTEM,
                actor_id=None,
                description="Issue closed after citizen verification",
                metadata={'resolution_date': issue.resolution_date.isoformat()}
            )
        else:
            issue.status = 'DISPUTED'
            issue.citizen_verification_status = 'DISPUTED'
            
            # Create timeline event
            timeline_service.create_event(
                issue_id=issue_id,
                event_type=EventType.ISSUE_DISPUTED,
                actor_type=ActorType.CITIZEN,
                actor_id=current_user.id,
                description="Citizen disputed resolution",
                metadata={'verified': False, 'notes': data.get('notes', '')},
                image_urls=data.get('image_urls', [])
            )
        
        db.session.commit()
        
        logger.info(f"Citizen verification submitted for issue #{issue_id}: {data['verified']}")
        
        return jsonify({
            'message': 'Verification submitted successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to submit citizen verification: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/issues/<int:issue_id>/cross-verification', methods=['GET'])
@require_auth
def get_cross_verification(current_user, issue_id):
    """Get cross-verification results for an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if cross-verification exists in database
        result = db.session.execute(
            db.text("""
                SELECT id, status, confidence_score, checks_performed, created_at
                FROM ai_verifications 
                WHERE issue_id = :issue_id 
                AND verification_type = 'CROSS_VERIFICATION'
                ORDER BY created_at DESC 
                LIMIT 1
            """),
            {'issue_id': issue_id}
        )
        
        verification = result.fetchone()
        
        if not verification:
            return jsonify({'error': 'Cross-verification not found'}), 404
        
        return jsonify({
            'issue_id': issue_id,
            'verification_id': verification[0],
            'status': verification[1],
            'confidence_score': verification[2],
            'checks_performed': json.loads(verification[3]) if verification[3] else {},
            'created_at': verification[4].isoformat() if verification[4] else None,
            'citizen_images': issue.get_image_urls(),
            'government_images': issue.get_government_images()
        })
        
    except Exception as e:
        logger.error(f"Failed to get cross-verification: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/issues/<int:issue_id>/government-action', methods=['POST'])
@require_auth
def submit_government_action(current_user, issue_id):
    """Submit government action/resolution for an issue (Admin only)"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # TODO: Add admin role check here
        # For now, any authenticated user can submit (for testing)
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        action_type = data.get('action_type', 'WORK_COMPLETED')
        government_images = data.get('image_urls', [])
        notes = data.get('notes', '')
        
        # Update issue with government data
        issue.set_government_images(government_images)
        issue.government_notes = notes
        issue.status = 'RESOLVED'
        
        # Create timeline event
        timeline_service.create_event(
            issue_id=issue_id,
            event_type=EventType.WORK_COMPLETED,
            actor_type=ActorType.GOVERNMENT,
            actor_id=current_user.id,
            description=f"Government marked issue as resolved: {notes}",
            metadata={'action_type': action_type},
            image_urls=government_images
        )
        
        db.session.commit()
        
        # Trigger cross-verification if both citizen and government images exist
        if issue.get_image_urls() and government_images:
            try:
                # Create timeline event for cross-verification start
                timeline_service.create_event(
                    issue_id=issue_id,
                    event_type=EventType.CROSS_VERIFICATION_STARTED,
                    actor_type=ActorType.AI,
                    actor_id=None,
                    description="AI cross-verification started"
                )
                
                # Call AI service for cross-verification
                cross_result = asyncio.run(ai_client.verify_cross_check(
                    issue_id=issue_id,
                    citizen_images=issue.get_image_urls(),
                    government_images=government_images,
                    location={
                        'latitude': issue.latitude,
                        'longitude': issue.longitude
                    },
                    issue_category=issue.category
                ))
                
                if cross_result:
                    # Create timeline event for cross-verification completion
                    timeline_service.create_event(
                        issue_id=issue_id,
                        event_type=EventType.CROSS_VERIFICATION_COMPLETED,
                        actor_type=ActorType.AI,
                        actor_id=None,
                        description=f"Cross-verification completed: {cross_result.get('status')}",
                        metadata={
                            'status': cross_result.get('status'),
                            'confidence_score': cross_result.get('confidence_score'),
                            'checks_performed': cross_result.get('checks_performed', {})
                        }
                    )
                    
                    # Request citizen verification
                    timeline_service.create_event(
                        issue_id=issue_id,
                        event_type=EventType.CITIZEN_VERIFICATION_REQUESTED,
                        actor_type=ActorType.SYSTEM,
                        actor_id=None,
                        description="Citizen verification requested"
                    )
                    
                    logger.info(f"Cross-verification completed for issue #{issue_id}")
                    
            except Exception as e:
                logger.error(f"Cross-verification failed for issue #{issue_id}: {e}")
        
        return jsonify({
            'message': 'Government action submitted successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to submit government action: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/ai-service/health', methods=['GET'])
def check_ai_service_health():
    """Check AI service health"""
    try:
        is_healthy = asyncio.run(ai_client.health_check())
        
        return jsonify({
            'ai_service_enabled': ai_client.enabled,
            'ai_service_healthy': is_healthy,
            'ai_service_url': ai_client.base_url
        })
    except Exception as e:
        logger.error(f"Failed to check AI service health: {e}")
        return jsonify({
            'ai_service_enabled': ai_client.enabled,
            'ai_service_healthy': False,
            'error': str(e)
        }), 500

# ================================
# User Routes
# ================================

@app.route('/api/v1/users/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current user profile - Performance Optimized"""
    # Return cached user data to avoid additional database queries
    return jsonify({'user': current_user.to_dict()})

@app.route('/api/v1/users/me', methods=['PUT'])
@require_auth
def update_current_user(current_user):
    """Update current user profile"""
    try:
        data = request.get_json()
        
        if 'display_name' in data:
            current_user.display_name = data['display_name'].strip()
        if 'bio' in data:
            current_user.bio = data['bio'].strip()
        if 'phone' in data:
            current_user.phone = data['phone'].strip()
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated',
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/me/settings', methods=['PUT'])
@require_auth
def update_user_settings(current_user):
    """Update user settings"""
    try:
        data = request.get_json()
        
        # Preferences
        if 'notifications_enabled' in data:
            current_user.notifications_enabled = bool(data['notifications_enabled'])
        if 'dark_mode' in data:
            current_user.dark_mode = bool(data['dark_mode'])
        if 'anonymous_reporting' in data:
            current_user.anonymous_reporting = bool(data['anonymous_reporting'])
        if 'satellite_view' in data:
            current_user.satellite_view = bool(data['satellite_view'])
        if 'save_to_gallery' in data:
            current_user.save_to_gallery = bool(data['save_to_gallery'])
        
        # Appearance settings
        if 'theme_color' in data:
            valid_colors = ['blue', 'green', 'purple', 'orange', 'red', 'pink']
            if data['theme_color'] in valid_colors:
                current_user.theme_color = data['theme_color']
        if 'font_size' in data:
            valid_sizes = ['small', 'medium', 'large', 'extra_large']
            if data['font_size'] in valid_sizes:
                current_user.font_size = data['font_size']
        if 'language' in data:
            valid_languages = ['en', 'ta', 'hi', 'es', 'fr']
            if data['language'] in valid_languages:
                current_user.language = data['language']
        
        # Notification settings
        if 'issue_updates_notifications' in data:
            current_user.issue_updates_notifications = bool(data['issue_updates_notifications'])
        if 'community_activity_notifications' in data:
            current_user.community_activity_notifications = bool(data['community_activity_notifications'])
        if 'system_alerts_notifications' in data:
            current_user.system_alerts_notifications = bool(data['system_alerts_notifications'])
        
        # Media settings
        if 'photo_quality' in data:
            valid_qualities = ['low', 'medium', 'high', 'original']
            if data['photo_quality'] in valid_qualities:
                current_user.photo_quality = data['photo_quality']
        if 'video_quality' in data:
            valid_qualities = ['low', 'medium', 'high', 'original']
            if data['video_quality'] in valid_qualities:
                current_user.video_quality = data['video_quality']
        if 'auto_upload' in data:
            current_user.auto_upload = bool(data['auto_upload'])
        
        # Storage settings
        if 'cache_auto_clear' in data:
            current_user.cache_auto_clear = bool(data['cache_auto_clear'])
        if 'backup_sync' in data:
            current_user.backup_sync = bool(data['backup_sync'])
        
        # Privacy settings
        if 'location_services' in data:
            current_user.location_services = bool(data['location_services'])
        if 'data_collection' in data:
            current_user.data_collection = bool(data['data_collection'])
        
        # Accessibility settings
        if 'high_contrast' in data:
            current_user.high_contrast = bool(data['high_contrast'])
        if 'large_text' in data:
            current_user.large_text = bool(data['large_text'])
        if 'voice_over' in data:
            current_user.voice_over = bool(data['voice_over'])
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Settings updated successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Authentication Endpoints
# ================================

@app.route('/api/v1/auth/google', methods=['POST'])
def authenticate_google():
    """Authenticate user with Google OAuth"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Verify the token with Supabase
        token_data = verify_supabase_token(id_token)
        if not token_data:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Sync user to database
        user = sync_user_to_database(token_data)
        if not user:
            return jsonify({'error': 'Failed to sync user'}), 500
        
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict(),
            'token': id_token
        })
    except Exception as e:
        logger.error(f"Error authenticating with Google: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/v1/auth/check-user', methods=['POST'])
def check_user_exists():
    """Check if user exists in database without creating them - Performance Optimized"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        logger.info("Check user request received")
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Verify the token with Supabase
        logger.info("Verifying Supabase token...")
        try:
            token_data = verify_supabase_token(id_token)
            if not token_data:
                logger.error("Token verification failed")
                return jsonify({'error': 'Invalid token'}), 401
            logger.info(f"Token verified for email: {token_data.get('email')}")
        except Exception as token_error:
            logger.error(f"Token verification error: {token_error}")
            return jsonify({'error': 'Invalid token'}), 401
        
        email = token_data.get('email')
        if not email:
            return jsonify({'error': 'Email not found in token'}), 400
        
        # Query only essential fields to avoid missing column errors
        # Retry logic for transient connection errors
        logger.info(f"Checking if user exists: {email}")
        max_retries = 3
        retry_count = 0
        result = None
        
        while retry_count < max_retries:
            try:
                # Use raw SQL to query only existing columns
                result = db.session.execute(
                    db.text("""
                        SELECT id, email, name, display_name, photo_url, 
                               firebase_uid, password_hash, onboarding_completed
                        FROM users 
                        WHERE email = :email
                        LIMIT 1
                    """),
                    {'email': email}
                ).fetchone()
                
                # If we got here, query succeeded
                break
                
            except Exception as db_error:
                retry_count += 1
                error_msg = str(db_error)
                
                # Check if it's a connection error that we should retry
                if 'SSL connection' in error_msg or 'connection' in error_msg.lower():
                    logger.warning(f"Database connection error (attempt {retry_count}/{max_retries}): {db_error}")
                    
                    if retry_count < max_retries:
                        # Close the current session and create a new one
                        try:
                            db.session.rollback()
                            db.session.remove()
                        except:
                            pass
                        
                        # Wait a bit before retrying
                        import time
                        time.sleep(0.5 * retry_count)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Database query failed after {max_retries} attempts")
                        logger.error(f"Error type: {type(db_error).__name__}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return jsonify({'error': 'Database connection error. Please try again.'}), 503
                else:
                    # Not a connection error, don't retry
                    logger.error(f"Database query error: {db_error}")
                    logger.error(f"Error type: {type(db_error).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return jsonify({'error': 'Database error'}), 500
        
        if result:
            # User exists - return minimal data
            logger.info(f"User found: {email}")
            return jsonify({
                'exists': True,
                'has_password': bool(result[6]),  # password_hash
                'user': {
                    'id': result[0],
                    'email': result[1],
                    'name': result[2],
                    'display_name': result[3],
                    'photo_url': result[4],
                    'firebase_uid': result[5],
                    'onboarding_completed': result[7] if result[7] is not None else False
                },
                'token': id_token
            })
        else:
            # User doesn't exist
            logger.info(f"User not found: {email}")
            return jsonify({
                'exists': False,
                'has_password': False,
                'email': email,
                'name': token_data.get('name', ''),
                'photo_url': token_data.get('picture', ''),
                'firebase_uid': token_data.get('sub', ''),
                'token': id_token
            })
            
    except Exception as e:
        logger.error(f"Error checking user: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to check user'}), 500

@app.route('/api/v1/auth/create-user', methods=['POST'])
def create_user_with_password():
    """Create new user with password and language"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        password = data.get('password')
        language = data.get('language', 'en')
        
        logger.info(f"Create user request received")
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Verify the token with Supabase
        logger.info(f"Verifying Supabase token...")
        try:
            token_data = verify_supabase_token(id_token)
            if not token_data:
                logger.error("Token verification failed")
                return jsonify({'error': 'Invalid token'}), 401
            logger.info(f"Token verified successfully for email: {token_data.get('email')}")
        except Exception as token_error:
            logger.error(f"Token verification error: {token_error}")
            return jsonify({'error': 'Token verification failed'}), 401
        
        email = token_data.get('email')
        if not email:
            return jsonify({'error': 'Email not found in token'}), 400
        
        # Check if user already exists
        logger.info(f"Checking if user exists: {email}")
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.info(f"User already exists: {email}")
                return jsonify({'error': 'User already exists'}), 400
            logger.info(f"User does not exist, creating new user")
        except Exception as db_error:
            logger.error(f"Database query error when checking user: {db_error}")
            logger.error(f"Error type: {type(db_error).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Database error'}), 500
        
        # Create new user
        try:
            logger.info(f"Creating new user object...")
            new_user = User(
                firebase_uid=token_data.get('sub', ''),
                email=email,
                name=token_data.get('name', email.split('@')[0]),
                display_name=token_data.get('name', email.split('@')[0]),
                photo_url=token_data.get('picture', ''),
                password_hash=hash_password(password),
                language=language,
                onboarding_completed=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            logger.info(f"User object created, adding to session...")
            
            db.session.add(new_user)
            logger.info(f"User added to session, committing...")
            
            db.session.commit()
            logger.info(f"User committed successfully: {new_user.email} (ID: {new_user.id})")
            
            # Generate JWT token
            token_payload = {
                'user_id': new_user.id,
                'email': new_user.email,
                'firebase_uid': new_user.firebase_uid,
                'exp': datetime.utcnow() + timedelta(days=30)
            }
            
            jwt_token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
            
            # Handle both string and bytes return from jwt.encode
            if isinstance(jwt_token, bytes):
                jwt_token = jwt_token.decode('utf-8')
            
            return jsonify({
                'message': 'User created successfully',
                'user': new_user.to_dict(),
                'token': jwt_token
            })
        except Exception as create_error:
            logger.error(f"Error creating user: {create_error}")
            logger.error(f"Error type: {type(create_error).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
            return jsonify({'error': f'Failed to create user: {str(create_error)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in create_user: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/v1/auth/test', methods=['GET'])
@require_auth
def test_auth(current_user):
    """Test authentication endpoint"""
    return jsonify({
        'message': 'Authentication successful',
        'user': current_user.to_dict(),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/debug/auth', methods=['GET'])
@require_auth
def debug_auth(current_user):
    """Debug authentication endpoint"""
    return jsonify({
        'message': 'Debug authentication',
        'user': current_user.to_dict(),
        'token_present': bool(request.headers.get('Authorization')),
        'timestamp': datetime.utcnow().isoformat()
    })

# ================================
# Onboarding Endpoints
# ================================

@app.route('/api/v1/onboarding/password', methods=['POST'])
@require_auth
def set_onboarding_password(current_user):
    """Set password during onboarding"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        logger.info(f"Setting password for user: {current_user.email} (ID: {current_user.id})")
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check current password state
        logger.info(f"Current password_hash state: {bool(current_user.password_hash)}")
        
        # Hash and store password (for local auth if needed)
        hashed_password = hash_password(password)
        logger.info(f"Generated password hash length: {len(hashed_password)}")
        
        current_user.password_hash = hashed_password
        current_user.onboarding_completed = True  # Mark onboarding as completed when password is set
        current_user.updated_at = datetime.utcnow()
        
        # Commit the transaction
        db.session.commit()
        logger.info(f"Password committed to database for user: {current_user.email}")
        
        # Verify the password was saved by re-querying the user
        updated_user = User.query.get(current_user.id)
        logger.info(f"Verification - User password_hash exists: {bool(updated_user.password_hash)}")
        logger.info(f"Verification - Onboarding completed: {updated_user.onboarding_completed}")
        
        return jsonify({
            'message': 'Password set successfully',
            'user': updated_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error setting onboarding password: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/auth/verify-password', methods=['POST'])
@require_auth
def verify_user_password(current_user):
    """Verify user password for login"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Check if user has password set
        if not current_user.password_hash:
            return jsonify({'error': 'Password not set for this account'}), 400
        
        # Verify password
        if not verify_password(password, current_user.password_hash):
            return jsonify({'error': 'Invalid password'}), 401
        
        return jsonify({
            'message': 'Password verified successfully',
            'verified': True,
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/auth/login-with-password', methods=['POST'])
def login_with_password():
    """Login user by verifying password against Neon database"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        logger.info(f"Login attempt for email: {email}")
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
            
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Find user by email in Neon database with retry logic
        max_retries = 3
        retry_count = 0
        user = None
        
        while retry_count < max_retries:
            try:
                user = User.query.filter_by(email=email).first()
                logger.info(f"User query result: {user is not None}")
                break  # Success, exit retry loop
                
            except Exception as db_error:
                retry_count += 1
                error_msg = str(db_error)
                
                if 'SSL connection' in error_msg or 'connection' in error_msg.lower():
                    logger.warning(f"Database connection error (attempt {retry_count}/{max_retries}): {db_error}")
                    
                    if retry_count < max_retries:
                        try:
                            db.session.rollback()
                            db.session.remove()
                        except:
                            pass
                        
                        import time
                        time.sleep(0.5 * retry_count)
                        continue
                    else:
                        logger.error(f"Database query failed after {max_retries} attempts")
                        return jsonify({'error': 'Database connection error. Please try again.'}), 503
                else:
                    logger.error(f"Database query error: {db_error}")
                    return jsonify({'error': 'Database error'}), 500
        
        if not user:
            logger.info(f"User not found for email: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has password set
        if not user.password_hash:
            logger.info(f"User {email} has no password set")
            return jsonify({'error': 'Password not set for this account'}), 400
        
        # Verify password against Neon database
        try:
            password_valid = verify_password(password, user.password_hash)
            logger.info(f"Password verification result: {password_valid}")
        except Exception as verify_error:
            logger.error(f"Password verification error: {verify_error}")
            return jsonify({'error': 'Password verification failed'}), 500
        
        if not password_valid:
            logger.info(f"Invalid password for user: {email}")
            return jsonify({'error': 'Invalid password'}), 401
        
        # Generate JWT token for the user
        try:
            token_payload = {
                'user_id': user.id,
                'email': user.email,
                'firebase_uid': user.firebase_uid,
                'exp': datetime.utcnow() + timedelta(days=30)
            }
            
            token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
            
            # Handle both string and bytes return from jwt.encode
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            logger.info(f"User {user.email} logged in successfully with password")
        except Exception as jwt_error:
            logger.error(f"JWT token generation error: {jwt_error}")
            return jsonify({'error': 'Token generation failed'}), 500
        
        return jsonify({
            'message': 'Login successful',
            'verified': True,
            'user': user.to_dict(),
            'token': token
        })
        
    except Exception as e:
        logger.error(f"Error in password login: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/onboarding/language', methods=['POST'])
@require_auth
def set_onboarding_language(current_user):
    """Set language during onboarding"""
    try:
        data = request.get_json()
        language = data.get('language')
        
        if not language:
            return jsonify({'error': 'Language is required'}), 400
        
        current_user.language = language
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Language set successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error setting onboarding language: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/onboarding/complete', methods=['POST'])
@require_auth
def complete_onboarding(current_user):
    """Complete onboarding process"""
    try:
        current_user.onboarding_completed = True
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Onboarding completed successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# User Profile Endpoints
# ================================

@app.route('/api/v1/users/me/password', methods=['PUT'])
@require_auth
def change_password(current_user):
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password are required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        
        # Verify current password
        if current_user.password_hash:
            if not verify_password(current_password, current_user.password_hash):
                return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Set new password
        current_user.password_hash = hash_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully',
            'instructions': 'Please use your new password for future logins',
            'supabase_method': 'Password updated in local database'
        })
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/me/delete', methods=['DELETE'])
@require_auth
def delete_user_account(current_user):
    """Delete user account and all associated data"""
    try:
        user_id = current_user.id
        user_email = current_user.email
        
        # Delete user's issues and comments (cascade should handle this, but let's be explicit)
        Issue.query.filter_by(created_by=user_id).delete()
        Comment.query.filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        logger.info(f"User account deleted: {user_email} (ID: {user_id})")
        
        return jsonify({
            'message': 'Account deleted successfully',
            'note': 'All your data has been permanently removed'
        })
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete account. Please try again.'}), 500

@app.route('/api/v1/users/<int:user_id>/issues', methods=['GET'])
def get_user_issues(user_id):
    """Get issues created by a specific user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query issues by user
        query = Issue.query.filter_by(created_by=user_id).order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        issues = [{
            **issue.to_dict(),
            'creator_name': issue.creator.name if issue.creator else 'Unknown'
        } for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        logger.error(f"Error getting user issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()})
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Issue CRUD Endpoints
# ================================

@app.route('/api/v1/issues/<int:issue_id>', methods=['PUT'])
@require_auth
def update_issue(current_user, issue_id):
    """Update an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user owns the issue
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            issue.title = data['title']
        if 'description' in data:
            issue.description = data['description']
        if 'category' in data:
            issue.category = data['category']
        if 'priority' in data:
            issue.priority = data['priority']
        if 'address' in data:
            issue.address = data['address']
        if 'image_urls' in data:
            issue.image_urls = json.dumps(data['image_urls'])
        
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Issue updated successfully',
            'issue': issue.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>', methods=['DELETE'])
@require_auth
def delete_issue(current_user, issue_id):
    """Delete an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user owns the issue
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(issue)
        db.session.commit()
        
        return jsonify({'message': 'Issue deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/status', methods=['PUT'])
@require_auth
def update_issue_status(current_user, issue_id):
    """Update issue status"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        issue.status = status
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating issue status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/nearby', methods=['GET'])
def get_nearby_issues():
    """Get issues near a location"""
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 5.0, type=float)  # km
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if latitude is None or longitude is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Simple distance calculation (Haversine formula would be more accurate)
        # For now, use a bounding box
        lat_range = radius / 111.0  # 1 degree latitude ≈ 111 km
        lon_range = radius / (111.0 * abs(latitude / 90.0))  # Adjust for latitude
        
        query = Issue.query.filter(
            Issue.latitude.between(latitude - lat_range, latitude + lat_range),
            Issue.longitude.between(longitude - lon_range, longitude + lon_range)
        ).order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        issues = [{
            **issue.to_dict(),
            'creator_name': issue.creator.name if issue.creator else 'Unknown'
        } for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        logger.error(f"Error getting nearby issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Upvote Endpoints
# ================================

@app.route('/api/v1/issues/<int:issue_id>/upvote', methods=['DELETE'])
@require_auth
def remove_upvote(current_user, issue_id):
    """Remove upvote from an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Decrement upvotes (in a real app, track individual upvotes in a separate table)
        if issue.upvotes > 0:
            issue.upvotes -= 1
            issue.updated_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'message': 'Upvote removed',
            'upvotes': issue.upvotes
        })
    except Exception as e:
        logger.error(f"Error removing upvote: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/upvotes', methods=['GET'])
def get_issue_upvotes(issue_id):
    """Get upvote information for an issue"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # In a real app, check if current user has upvoted
        # For now, return basic info
        return jsonify({
            'upvotes': issue.upvotes,
            'user_upvoted': False  # Would check against upvotes table
        })
    except Exception as e:
        logger.error(f"Error getting upvotes: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Comment Endpoints
# ================================

@app.route('/api/v1/issues/<int:issue_id>/comments', methods=['GET'])
def get_issue_comments(issue_id):
    """Get comments for an issue"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Check if issue exists
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Query comments
        query = Comment.query.filter_by(issue_id=issue_id).order_by(Comment.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        comments = [{
            **comment.to_dict(),
            'user_name': comment.user.name if comment.user else 'Unknown',
            'user_photo': comment.user.photo_url if comment.user else None,
            'user_display_name': comment.user.display_name if comment.user else None
        } for comment in pagination.items]
        
        return jsonify({
            'comments': comments,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/comments', methods=['POST'])
@require_auth
def create_comment(current_user, issue_id):
    """Create a comment on an issue"""
    try:
        # Check if issue exists
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if len(content) > 1000:
            return jsonify({'error': 'Content must be less than 1000 characters'}), 400
        
        # Create comment
        comment = Comment(
            content=content,
            issue_id=issue_id,
            user_id=current_user.id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': {
                **comment.to_dict(),
                'user_name': current_user.name,
                'user_photo': current_user.photo_url,
                'user_display_name': current_user.display_name
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/comments/<int:comment_id>', methods=['PUT'])
@require_auth
def update_comment(current_user, comment_id):
    """Update a comment"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check if user owns the comment
        if comment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if len(content) > 1000:
            return jsonify({'error': 'Content must be less than 1000 characters'}), 400
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': {
                **comment.to_dict(),
                'user_name': current_user.name,
                'user_photo': current_user.photo_url,
                'user_display_name': current_user.display_name
            }
        })
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/comments/<int:comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(current_user, comment_id):
    """Delete a comment"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check if user owns the comment
        if comment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': 'Comment deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Upload Endpoints
# ================================

@app.route('/api/v1/upload/multiple', methods=['POST'])
@require_auth
def upload_multiple_files(current_user):
    """Upload multiple files to Supabase Storage"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                if file.filename == '':
                    errors.append('Empty filename')
                    continue
                
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Upload to Supabase Storage
                file_data = file.read()
                storage_service.upload_file(unique_filename, file_data, file.content_type)
                
                file_url = storage_service.get_public_url(unique_filename)
                
                uploaded_files.append({
                    'file_url': file_url,
                    'file_name': filename,
                    'file_size': len(file_data)
                })
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {e}")
                errors.append(f"Failed to upload {file.filename}")
        
        return jsonify({
            'message': f'Uploaded {len(uploaded_files)} files',
            'uploaded_files': uploaded_files,
            'errors': errors
        })
    except Exception as e:
        logger.error(f"Error uploading multiple files: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/upload/video', methods=['POST'])
@require_auth
def upload_video(current_user):
    """Upload video to Supabase Storage"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate video file
        allowed_video_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']
        if file.content_type not in allowed_video_types:
            return jsonify({'error': 'Invalid video format. Allowed: MP4, MOV, AVI, WEBM'}), 400
        
        filename = secure_filename(file.filename)
        unique_filename = f"videos/{uuid.uuid4()}_{filename}"
        
        # Upload to Supabase Storage
        file_data = file.read()
        storage_service.upload_file(unique_filename, file_data, file.content_type)
        
        file_url = storage_service.get_public_url(unique_filename)
        
        return jsonify({
            'message': 'Video uploaded successfully',
            'file_url': file_url,
            'file_name': filename,
            'file_size': len(file_data),
            'file_type': 'video',
            'content_type': file.content_type,
            'file_extension': filename.rsplit('.', 1)[1].lower() if '.' in filename else '',
            'upload_timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id
        })
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Utility Endpoints
# ================================

@app.route('/api/v1/status-options', methods=['GET'])
def get_status_options():
    """Get available status options"""
    return jsonify({
        'status_options': [
            {'value': 'open', 'label': 'Open', 'description': 'Issue is reported and awaiting action'},
            {'value': 'in_progress', 'label': 'In Progress', 'description': 'Issue is being worked on'},
            {'value': 'resolved', 'label': 'Resolved', 'description': 'Issue has been fixed'},
            {'value': 'closed', 'label': 'Closed', 'description': 'Issue is closed'}
        ]
    })

@app.route('/api/v1/priority-options', methods=['GET'])
def get_priority_options():
    """Get available priority options"""
    return jsonify({
        'priority_options': [
            {'value': 'low', 'label': 'Low', 'description': 'Minor issue, can wait'},
            {'value': 'medium', 'label': 'Medium', 'description': 'Moderate issue, should be addressed'},
            {'value': 'high', 'label': 'High', 'description': 'Important issue, needs attention'},
            {'value': 'urgent', 'label': 'Urgent', 'description': 'Critical issue, immediate action required'}
        ]
    })

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    try:
        logger.info("Stats endpoint called")
        
        try:
            total_issues = Issue.query.count()
            logger.info(f"Total issues: {total_issues}")
        except Exception as issue_error:
            logger.error(f"Error counting issues: {issue_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Database error: Issue table'}), 500
        
        try:
            total_users = User.query.count()
            logger.info(f"Total users: {total_users}")
        except Exception as user_error:
            logger.error(f"Error counting users: {user_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Database error: User table'}), 500
        
        # Issues by status
        issues_by_status = {}
        for status in ['open', 'in_progress', 'resolved', 'closed']:
            count = Issue.query.filter_by(status=status).count()
            issues_by_status[status] = count
        
        # Issues by category
        issues_by_category = {}
        categories = ['roads', 'water', 'electricity', 'waste', 'public_safety', 'other']
        for category in categories:
            count = Issue.query.filter_by(category=category).count()
            issues_by_category[category] = count
        
        return jsonify({
            'total_issues': total_issues,
            'total_users': total_users,
            'issues_by_status': issues_by_status,
            'issues_by_category': issues_by_category
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Run Application
# ================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# ================================
# Automated Escalation & Jobs
# ================================

@app.route('/api/v1/jobs/check-escalations', methods=['POST'])
def check_escalations():
    """Check for issues that need escalation (Cron Job)"""
    try:
        # Check for authorization (e.g., specific API key for jobs)
        api_key = request.headers.get('X-Job-Key')
        # In production, verify this key against environment variable
        
        logger.info("Starting escalation check job...")
        
        # specific period: 30 days ago
        escalation_threshold = datetime.utcnow() - timedelta(days=30)
        
        # Find issues that are OPEN or IN_PROGRESS and older than threshold
        # And haven't been escalated yet
        issues_to_escalate = Issue.query.filter(
            Issue.status.in_(['OPEN', 'IN_PROGRESS']),
            Issue.created_at <= escalation_threshold,
            Issue.escalation_status == 'NONE'
        ).all()
        
        escalated_count = 0
        
        for issue in issues_to_escalate:
            try:
                logger.info(f"Escalating issue #{issue.id} (Created: {issue.created_at})")
                
                # Update issue status
                issue.escalation_status = 'ESCALATED'
                issue.escalation_date = datetime.utcnow()
                issue.priority = 'CRITICAL' # Bump priority
                
                # Create timeline event
                timeline_service.create_event(
                    issue_id=issue.id,
                    event_type=EventType.ESCALATION_TRIGGERED,
                    actor_type=ActorType.SYSTEM,
                    actor_id=None,
                    description="Issue automatically escalated due to delay (>30 days)",
                    metadata={
                        'reason': 'delay_exceeded',
                        'days_open': (datetime.utcnow() - issue.created_at).days
                    }
                )
                
                escalated_count += 1
            except Exception as e:
                logger.error(f"Failed to escalate issue #{issue.id}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'message': 'Escalation check completed',
            'escalated_count': escalated_count
        })
        
    except Exception as e:
        logger.error(f"Escalation job failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# AI Assistant Proxy
# ================================

@app.route('/api/v1/assistant/chat', methods=['POST'])
@require_auth
def assistant_chat(current_user):
    """Chat with AI Assistant"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message required'}), 400
        
        user_message = data['message']
        context = data.get('context', {}) # issue_id, screen, etc.
        
        # Prepare payload for AI Service
        payload = {
            'user_id': current_user.id,
            'message': user_message,
            'user_name': current_user.name,
            'context': context
        }
        
        # Call AI Service (assuming it's running locally or accessible)
        # In a real microservices setup, use the service URL
        ai_service_url = os.environ.get('AI_SERVICE_URL', 'http://localhost:8001')
        
        import requests
        try:
            # We'll implement this endpoint in the AI service next
            response = requests.post(
                f"{ai_service_url}/api/v1/assistant/chat",
                json=payload,
                headers={'X-API-Key': os.environ.get('AI_SERVICE_API_KEY', 'dev-key')},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                # Fallback if AI service error
                logger.error(f"AI Service error: {response.text}")
                return jsonify({
                    'response': "I'm having trouble connecting to my brain right now. Please try again later.",
                    'suggestions': []
                })
                
        except Exception as conn_err:
            logger.error(f"Connection to AI Service failed: {conn_err}")
            # Fallback response
            return jsonify({
                'response': "I can help you with reporting issues, tracking status, or explaining the process. What would you like to know?",
                'suggestions': ["How to report?", "Check my status", "Escalation process"]
            })

    except Exception as e:
        logger.error(f"Assistant chat error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

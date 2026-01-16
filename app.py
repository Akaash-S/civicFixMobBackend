"""
CivicFix Backend - Neon PostgreSQL + Supabase Storage
Production-ready Flask application with modern cloud services
"""

import os
import logging
from datetime import datetime
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
            
            # Upload file to Supabase Storage
            result = self.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            # Generate public URL
            file_url = self.storage.from_(self.bucket_name).get_public_url(unique_filename)
            
            logger.info(f"File uploaded to Supabase Storage: {unique_filename}")
            return file_url, None
            
        except Exception as e:
            logger.error(f"Supabase Storage upload failed: {e}")
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
    notifications_enabled = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)
    anonymous_reporting = db.Column(db.Boolean, default=False)
    satellite_view = db.Column(db.Boolean, default=False)
    save_to_gallery = db.Column(db.Boolean, default=True)
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
            'notifications_enabled': self.notifications_enabled,
            'dark_mode': self.dark_mode,
            'anonymous_reporting': self.anonymous_reporting,
            'satellite_view': self.satellite_view,
            'save_to_gallery': self.save_to_gallery,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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
    """Sync Supabase user data to local database"""
    try:
        if not user_data or not user_data.get('uid'):
            return None
        
        uid = user_data['uid']
        user = User.query.filter_by(firebase_uid=uid).first()
        
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
            db.session.commit()
            logger.info(f"Created new user: {user.email}")
        
        return user
    except Exception as e:
        logger.error(f"Failed to sync user: {e}")
        db.session.rollback()
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
            return jsonify({'error': 'File upload service not available'}), 503
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        if len(files) > 8:
            return jsonify({'error': 'Maximum 8 files allowed'}), 400
        
        uploaded_files = []
        errors = []
        total_size = 0
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_extension not in allowed_extensions:
                    errors.append(f"{file.filename}: Invalid file type")
                    continue
                
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                
                max_size = 100 * 1024 * 1024 if file_extension in video_extensions else 15 * 1024 * 1024
                
                if file_size > max_size:
                    errors.append(f"{file.filename}: File too large")
                    continue
                
                total_size += file_size
                
                if total_size > 200 * 1024 * 1024:
                    errors.append(f"{file.filename}: Total size exceeds 200MB")
                    continue
                
                file_data = file.read()
                content_type = f'video/{file_extension}' if file_extension in video_extensions else file.content_type or f'image/{file_extension}'
                
                file_url, error = storage_service.upload_file(file_data, f"issue_media_{file.filename}", content_type)
                
                if error:
                    errors.append(f"{file.filename}: Upload failed - {error}")
                else:
                    uploaded_files.append({
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_size': file_size,
                        'file_type': 'video' if file_extension in video_extensions else 'image'
                    })
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        media_urls = [f['file_url'] for f in uploaded_files]
        
        logger.info(f"Issue media uploaded by {current_user.email}: {len(uploaded_files)} files")
        
        return jsonify({
            'message': f'{len(uploaded_files)} files uploaded successfully',
            'media_urls': media_urls,
            'uploaded_files': uploaded_files,
            'errors': errors,
            'total_size': total_size,
            'summary': {
                'images': len([f for f in uploaded_files if f['file_type'] == 'image']),
                'videos': len([f for f in uploaded_files if f['file_type'] == 'video']),
                'total_files': len(uploaded_files)
            }
        }), 201 if uploaded_files else 400
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
    """Create a new issue"""
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
            created_by=current_user.id
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
# User Routes
# ================================

@app.route('/api/v1/users/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current user profile"""
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
        
        if 'notifications_enabled' in data:
            current_user.notifications_enabled = bool(data['notifications_enabled'])
        if 'dark_mode' in data:
            current_user.dark_mode = bool(data['dark_mode'])
        if 'anonymous_reporting' in data:
            current_user.anonymous_reporting = bool(data['anonymous_reporting'])
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Settings updated',
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
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Hash and store password (for local auth if needed)
        current_user.password_hash = hash_password(password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Password set successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error setting onboarding password: {e}")
        db.session.rollback()
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
        total_issues = Issue.query.count()
        total_users = User.query.count()
        
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
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Run Application
# ================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

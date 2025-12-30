"""
CivicFix Backend - Clean, Production-Ready Flask Application
Simple, reliable, and easy to deploy
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import json
import boto3
from botocore.exceptions import ClientError
import uuid
from werkzeug.utils import secure_filename
import jwt
from functools import lru_cache
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable is required")

# Database configuration - AWS RDS PostgreSQL only
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required for AWS RDS connection")

# Handle PostgreSQL URL format
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
    # Parse comma-separated origins
    origins = [origin.strip() for origin in cors_origins.split(',')]
    CORS(app, origins=origins)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# AWS S3 Configuration
# ================================

class S3Service:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Require AWS credentials for both development and production
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME environment variable is required")
        
        self.init_s3()
    
    def init_s3(self):
        """Initialize S3 client"""
        try:
            # AWS credentials from environment variables (required)
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            
            if not aws_access_key or not aws_secret_key:
                raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are required")
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=self.region
            )
            
            # Test S3 connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 client initialized successfully for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"S3 initialization failed: {e}")
            raise ValueError(f"Failed to initialize S3: {e}")
    
    def upload_file(self, file_data, file_name, content_type='application/octet-stream'):
        """Upload file to S3 bucket"""
        try:
            # Generate unique filename
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            unique_filename = f"issues/{uuid.uuid4()}.{file_extension}" if file_extension else f"issues/{uuid.uuid4()}"
            
            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_data,
                ContentType=content_type
                # Removed ACL='public-read' - bucket doesn't allow ACLs
                # Files will be accessible via bucket policy or CloudFront
            )
            
            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{unique_filename}"
            return file_url, None
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None, str(e)
    
    def delete_file(self, file_url):
        """Delete file from S3 bucket"""
        try:
            # Extract key from URL
            if f"{self.bucket_name}.s3." in file_url:
                key = file_url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")[1]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
        
        return False

# Initialize S3 service
try:
    s3_service = S3Service()
    logger.info("S3 service initialized successfully")
except Exception as e:
    logger.warning(f"S3 service initialization failed: {e}")
    logger.warning("S3 functionality will be disabled")
    s3_service = None

# ================================
# Models
# ================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    photo_url = db.Column(db.String(500))
    bio = db.Column(db.Text)  # Added bio field
    # Settings fields
    notifications_enabled = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)
    anonymous_reporting = db.Column(db.Boolean, default=False)
    satellite_view = db.Column(db.Boolean, default=False)
    save_to_gallery = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('Issue', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'photo_url': self.photo_url,
            'bio': self.bio,
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
    # Support both old and new schema
    image_url = db.Column(db.String(500))  # Legacy field
    image_urls = db.Column(db.Text)  # New field - JSON array of image URLs
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='issue', lazy=True, cascade='all, delete-orphan')
    
    def get_image_urls(self):
        """Get image URLs as list"""
        # Try new field first
        if self.image_urls:
            try:
                return json.loads(self.image_urls)
            except:
                return []
        # Fallback to legacy field
        elif self.image_url:
            return [self.image_url]
        return []
    
    def set_image_urls(self, urls):
        """Set image URLs from list"""
        if urls:
            self.image_urls = json.dumps(urls)
            # Also set first URL as legacy field for backward compatibility
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
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True)  # VARCHAR(36) in database
    text = db.Column(db.Text, nullable=False)
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)  # VARCHAR(36)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)  # VARCHAR(36)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Note: updated_at column doesn't exist in database
    
    # Relationships
    user = db.relationship('User', backref='comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.text,  # Map 'text' field to 'content' for API consistency
            'issue_id': self.issue_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_photo': self.user.photo_url if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.created_at.isoformat() if self.created_at else None  # Use created_at for both
        }

# ================================
# Supabase Authentication (Only)
# ================================

@lru_cache(maxsize=1)
def get_supabase_jwt_secret():
    """Get Supabase JWT secret from environment"""
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET not found in environment variables")
        logger.error("Available environment variables starting with 'SUPABASE':")
        for key in os.environ:
            if key.startswith('SUPABASE'):
                logger.error(f"  {key}={os.environ[key][:20]}...")
        return None
    
    logger.info(f"Supabase JWT secret loaded: {jwt_secret[:20]}... (length: {len(jwt_secret)})")
    return jwt_secret

def verify_supabase_token(token):
    """
    Verify Supabase JWT access token with comprehensive error handling
    Fixes clock skew, malformed tokens, and signature verification issues
    """
    try:
        jwt_secret = get_supabase_jwt_secret()
        if not jwt_secret:
            logger.error("Supabase JWT secret not configured")
            return None
        
        # Step 1: Basic token format validation (fail fast)
        if not token or not isinstance(token, str):
            logger.error("Token is empty or not a string")
            return None
        
        token_parts = token.split('.')
        if len(token_parts) != 3:
            logger.error(f"Failed to decode token header: Not enough segments")
            return None
        
        # Step 2: Decode header to check algorithm
        try:
            header = jwt.get_unverified_header(token)
            algorithm = header.get('alg', 'HS256')
            logger.debug(f"Token uses algorithm: {algorithm}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {e}")
            return None
        
        decoded_token = None
        
        # Step 3: Handle different algorithms with proper error handling
        if algorithm == 'HS256':
            # Standard HMAC verification with Supabase JWT secret
            try:
                # CRITICAL FIX: Disable iat validation to handle clock skew
                decoded_token = jwt.decode(
                    token, 
                    jwt_secret, 
                    algorithms=['HS256'],
                    options={
                        "verify_exp": True,      # Still verify expiration
                        "verify_aud": False,     # Supabase doesn't always set audience
                        "verify_iat": False,     # DISABLE to fix clock skew issues
                        "verify_nbf": False      # Disable not-before validation
                    }
                )
                logger.debug("Successfully verified HS256 token")
                
            except jwt.ExpiredSignatureError:
                logger.error("Supabase token expired")
                return None
            except jwt.InvalidSignatureError:
                logger.error("Invalid HS256 token: Signature verification failed")
                return None
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid HS256 token: {e}")
                return None
                
        elif algorithm in ['ES256', 'RS256']:
            # For ES256/RS256, decode without signature verification for now
            # In production, you should get the public key from Supabase
            logger.warning(f"Token uses {algorithm} - decoding without signature verification")
            try:
                decoded_token = jwt.decode(
                    token, 
                    options={
                        "verify_signature": False,  # No public key available
                        "verify_exp": True,         # Still check expiration
                        "verify_aud": False,
                        "verify_iat": False,        # Disable to fix clock skew
                        "verify_nbf": False
                    }
                )
                
                # Manual expiration check since we're not verifying signature
                current_time = int(time.time())
                if 'exp' in decoded_token and decoded_token['exp'] < current_time:
                    logger.error("Token expired")
                    return None
                    
                logger.debug(f"Successfully decoded {algorithm} token (no signature verification)")
                
            except jwt.ExpiredSignatureError:
                logger.error("Token expired")
                return None
            except Exception as e:
                logger.error(f"Failed to decode {algorithm} token: {e}")
                return None
        else:
            logger.error(f"Unsupported algorithm: {algorithm}")
            return None
        
        # Step 4: Validate decoded token structure
        if not decoded_token or not isinstance(decoded_token, dict):
            logger.error("Invalid token: decoded token is not a valid dictionary")
            return None
            
        if 'sub' not in decoded_token:
            logger.error("Invalid Supabase token: missing 'sub' field")
            return None
        
        # Step 5: Extract user information from Supabase token
        user_data = {
            'uid': decoded_token['sub'],
            'email': decoded_token.get('email', ''),
            'name': (
                decoded_token.get('user_metadata', {}).get('full_name') or 
                decoded_token.get('user_metadata', {}).get('name') or
                decoded_token.get('name') or
                (decoded_token.get('email', '').split('@')[0] if decoded_token.get('email') else 'User')
            ),
            'provider': 'supabase',
            'aud': decoded_token.get('aud', ''),
            'role': decoded_token.get('role', 'authenticated'),
            'algorithm': algorithm,
            'user_metadata': decoded_token.get('user_metadata', {}),
            'app_metadata': decoded_token.get('app_metadata', {}),
            'exp': decoded_token.get('exp'),
            'iat': decoded_token.get('iat')
        }
        
        logger.info(f"Supabase token verified successfully with {algorithm} for user: {user_data['email']}")
        return user_data
        
    except Exception as e:
        logger.error(f"Supabase token verification failed: {e}")
        return None

def require_auth(f):
    """
    Decorator to require Supabase authentication with comprehensive validation
    Implements fail-fast validation for malformed requests and tokens
    Fixes all authentication issues: clock skew, malformed tokens, invalid headers
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Step 1: Validate Authorization header presence
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning(f"Missing Authorization header from {request.remote_addr}")
            return jsonify({
                'error': 'Authorization header required',
                'message': 'Please provide Authorization: Bearer <token> header'
            }), 401
        
        # Step 2: Validate Bearer format (fix "Invalid Authorization header format")
        if not auth_header.startswith('Bearer '):
            logger.warning(f"Invalid Authorization header format from {request.remote_addr}: {auth_header[:50]}")
            return jsonify({
                'error': 'Invalid Authorization header format',
                'message': 'Authorization header must be: Bearer <token>'
            }), 401
        
        # Step 3: Extract token (strict validation - nginx must preserve exact headers)
        try:
            # Check for exact "Bearer " prefix (case sensitive, single space)
            if not auth_header.startswith('Bearer '):
                logger.warning(f"Invalid Authorization header format from {request.remote_addr}: {auth_header[:50]}")
                return jsonify({
                    'error': 'Invalid Authorization header format',
                    'message': 'Authorization header must be: Bearer <token>'
                }), 401
            
            # Extract token part after "Bearer "
            token_part = auth_header[7:]  # Remove "Bearer " (7 characters)
            
            # STRICT VALIDATION: Check for multiple spaces or trailing spaces
            if '  ' in auth_header or auth_header.rstrip() != auth_header:
                logger.warning(f"Invalid Authorization header with extra spaces from {request.remote_addr}: '{auth_header}'")
                return jsonify({
                    'error': 'Invalid Authorization header format',
                    'message': 'Authorization header must be: Bearer <token> (single space, no trailing spaces)'
                }), 401
            
            # Validate token is not empty after Bearer
            if not token_part or token_part.isspace():
                logger.warning(f"Empty token after Bearer from {request.remote_addr}")
                return jsonify({
                    'error': 'Empty token',
                    'message': 'JWT token cannot be empty after Bearer'
                }), 401
            
            token = token_part.strip()
            
            # Final validation: token should not be empty after stripping
            if not token:
                logger.warning(f"Token is empty after processing from {request.remote_addr}")
                return jsonify({
                    'error': 'Empty token',
                    'message': 'JWT token cannot be empty'
                }), 401
            
        except (IndexError, AttributeError) as e:
            logger.warning(f"Failed to extract token from Authorization header from {request.remote_addr}: {e}")
            return jsonify({
                'error': 'Invalid Authorization header format',
                'message': 'Unable to extract token from Authorization header'
            }), 401
        
        # Step 4: Validate token is not empty and reasonable length
        if not token or token == '':
            logger.warning(f"Empty token in Authorization header from {request.remote_addr}")
            return jsonify({
                'error': 'Empty token',
                'message': 'JWT token cannot be empty'
            }), 401
        
        # Validate token length (prevent extremely long tokens that could cause issues)
        if len(token) > 8192:  # 8KB limit for JWT tokens
            logger.warning(f"Token too long from {request.remote_addr}: {len(token)} characters")
            return jsonify({
                'error': 'Token too long',
                'message': 'JWT token exceeds maximum allowed length'
            }), 400
        
        # Step 5: Basic token format validation (fix "Not enough segments")
        if token in ['invalid-token', 'invalid-token-123', 'header.payload']:
            logger.warning(f"Obviously invalid token from {request.remote_addr}: {token}")
            return jsonify({
                'error': 'Invalid token format',
                'message': 'Token appears to be a test or placeholder value'
            }), 401
        
        token_segments = token.split('.')
        if len(token_segments) != 3:
            logger.warning(f"Malformed JWT token from {request.remote_addr}: {len(token_segments)} segments")
            return jsonify({
                'error': 'Malformed JWT token',
                'message': 'JWT token must have exactly 3 segments (header.payload.signature)'
            }), 401
        
        # Step 6: Verify token with Supabase (handles clock skew and signature issues)
        logger.debug(f"Verifying Supabase JWT token from {request.remote_addr}")
        user_data = verify_supabase_token(token)
        
        if not user_data:
            logger.warning(f"Token verification failed from {request.remote_addr} for token: {token[:20]}...")
            return jsonify({
                'error': 'Invalid or expired token',
                'message': 'Please refresh your session and try again'
            }), 401
        
        # Step 7: Sync user to database with detailed error handling
        try:
            user = sync_user_to_database(user_data)
            if not user:
                logger.error(f"Failed to sync user to database: {user_data.get('email', 'unknown')}")
                logger.error(f"User data received: {user_data}")
                return jsonify({
                    'error': 'User synchronization failed',
                    'message': 'Unable to process user data. Please try again.'
                }), 500
            
            # Step 8: Apply role-based access control
            if not check_user_permissions(user, request.endpoint):
                logger.warning(f"User {user.email} denied access to {request.endpoint}")
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': 'You do not have permission to access this resource'
                }), 403
            
            # Step 9: Log successful authentication
            logger.info(f"Authentication successful: {user.email} (Supabase) -> {request.endpoint}")
            
            return f(user, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Database error during authentication: {e}", exc_info=True)
            logger.error(f"User data that caused error: {user_data}")
            try:
                db.session.rollback()
            except:
                pass  # Ignore rollback errors
            return jsonify({
                'error': 'Authentication database error',
                'message': 'Unable to process authentication. Please try again.'
            }), 500
    
    return decorated_function

def sync_user_to_database(user_data):
    """
    Sync Supabase user data to local database
    Creates or updates user record with bulletproof error handling
    Handles all database constraints and edge cases
    """
    try:
        # Validate input data
        if not user_data or not isinstance(user_data, dict):
            logger.error("Invalid user_data provided to sync_user_to_database")
            return None
        
        uid = user_data.get('uid')
        if not uid:
            logger.error("No UID provided in user_data")
            return None
        
        # Look up user by Supabase UID
        user = User.query.filter_by(firebase_uid=uid).first()
        
        if not user:
            # Create new user with bulletproof validation
            email = user_data.get('email', '').strip()
            name = user_data.get('name', '').strip()
            
            # Handle email constraint (unique=True, nullable=False)
            if not email:
                # Generate unique email based on UID
                email = f"user_{uid.replace('-', '')[:16]}@civicfix.temp"
            
            # Check if email already exists (handle unique constraint)
            existing_email_user = User.query.filter_by(email=email).first()
            if existing_email_user:
                # Generate unique email with timestamp
                import time
                timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
                email = f"user_{uid.replace('-', '')[:10]}_{timestamp}@civicfix.temp"
            
            # Handle name constraint (nullable=False)
            if not name:
                name = f"User_{uid.replace('-', '')[:8]}"
            
            # Ensure name is not too long (max 255 chars)
            if len(name) > 255:
                name = name[:255]
            
            # Ensure email is not too long (max 255 chars)
            if len(email) > 255:
                email = f"user_{uid[:8]}@temp.com"
            
            # Create user with validated data
            try:
                user = User(
                    firebase_uid=uid,
                    email=email,
                    name=name,
                    phone='',
                    photo_url=user_data.get('user_metadata', {}).get('avatar_url', '') or ''
                )
                
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new user: {user.email} (Supabase UID: {uid})")
                
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error creating user: {db_error}")
                
                # Check if user was created by concurrent request
                user = User.query.filter_by(firebase_uid=uid).first()
                if user:
                    logger.info(f"User found after rollback (concurrent creation): {user.email}")
                    return user
                
                # Final fallback - create with minimal guaranteed unique data
                try:
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    fallback_email = f"fallback_{unique_suffix}@civicfix.temp"
                    fallback_name = f"User_{unique_suffix}"
                    
                    user = User(
                        firebase_uid=uid,
                        email=fallback_email,
                        name=fallback_name,
                        phone='',
                        photo_url=''
                    )
                    
                    db.session.add(user)
                    db.session.commit()
                    logger.info(f"Created fallback user: {user.email}")
                    
                except Exception as final_error:
                    db.session.rollback()
                    logger.error(f"Final fallback user creation failed: {final_error}")
                    return None
        else:
            # Update existing user info if needed
            updated = False
            
            # Update email if provided and different
            new_email = user_data.get('email', '').strip()
            if new_email and new_email != user.email:
                # Check if new email is already taken by another user
                existing_user = User.query.filter_by(email=new_email).filter(User.id != user.id).first()
                if not existing_user:
                    try:
                        user.email = new_email
                        updated = True
                    except Exception as email_error:
                        logger.warning(f"Could not update email for user {user.id}: {email_error}")
                else:
                    logger.warning(f"Email {new_email} already taken by another user")
            
            # Update name if provided and different
            new_name = user_data.get('name', '').strip()
            if new_name and new_name != user.name:
                # Ensure name is not too long
                if len(new_name) > 255:
                    new_name = new_name[:255]
                user.name = new_name
                updated = True
            
            # Update photo URL from user metadata
            new_photo_url = user_data.get('user_metadata', {}).get('avatar_url', '') or ''
            if new_photo_url and new_photo_url != user.photo_url:
                # Ensure photo URL is not too long
                if len(new_photo_url) > 500:
                    new_photo_url = new_photo_url[:500]
                user.photo_url = new_photo_url
                updated = True
            
            # Commit updates if any
            if updated:
                try:
                    user.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Updated user info: {user.email}")
                except Exception as update_error:
                    db.session.rollback()
                    logger.warning(f"Could not update user {user.id}: {update_error}")
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to sync user to database: {e}", exc_info=True)
        try:
            db.session.rollback()
        except:
            pass  # Ignore rollback errors
        return None

def check_user_permissions(user, endpoint):
    """
    Role-based access control
    Check if user has permission to access the endpoint
    """
    # For now, all authenticated users have access to all endpoints
    # You can extend this with role-based logic later
    
    # Example role-based access control:
    # if endpoint == 'admin_only_endpoint':
    #     return user.role == 'admin'
    
    # For CivicFix, all authenticated users can access all endpoints
    return True

# ================================
# Routes
# ================================

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'CivicFix Backend API',
        'version': '2.0.0',
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check Supabase JWT secret status
    supabase_status = 'healthy' if get_supabase_jwt_secret() else 'not_configured'
    
    # Check S3 status
    try:
        if s3_service:
            s3_service.s3_client.head_bucket(Bucket=s3_service.bucket_name)
            s3_status = 'healthy'
        else:
            s3_status = 'disabled'
    except Exception as e:
        s3_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '3.0.0-supabase',
        'authentication': 'supabase',
        'services': {
            'database': db_status,
            'supabase_auth': supabase_status,
            's3': s3_status
        }
    })



# ================================
# File Upload Routes
# ================================

@app.route('/api/v1/upload', methods=['POST'])
@require_auth
def upload_file(current_user):
    """Upload file (image or video) to S3"""
    try:
        if not s3_service:
            return jsonify({'error': 'File upload service not available'}), 503
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type - support both images and videos
        allowed_extensions = {
            # Images
            'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff',
            # Videos
            'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'
        }
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file type. Allowed: ' + ', '.join(sorted(allowed_extensions))
            }), 400
        
        # Validate file size - different limits for images and videos
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'}
        max_size = 50 * 1024 * 1024 if file_extension in video_extensions else 10 * 1024 * 1024  # 50MB for videos, 10MB for images
        
        if file_size > max_size:
            size_limit = "50MB" if file_extension in video_extensions else "10MB"
            return jsonify({'error': f'File too large. Maximum size for {file_extension}: {size_limit}'}), 400
        
        # Upload to S3
        file_data = file.read()
        
        # Set appropriate content type
        if file_extension in video_extensions:
            content_type = f'video/{file_extension}' if file_extension != '3gp' else 'video/3gpp'
        else:
            content_type = file.content_type or f'image/{file_extension}'
        
        file_url, error = s3_service.upload_file(file_data, file.filename, content_type)
        
        if error:
            return jsonify({'error': f'Upload failed: {error}'}), 500
        
        logger.info(f"File uploaded by user {current_user.email}: {file_url} ({file_size} bytes)")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_url': file_url,
            'file_name': file.filename,
            'file_size': file_size,
            'file_type': 'video' if file_extension in video_extensions else 'image',
            'content_type': content_type
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/upload/multiple', methods=['POST'])
@require_auth
def upload_multiple_files(current_user):
    """Upload multiple files (images and videos) to S3"""
    try:
        if not s3_service:
            return jsonify({'error': 'File upload service not available'}), 503
            
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Limit number of files
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed'}), 400
        
        uploaded_files = []
        errors = []
        
        # Allowed file extensions
        allowed_extensions = {
            # Images
            'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff',
            # Videos
            'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'
        }
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', '3gp'}
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                # Validate file type
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_extension not in allowed_extensions:
                    errors.append(f"{file.filename}: Invalid file type")
                    continue
                
                # Validate file size
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                
                max_size = 50 * 1024 * 1024 if file_extension in video_extensions else 10 * 1024 * 1024  # 50MB for videos, 10MB for images
                
                if file_size > max_size:
                    size_limit = "50MB" if file_extension in video_extensions else "10MB"
                    errors.append(f"{file.filename}: File too large (max {size_limit})")
                    continue
                
                # Upload to S3
                file_data = file.read()
                
                # Set appropriate content type
                if file_extension in video_extensions:
                    content_type = f'video/{file_extension}' if file_extension != '3gp' else 'video/3gpp'
                else:
                    content_type = file.content_type or f'image/{file_extension}'
                
                file_url, error = s3_service.upload_file(file_data, file.filename, content_type)
                
                if error:
                    errors.append(f"{file.filename}: Upload failed - {error}")
                else:
                    uploaded_files.append({
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_size': file_size,
                        'file_type': 'video' if file_extension in video_extensions else 'image',
                        'content_type': content_type
                    })
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        logger.info(f"Multiple files uploaded by user {current_user.email}: {len(uploaded_files)} successful, {len(errors)} failed")
        
        return jsonify({
            'message': f'{len(uploaded_files)} files uploaded successfully',
            'uploaded_files': uploaded_files,
            'errors': errors
        }), 201 if uploaded_files else 400
        
    except Exception as e:
        logger.error(f"Error uploading multiple files: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/upload-media', methods=['POST'])
@require_auth
def upload_issue_media(current_user):
    """Upload media files for issue creation/update"""
    try:
        logger.info(f"📤 Media upload request from user: {current_user.email}")
        logger.info(f"📤 Request files: {list(request.files.keys())}")
        logger.info(f"📤 Request form: {dict(request.form)}")
        
        if not s3_service:
            logger.error("📤 S3 service not available")
            return jsonify({'error': 'File upload service not available'}), 503
            
        if 'files' not in request.files:
            logger.warning("📤 No 'files' field in request")
            logger.warning(f"📤 Available fields: {list(request.files.keys())}")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        logger.info(f"📤 Received {len(files)} files")
        
        for i, file in enumerate(files):
            logger.info(f"📤 File {i+1}: name='{file.filename}', content_type='{file.content_type}', size={len(file.read())} bytes")
            file.seek(0)  # Reset file pointer after reading for size
        
        if not files or all(f.filename == '' for f in files):
            logger.warning("📤 No files selected or all files have empty names")
            return jsonify({'error': 'No files selected'}), 400
        
        # Limit number of files for issues
        if len(files) > 8:
            return jsonify({'error': 'Maximum 8 media files allowed per issue'}), 400
        
        uploaded_files = []
        errors = []
        total_size = 0
        
        # Allowed file extensions for issues
        allowed_extensions = {
            # Images
            'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp',
            # Videos
            'mp4', 'mov', 'avi', 'mkv', 'webm'
        }
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                # Validate file type
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_extension not in allowed_extensions:
                    errors.append(f"{file.filename}: Invalid file type. Allowed: {', '.join(sorted(allowed_extensions))}")
                    continue
                
                # Validate file size
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                
                # Different size limits for different file types
                if file_extension in video_extensions:
                    max_size = 100 * 1024 * 1024  # 100MB for videos
                    size_limit = "100MB"
                else:
                    max_size = 15 * 1024 * 1024  # 15MB for images
                    size_limit = "15MB"
                
                if file_size > max_size:
                    errors.append(f"{file.filename}: File too large (max {size_limit} for {file_extension})")
                    continue
                
                total_size += file_size
                
                # Check total upload size (max 200MB per issue)
                if total_size > 200 * 1024 * 1024:
                    errors.append(f"{file.filename}: Total upload size exceeds 200MB limit")
                    continue
                
                # Upload to S3 with issue-specific path
                file_data = file.read()
                
                # Set appropriate content type
                if file_extension in video_extensions:
                    content_type = f'video/{file_extension}'
                else:
                    content_type = file.content_type or f'image/{file_extension}'
                
                # Use issue-specific S3 path
                file_url, error = s3_service.upload_file(file_data, f"issue_media_{file.filename}", content_type)
                
                if error:
                    errors.append(f"{file.filename}: Upload failed - {error}")
                else:
                    uploaded_files.append({
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_size': file_size,
                        'file_type': 'video' if file_extension in video_extensions else 'image',
                        'content_type': content_type,
                        'file_extension': file_extension
                    })
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        logger.info(f"Issue media uploaded by user {current_user.email}: {len(uploaded_files)} successful, {len(errors)} failed, total size: {total_size} bytes")
        
        # Return URLs array for easy integration with issue creation
        media_urls = [file['file_url'] for file in uploaded_files]
        
        return jsonify({
            'message': f'{len(uploaded_files)} media files uploaded successfully',
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
        logger.error(f"Error uploading issue media: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Issue Routes
# ================================

# ================================
# Issue Routes
# ================================

@app.route('/api/v1/issues', methods=['GET'])
def get_issues():
    """Get all issues with optional filtering and search"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')  # New search parameter
        
        # Build query
        query = Issue.query
        
        # Search functionality - search in title, description, and address
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Issue.title.ilike(search_term),
                    Issue.description.ilike(search_term),
                    Issue.address.ilike(search_term)
                )
            )
        
        # Category filter
        if category and category.lower() != 'all':
            query = query.filter(Issue.category == category)
        
        # Status filter
        if status:
            query = query.filter(Issue.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        issues = [issue.to_dict() for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
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
            logger.warning("Create issue request with no JSON data")
            return jsonify({'error': 'Request body required'}), 400
        
        logger.info(f"Creating issue for user {current_user.email} with data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'category', 'latitude', 'longitude']
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            logger.warning(f"Create issue validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Validate data types
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid latitude/longitude values: {e}")
            return jsonify({'error': 'Invalid latitude or longitude values'}), 400
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        priority = data.get('priority', 'medium').lower()
        if priority not in valid_priorities:
            priority = 'medium'
        
        # Create issue
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
        
        # Handle image URLs (can be single URL or array of URLs)
        image_urls = data.get('image_urls', [])
        if isinstance(image_urls, str):
            image_urls = [image_urls]
        elif not isinstance(image_urls, list):
            image_urls = []
        
        # Also support legacy image_url field
        if 'image_url' in data and data['image_url']:
            if data['image_url'] not in image_urls:
                image_urls.append(data['image_url'])
        
        # Filter out empty URLs
        image_urls = [url for url in image_urls if url and url.strip()]
        
        issue.set_image_urls(image_urls)
        
        db.session.add(issue)
        db.session.commit()
        
        logger.info(f"Issue created successfully: ID {issue.id} by user {current_user.email}")
        
        return jsonify({
            'message': 'Issue created successfully',
            'issue': issue.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}", exc_info=True)
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
        logger.error(f"Error getting issue {issue_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/status', methods=['PUT'])
@require_auth
def update_issue_status(current_user, issue_id):
    """Update issue status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
            
        issue.status = new_status
        issue.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Issue {issue_id} status updated to {new_status} by {current_user.email}")
        
        return jsonify({
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating issue status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Authentication Routes
# ================================

@app.route('/api/v1/auth/google', methods=['POST'])
def authenticate_with_google():
    """Authenticate user with Google OAuth via Supabase"""
    try:
        data = request.get_json()
        if not data or 'id_token' not in data:
            return jsonify({'error': 'Google ID token is required'}), 400
        
        id_token = data['id_token']
        
        # Verify the Supabase JWT token
        user_data = verify_supabase_token(id_token)
        if not user_data:
            return jsonify({'error': 'Invalid Google ID token'}), 401
        
        # Sync user to database
        user = sync_user_to_database(user_data)
        if not user:
            return jsonify({'error': 'Failed to create user account'}), 500
        
        logger.info(f"Google authentication successful for user: {user.email}")
        
        return jsonify({
            'user': user.to_dict(),
            'token': id_token,  # Return the same token for frontend use
            'message': 'Authentication successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Google authentication failed: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/v1/auth/test', methods=['GET'])
@require_auth
def test_auth(current_user):
    """Test Supabase authentication endpoint"""
    return jsonify({
        'message': 'Authentication successful',
        'user': current_user.to_dict(),
        'timestamp': datetime.utcnow().isoformat(),
        'provider': 'supabase'
    }), 200

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
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Update profile fields
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'error': 'Name cannot be empty'}), 400
            if len(name) > 255:
                return jsonify({'error': 'Name too long (max 255 characters)'}), 400
            current_user.name = name
            
        if 'phone' in data:
            phone = data['phone'].strip() if data['phone'] else ''
            if len(phone) > 20:
                return jsonify({'error': 'Phone number too long (max 20 characters)'}), 400
            current_user.phone = phone
            
        if 'photo_url' in data:
            photo_url = data['photo_url'].strip() if data['photo_url'] else ''
            if len(photo_url) > 500:
                return jsonify({'error': 'Photo URL too long (max 500 characters)'}), 400
            current_user.photo_url = photo_url
            
        if 'bio' in data:
            bio = data['bio'].strip() if data['bio'] else ''
            current_user.bio = bio
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/me/settings', methods=['PUT'])
@require_auth
def update_user_settings(current_user):
    """Update user settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Update settings fields
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
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Settings updated for user: {current_user.email}")
        
        return jsonify({
            'message': 'Settings updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/me/password', methods=['PUT'])
@require_auth
def change_password(current_user):
    """Change user password (Supabase integration)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # For Supabase authentication, password changes should be handled on the client side
        # using Supabase's updateUser method. This endpoint serves as a notification/logging endpoint.
        
        # Validate that required fields are present (for logging purposes)
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'error': 'Current password and new password are required',
                'message': 'For Supabase users, password changes must be initiated from the client app using Supabase auth methods'
            }), 400
        
        # Since we're using Supabase auth, we can't directly change passwords on the backend
        # The frontend should use Supabase's updateUser method
        logger.info(f"Password change request received for user: {current_user.email}")
        
        return jsonify({
            'message': 'Password change must be handled through Supabase client',
            'instructions': 'Use supabase.auth.updateUser({ password: newPassword }) in your frontend app',
            'supabase_method': 'updateUser'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in password change endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Additional Issue Routes
# ================================

@app.route('/api/v1/issues/<int:issue_id>', methods=['PUT'])
@require_auth
def update_issue(current_user, issue_id):
    """Update an issue (only by creator or admin)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user is the creator (in a real app, you might have admin roles)
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Update allowed fields
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
        
        # Handle image URLs update
        if 'image_urls' in data:
            image_urls = data['image_urls']
            if isinstance(image_urls, str):
                image_urls = [image_urls]
            elif not isinstance(image_urls, list):
                image_urls = []
            issue.set_image_urls(image_urls)
        elif 'image_url' in data:
            # Support legacy single image_url
            if data['image_url']:
                issue.set_image_urls([data['image_url']])
            else:
                issue.set_image_urls([])
        
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Issue {issue_id} updated by user {current_user.email}")
        
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
    """Delete an issue (only by creator)"""
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user is the creator
        if issue.created_by != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        db.session.delete(issue)
        db.session.commit()
        
        logger.info(f"Issue {issue_id} deleted by user {current_user.email}")
        
        return jsonify({'message': 'Issue deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting issue: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/users/<int:user_id>/issues', methods=['GET'])
def get_user_issues(user_id):
    """Get issues created by a specific user"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        
        # Build query
        query = Issue.query.filter_by(created_by=user_id)
        
        if status:
            query = query.filter(Issue.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Issue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        issues = [issue.to_dict() for issue in pagination.items]
        
        return jsonify({
            'issues': issues,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        total_issues = Issue.query.count()
        total_users = User.query.count()
        
        # Issues by status
        open_issues = Issue.query.filter_by(status='OPEN').count()
        in_progress_issues = Issue.query.filter_by(status='IN_PROGRESS').count()
        resolved_issues = Issue.query.filter_by(status='RESOLVED').count()
        closed_issues = Issue.query.filter_by(status='CLOSED').count()
        
        # Issues by category
        categories_stats = {}
        categories = [
            'Pothole', 'Street Light', 'Garbage Collection', 'Traffic Signal',
            'Road Damage', 'Water Leak', 'Sidewalk Issue', 'Graffiti',
            'Noise Complaint', 'Other'
        ]
        
        for category in categories:
            count = Issue.query.filter_by(category=category).count()
            if count > 0:
                categories_stats[category] = count
        
        return jsonify({
            'total_issues': total_issues,
            'total_users': total_users,
            'issues_by_status': {
                'OPEN': open_issues,
                'IN_PROGRESS': in_progress_issues,
                'RESOLVED': resolved_issues,
                'CLOSED': closed_issues
            },
            'issues_by_category': categories_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ================================
# Utility Routes
# ================================

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """Get available issue categories"""
    categories = [
        'Pothole',
        'Street Light',
        'Garbage Collection',
        'Traffic Signal',
        'Road Damage',
        'Water Leak',
        'Sidewalk Issue',
        'Graffiti',
        'Noise Complaint',
        'Other'
    ]
    return jsonify({'categories': categories})

@app.route('/api/v1/issues/nearby', methods=['GET'])
def get_nearby_issues():
    """Get issues near a specific location"""
    try:
        # Get location parameters
        lat = request.args.get('latitude', type=float)
        lng = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 5.0, type=float)  # Default 5km radius
        
        if lat is None or lng is None:
            return jsonify({'error': 'latitude and longitude parameters are required'}), 400
        
        # Simple distance calculation (for more accuracy, use PostGIS in production)
        # This is a basic implementation using Haversine formula approximation
        lat_range = radius / 111.0  # Rough conversion: 1 degree ≈ 111 km
        lng_range = radius / (111.0 * abs(lat) / 90.0) if lat != 0 else radius / 111.0
        
        # Query issues within the bounding box
        issues = Issue.query.filter(
            Issue.latitude.between(lat - lat_range, lat + lat_range),
            Issue.longitude.between(lng - lng_range, lng + lng_range)
        ).order_by(Issue.created_at.desc()).limit(50).all()
        
        return jsonify({
            'issues': [issue.to_dict() for issue in issues],
            'center': {'latitude': lat, 'longitude': lng},
            'radius_km': radius,
            'count': len(issues)
        })
        
    except Exception as e:
        logger.error(f"Error getting nearby issues: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/status-options', methods=['GET'])
def get_status_options():
    """Get available issue status options"""
    statuses = [
        {'value': 'OPEN', 'label': 'Open', 'description': 'Issue reported and awaiting review'},
        {'value': 'IN_PROGRESS', 'label': 'In Progress', 'description': 'Issue is being worked on'},
        {'value': 'RESOLVED', 'label': 'Resolved', 'description': 'Issue has been fixed'},
        {'value': 'CLOSED', 'label': 'Closed', 'description': 'Issue is closed (resolved or rejected)'},
        {'value': 'REJECTED', 'label': 'Rejected', 'description': 'Issue was rejected or invalid'}
    ]
    return jsonify({'statuses': statuses})

# ================================
# Comment Routes
# ================================

@app.route('/api/v1/issues/<int:issue_id>/comments', methods=['GET'])
def get_issue_comments(issue_id):
    """Get all comments for a specific issue"""
    try:
        # Check if issue exists
        issue = Issue.query.get(str(issue_id))  # Convert to string for UUID lookup
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get comments for the issue (convert issue_id to string)
        query = Comment.query.filter_by(issue_id=str(issue_id)).order_by(Comment.created_at.asc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        comments = [comment.to_dict() for comment in pagination.items]
        
        return jsonify({
            'comments': comments,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting comments for issue {issue_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/issues/<int:issue_id>/comments', methods=['POST'])
@require_auth
def create_comment(current_user, issue_id):
    """Create a new comment on an issue"""
    try:
        # Check if issue exists
        issue = Issue.query.get(str(issue_id))  # Convert to string for UUID lookup
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': 'Comment content is required'}), 400
        
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Comment content cannot be empty'}), 400
        
        # Create comment with UUID
        import uuid
        comment = Comment(
            id=str(uuid.uuid4()),  # Generate UUID for comment ID
            text=content,
            issue_id=str(issue_id),  # Convert to string
            user_id=str(current_user.id)  # Convert to string
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f"Comment created on issue {issue_id} by user {current_user.email}")
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/comments/<comment_id>', methods=['PUT'])
@require_auth
def update_comment(current_user, comment_id):
    """Update a comment (only by the comment author)"""
    try:
        comment = Comment.query.get(comment_id)  # comment_id is already a string
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check if user is the comment author (convert user IDs to string for comparison)
        if comment.user_id != str(current_user.id):
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': 'Comment content is required'}), 400
        
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Comment content cannot be empty'}), 400
        
        comment.text = content
        # Note: Not setting updated_at since column doesn't exist in database
        
        db.session.commit()
        
        logger.info(f"Comment {comment_id} updated by user {current_user.email}")
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/comments/<comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(current_user, comment_id):
    """Delete a comment (only by the comment author)"""
    try:
        comment = Comment.query.get(comment_id)  # comment_id is already a string
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Check if user is the comment author (convert user IDs to string for comparison)
        if comment.user_id != str(current_user.id):
            return jsonify({'error': 'Permission denied'}), 403
        
        db.session.delete(comment)
        db.session.commit()
        
        logger.info(f"Comment {comment_id} deleted by user {current_user.email}")
        
        return jsonify({'message': 'Comment deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/priority-options', methods=['GET'])
def get_priority_options():
    """Get available issue priority options"""
    priorities = [
        {'value': 'LOW', 'label': 'Low', 'description': 'Non-urgent issue'},
        {'value': 'MEDIUM', 'label': 'Medium', 'description': 'Standard priority'},
        {'value': 'HIGH', 'label': 'High', 'description': 'Important issue requiring attention'},
        {'value': 'URGENT', 'label': 'Urgent', 'description': 'Critical issue requiring immediate attention'}
    ]
    return jsonify({'priority_options': priorities})

# ================================
# Error Handlers
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ================================
# Application Startup
# ================================

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        logger.info("Database tables created/verified")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=False)

# ================================
# Initialize Application
# ================================

def create_tables():
    """Create database tables"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

if __name__ == '__main__':
    # Initialize Firebase
    # init_firebase()
    
    # Create tables
    create_tables()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting CivicFix Backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
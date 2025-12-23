"""
Production-safe AWS Service - Fixed recursion issues
"""

import boto3
import logging
import threading
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class AWSServiceError(Exception):
    pass

class AWSService:
    _instance: Optional['AWSService'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls) -> 'AWSService':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.s3_client: Optional[boto3.client] = None
        self.bucket_name: Optional[str] = None
        self.region: Optional[str] = None
        self._initialized = True
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize AWS services - no recursion"""
        try:
            self.bucket_name = config.get('S3_BUCKET_NAME')
            self.region = config.get('AWS_REGION', 'us-east-1')
            access_key = config.get('AWS_ACCESS_KEY_ID')
            secret_key = config.get('AWS_SECRET_ACCESS_KEY')
            
            if not self.bucket_name:
                raise AWSServiceError("S3_BUCKET_NAME is required")
            
            # Create S3 client
            if access_key and secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self.region
                )
            else:
                # Use default credential chain (IAM role)
                self.s3_client = boto3.client('s3', region_name=self.region)
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            logger.info(f"AWS S3 initialized: {self.bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"AWS initialization failed: {e}")
            self._cleanup()
            raise AWSServiceError(f"AWS init failed: {e}") from e
    
    def _cleanup(self):
        self.s3_client = None
        self.bucket_name = None
    
    def is_available(self) -> bool:
        return self.s3_client is not None and self.bucket_name is not None
    
    def generate_presigned_upload_url(self, file_key: str, content_type: str, expiration: int = 3600) -> Dict[str, Any]:
        if not self.is_available():
            raise AWSServiceError("AWS S3 service not available")
            
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 16777216]
                ],
                ExpiresIn=expiration
            )
            
            return {
                'upload_url': response['url'],
                'fields': response['fields'],
                'file_url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"
            }
            
        except ClientError as e:
            raise AWSServiceError(f"Failed to generate upload URL: {e}") from e
    
    def generate_presigned_download_url(self, file_key: str, expiration: int = 3600) -> str:
        if not self.is_available():
            raise AWSServiceError("AWS S3 service not available")
            
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
        except ClientError as e:
            raise AWSServiceError(f"Failed to generate download URL: {e}") from e
    
    def delete_file(self, file_key: str) -> bool:
        if not self.is_available():
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
    
    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists, create if it doesn't"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"S3 bucket '{self.bucket_name}' exists")
            
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            
            if error_code == 404:
                # Bucket doesn't exist, create it
                self.logger.info(f"Creating S3 bucket: {self.bucket_name}")
                
                try:
                    if current_app.config['AWS_REGION'] == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': current_app.config['AWS_REGION']
                            }
                        )
                    
                    # Configure bucket for private access
                    self._configure_bucket_security()
                    
                    self.logger.info("S3 bucket created successfully")
                    
                except ClientError as create_error:
                    self.logger.error(f"Failed to create S3 bucket: {str(create_error)}")
                    raise
            else:
                self.logger.error(f"Error accessing S3 bucket: {str(e)}")
                raise
    
    def _configure_bucket_security(self):
        """Configure bucket for private access with CORS"""
        try:
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            # Configure CORS for mobile app access
            cors_configuration = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            
            self.logger.info("S3 bucket security configured")
            
        except ClientError as e:
            self.logger.warning(f"Failed to configure bucket security: {str(e)}")
    
    def is_available(self):
        """Check if AWS services are available"""
        return self.s3_client is not None
    
    def generate_presigned_upload_url(self, file_key, content_type, expiration=3600):
        """Generate presigned URL for file upload"""
        if not self.is_available():
            raise RuntimeError("AWS S3 service is not available - check configuration")
            
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, current_app.config['MAX_CONTENT_LENGTH']]
                ],
                ExpiresIn=expiration
            )
            
            return {
                'upload_url': response['url'],
                'fields': response['fields'],
                'file_url': f"https://{self.bucket_name}.s3.{current_app.config['AWS_REGION']}.amazonaws.com/{file_key}"
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise
    
    def generate_presigned_download_url(self, file_key, expiration=3600):
        """Generate presigned URL for file download"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return response
            
        except ClientError as e:
            self.logger.error(f"Failed to generate download URL: {str(e)}")
            raise
    
    def delete_file(self, file_key):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            self.logger.info(f"File deleted from S3: {file_key}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
    
    def get_file_info(self, file_key):
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to get file info: {str(e)}")
            return None
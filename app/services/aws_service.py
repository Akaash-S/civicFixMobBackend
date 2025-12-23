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
            
            # Create S3 client with proper configuration
            client_config = boto3.session.Config(
                region_name=self.region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50
            )
            
            if access_key and secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    config=client_config
                )
            else:
                # Use default credential chain (IAM role)
                self.s3_client = boto3.client('s3', config=client_config)
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            logger.info(f"AWS S3 initialized: {self.bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"AWS initialization failed: {e}")
            self._cleanup()
            raise AWSServiceError(f"AWS init failed: {e}") from e
    
    def _cleanup(self):
        """Clean up resources"""
        self.s3_client = None
        self.bucket_name = None
    
    def is_available(self) -> bool:
        """Check if AWS services are available"""
        return self.s3_client is not None and self.bucket_name is not None
    
    def generate_presigned_upload_url(self, file_key: str, content_type: str, expiration: int = 3600) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        if not self.is_available():
            raise AWSServiceError("AWS S3 service not available")
            
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 16777216]  # 16MB max
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
        """Generate presigned URL for file download"""
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
        """Delete file from S3"""
        if not self.is_available():
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted from S3: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from S3"""
        if not self.is_available():
            return None
            
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
        except ClientError as e:
            logger.error(f"Failed to get file info: {e}")
            return None
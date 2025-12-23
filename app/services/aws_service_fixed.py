"""
Production-safe AWS Service Implementation
- No recursion
- Thread-safe singleton
- Proper error handling
- Docker/EC2/IAM role compatible
"""

import boto3
import logging
import threading
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from datetime import datetime, timedelta

# Module-level logger (no circular imports)
logger = logging.getLogger(__name__)

class AWSServiceError(Exception):
    """Custom exception for AWS service errors"""
    pass

class AWSService:
    """
    Thread-safe singleton AWS service with proper initialization
    """
    
    _instance: Optional['AWSService'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls) -> 'AWSService':
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once - prevent recursion"""
        if self._initialized:
            return
            
        # Initialize instance variables
        self.s3_client: Optional[boto3.client] = None
        self.bucket_name: Optional[str] = None
        self.region: Optional[str] = None
        self._health_check_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Mark as initialized to prevent recursion
        self._initialized = True
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize AWS services with configuration
        
        Args:
            config: Dictionary with AWS configuration
            
        Returns:
            bool: True if initialization successful
            
        Raises:
            AWSServiceError: If initialization fails
        """
        try:
            # Extract configuration
            self.bucket_name = config.get('S3_BUCKET_NAME')
            self.region = config.get('AWS_REGION', 'us-east-1')
            access_key = config.get('AWS_ACCESS_KEY_ID')
            secret_key = config.get('AWS_SECRET_ACCESS_KEY')
            
            # Validate required configuration
            if not self.bucket_name:
                raise AWSServiceError("S3_BUCKET_NAME is required")
            
            # Initialize S3 client with proper credential handling
            self.s3_client = self._create_s3_client(access_key, secret_key)
            
            # Verify connectivity (with timeout)
            self._verify_s3_access()
            
            logger.info(f"AWS S3 service initialized successfully. Bucket: {self.bucket_name}, Region: {self.region}")
            return True
            
        except Exception as e:
            logger.error(f"AWS service initialization failed: {str(e)}")
            # Clean up partial initialization
            self._cleanup()
            raise AWSServiceError(f"Failed to initialize AWS services: {str(e)}") from e
    
    def _create_s3_client(self, access_key: Optional[str], secret_key: Optional[str]) -> boto3.client:
        """
        Create S3 client with proper credential chain
        
        Priority:
        1. Explicit credentials (if provided)
        2. Environment variables
        3. IAM role (EC2/ECS)
        4. AWS credentials file
        """
        try:
            # Configuration for production reliability
            config = boto3.session.Config(
                region_name=self.region,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                max_pool_connections=50,
                connect_timeout=10,
                read_timeout=30
            )
            
            # Use explicit credentials if provided, otherwise use default chain
            if access_key and secret_key:
                logger.info("Using explicit AWS credentials")
                return boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    config=config
                )
            else:
                logger.info("Using AWS default credential chain (IAM role/env vars)")
                return boto3.client('s3', config=config)
                
        except Exception as e:
            raise AWSServiceError(f"Failed to create S3 client: {str(e)}") from e
    
    def _verify_s3_access(self) -> None:
        """Verify S3 bucket access with timeout"""
        try:
            # Quick connectivity test
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' is accessible")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            if error_code == '404':
                raise AWSServiceError(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code in ['403', 'Forbidden']:
                raise AWSServiceError(f"Access denied to S3 bucket '{self.bucket_name}'. Check IAM permissions.")
            else:
                raise AWSServiceError(f"S3 bucket access failed: {error_code} - {str(e)}")
                
        except NoCredentialsError:
            raise AWSServiceError("AWS credentials not found. Check IAM role, environment variables, or credentials file.")
        except BotoCoreError as e:
            raise AWSServiceError(f"AWS connection error: {str(e)}")
    
    def _cleanup(self) -> None:
        """Clean up resources on initialization failure"""
        self.s3_client = None
        self.bucket_name = None
        self._health_check_cache.clear()
    
    def is_healthy(self) -> bool:
        """
        Check if AWS service is healthy (with caching)
        """
        now = datetime.utcnow()
        cache_key = 'health_check'
        
        # Check cache first
        if cache_key in self._health_check_cache:
            cached_time, cached_result = self._health_check_cache[cache_key]
            if (now - cached_time).total_seconds() < self._cache_ttl:
                return cached_result
        
        # Perform health check
        try:
            if not self.s3_client or not self.bucket_name:
                return False
                
            # Quick health check
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            result = True
            
        except Exception as e:
            logger.warning(f"AWS health check failed: {str(e)}")
            result = False
        
        # Cache result
        self._health_check_cache[cache_key] = (now, result)
        return result
    
    def generate_presigned_upload_url(self, file_key: str, content_type: str, expiration: int = 3600) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        if not self.is_healthy():
            raise AWSServiceError("AWS S3 service is not available")
        
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
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise AWSServiceError(f"Failed to generate upload URL: {str(e)}") from e
    
    def generate_presigned_download_url(self, file_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file download"""
        if not self.is_healthy():
            raise AWSServiceError("AWS S3 service is not available")
        
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return response
            
        except ClientError as e:
            logger.error(f"Failed to generate download URL: {str(e)}")
            raise AWSServiceError(f"Failed to generate download URL: {str(e)}") from e
    
    def delete_file(self, file_key: str) -> bool:
        """Delete file from S3"""
        if not self.is_healthy():
            raise AWSServiceError("AWS S3 service is not available")
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted from S3: {file_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for health checks"""
        return {
            'service': 'aws_s3',
            'bucket': self.bucket_name,
            'region': self.region,
            'healthy': self.is_healthy(),
            'initialized': self._initialized
        }

# Module-level functions for safe access
_aws_service_instance: Optional[AWSService] = None

def get_aws_service() -> Optional[AWSService]:
    """
    Get AWS service instance (thread-safe)
    Returns None if not initialized
    """
    global _aws_service_instance
    return _aws_service_instance

def initialize_aws_service(config: Dict[str, Any]) -> AWSService:
    """
    Initialize AWS service with configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        AWSService: Initialized service instance
        
    Raises:
        AWSServiceError: If initialization fails
    """
    global _aws_service_instance
    
    if _aws_service_instance is None:
        _aws_service_instance = AWSService()
        _aws_service_instance.initialize(config)
    
    return _aws_service_instance

def cleanup_aws_service() -> None:
    """Cleanup AWS service (for testing)"""
    global _aws_service_instance
    if _aws_service_instance:
        _aws_service_instance._cleanup()
        _aws_service_instance = None
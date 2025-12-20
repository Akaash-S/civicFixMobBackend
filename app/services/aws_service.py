import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app
from datetime import datetime, timedelta

class AWSService:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = None
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize AWS services and verify connectivity"""
        try:
            # Get configuration
            self.bucket_name = current_app.config['S3_BUCKET_NAME']
            aws_access_key = current_app.config['AWS_ACCESS_KEY_ID']
            aws_secret_key = current_app.config['AWS_SECRET_ACCESS_KEY']
            aws_region = current_app.config['AWS_REGION']
            
            if not all([self.bucket_name, aws_access_key, aws_secret_key]):
                raise ValueError("Missing required AWS configuration")
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            
            # Verify S3 connectivity and bucket
            self._ensure_bucket_exists()
            
            self.logger.info(f"✅ AWS S3 initialized successfully with bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            self.logger.error("❌ AWS credentials not found")
            raise
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AWS services: {str(e)}")
            raise
    
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
                    
                    self.logger.info(f"✅ S3 bucket '{self.bucket_name}' created successfully")
                    
                except ClientError as create_error:
                    self.logger.error(f"❌ Failed to create S3 bucket: {str(create_error)}")
                    raise
            else:
                self.logger.error(f"❌ Error accessing S3 bucket: {str(e)}")
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
    
    def generate_presigned_upload_url(self, file_key, content_type, expiration=3600):
        """Generate presigned URL for file upload"""
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
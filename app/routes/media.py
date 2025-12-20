from flask import Blueprint, request, jsonify, current_app
from app.utils.decorators import firebase_required
import logging
import uuid
import os
from datetime import datetime

media_bp = Blueprint('media', __name__)
logger = logging.getLogger(__name__)

@media_bp.route('/presign-url', methods=['POST'])
@firebase_required
def generate_presigned_url(current_user_firebase):
    """Generate presigned URL for file upload to S3"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        file_name = data.get('file_name')
        content_type = data.get('content_type')
        file_size = data.get('file_size', 0)
        
        if not file_name or not content_type:
            return jsonify({'error': 'file_name and content_type are required'}), 400
        
        # Validate file type
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'video/mp4', 'video/quicktime', 'video/x-msvideo'
        ]
        
        if content_type not in allowed_types:
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Validate file size
        max_size = current_app.config['MAX_CONTENT_LENGTH']
        if file_size > max_size:
            return jsonify({'error': f'File size exceeds maximum allowed size of {max_size} bytes'}), 400
        
        # Generate unique file key
        file_extension = os.path.splitext(file_name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Organize files by date and user
        user_id = current_user_firebase['uid']
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        file_key = f"issues/{date_prefix}/{user_id}/{unique_filename}"
        
        # Generate presigned URL
        aws_service = getattr(current_app, 'aws_service', None)
        if not aws_service:
            if current_app.config.get('DEBUG'):
                # For development without AWS, return a mock response
                return jsonify({
                    'upload_url': 'http://localhost:5000/mock-upload',
                    'fields': {},
                    'file_url': f'http://localhost:5000/mock-files/{unique_filename}',
                    'file_key': file_key
                }), 200
            else:
                return jsonify({'error': 'File upload service unavailable'}), 503
        
        presigned_data = aws_service.generate_presigned_upload_url(
            file_key=file_key,
            content_type=content_type,
            expiration=3600  # 1 hour
        )
        
        logger.info(f"Generated presigned URL for user {user_id}: {file_key}")
        
        return jsonify({
            'upload_url': presigned_data['upload_url'],
            'fields': presigned_data['fields'],
            'file_url': presigned_data['file_url'],
            'file_key': file_key
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/download-url', methods=['POST'])
@firebase_required
def generate_download_url(current_user_firebase):
    """Generate presigned URL for file download from S3"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        file_key = data.get('file_key')
        
        if not file_key:
            return jsonify({'error': 'file_key is required'}), 400
        
        # Generate presigned download URL
        aws_service = current_app.aws_service
        download_url = aws_service.generate_presigned_download_url(
            file_key=file_key,
            expiration=3600  # 1 hour
        )
        
        return jsonify({
            'download_url': download_url,
            'expires_in': 3600
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@media_bp.route('/file-info', methods=['POST'])
@firebase_required
def get_file_info(current_user_firebase):
    """Get file information from S3"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        file_key = data.get('file_key')
        
        if not file_key:
            return jsonify({'error': 'file_key is required'}), 400
        
        # Get file info from S3
        aws_service = current_app.aws_service
        file_info = aws_service.get_file_info(file_key)
        
        if not file_info:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'file_key': file_key,
            'size': file_info['size'],
            'last_modified': file_info['last_modified'].isoformat(),
            'content_type': file_info['content_type']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
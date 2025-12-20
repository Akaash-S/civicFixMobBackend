import firebase_admin
from firebase_admin import credentials, auth
import logging
import os
from flask import current_app

class FirebaseService:
    def __init__(self):
        self.app = None
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            service_account_path = current_app.config['FIREBASE_SERVICE_ACCOUNT_PATH']
            project_id = current_app.config['FIREBASE_PROJECT_ID']
            
            if not service_account_path or not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Firebase service account file not found: {service_account_path}")
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_path)
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': project_id
            })
            
            # Verify connectivity by getting a test user (this will fail gracefully if no users exist)
            try:
                auth.list_users(max_results=1)
                self.logger.info("Firebase Admin SDK initialized and verified successfully")
            except Exception as e:
                self.logger.info("Firebase Admin SDK initialized (verification skipped)")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def verify_token(self, id_token):
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name', ''),
                'email_verified': decoded_token.get('email_verified', False)
            }
        except Exception as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            return None
    
    def get_user_by_uid(self, uid):
        """Get user information by Firebase UID"""
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'name': user_record.display_name or '',
                'email_verified': user_record.email_verified,
                'created_at': user_record.user_metadata.creation_timestamp
            }
        except Exception as e:
            self.logger.error(f"Failed to get user by UID: {str(e)}")
            return None
    
    def create_custom_token(self, uid, additional_claims=None):
        """Create custom token for user"""
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to create custom token: {str(e)}")
            return None
    
    def revoke_refresh_tokens(self, uid):
        """Revoke all refresh tokens for a user"""
        try:
            auth.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            self.logger.error(f"Failed to revoke tokens: {str(e)}")
            return False
import firebase_admin
from firebase_admin import credentials, auth
import logging
import os
from typing import Optional, Dict, Any

class FirebaseServiceError(Exception):
    pass

class FirebaseService:
    def __init__(self):
        self.app = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Firebase Admin SDK - no Flask dependencies"""
        if self._initialized:
            return True
            
        try:
            service_account_path = config.get('FIREBASE_SERVICE_ACCOUNT_PATH')
            project_id = config.get('FIREBASE_PROJECT_ID')
            
            if not service_account_path or not os.path.exists(service_account_path):
                raise FirebaseServiceError(f"Firebase service account file not found: {service_account_path}")
            
            if not project_id:
                raise FirebaseServiceError("FIREBASE_PROJECT_ID is required")
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_path)
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': project_id
            })
            
            # Verify connectivity
            try:
                auth.list_users(max_results=1)
                self.logger.info("Firebase Admin SDK initialized and verified successfully")
            except Exception as e:
                self.logger.info("Firebase Admin SDK initialized (verification skipped)")
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise FirebaseServiceError(f"Firebase initialization failed: {str(e)}") from e
    
    def is_available(self) -> bool:
        """Check if Firebase service is available"""
        return self._initialized and self.app is not None
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not initialized")
            
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
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user information by Firebase UID"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not initialized")
            
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
    
    def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> Optional[str]:
        """Create custom token for user"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not initialized")
            
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to create custom token: {str(e)}")
            return None
    
    def revoke_refresh_tokens(self, uid: str) -> bool:
        """Revoke all refresh tokens for a user"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not initialized")
            
        try:
            auth.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            self.logger.error(f"Failed to revoke tokens: {str(e)}")
            return False
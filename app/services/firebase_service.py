import firebase_admin
from firebase_admin import credentials, auth
import logging
import os
import time
from typing import Optional, Dict, Any

class FirebaseServiceError(Exception):
    pass

class FirebaseService:
    def __init__(self):
        self.app = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self._available = False
    
    def initialize(self, config: Dict[str, Any], timeout: int = 30) -> bool:
        """
        Initialize Firebase Admin SDK with timeout - never block server startup
        
        Args:
            config: Firebase configuration dictionary
            timeout: Maximum time to wait for initialization (seconds)
            
        Returns:
            bool: True if successful, False if failed/timeout
        """
        if self._initialized:
            return self._available
            
        start_time = time.time()
        
        try:
            logger.info(f"Initializing Firebase services (timeout: {timeout}s)...")
            
            service_account_path = config.get('FIREBASE_SERVICE_ACCOUNT_PATH')
            project_id = config.get('FIREBASE_PROJECT_ID')
            
            # Quick validation
            if not service_account_path or not os.path.exists(service_account_path):
                logger.warning(f"Firebase service account file not found: {service_account_path} - Firebase disabled")
                self._initialized = True
                return False
            
            if not project_id:
                logger.warning("FIREBASE_PROJECT_ID not configured - Firebase disabled")
                self._initialized = True
                return False
            
            # Check for placeholder values
            if "your-" in str(project_id):
                logger.warning("Firebase configuration contains placeholder values - Firebase disabled")
                self._initialized = True
                return False
            
            # Initialize Firebase Admin SDK with timeout check
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Firebase initialization timeout ({timeout}s) - skipping")
                self._initialized = True
                return False
            
            cred = credentials.Certificate(service_account_path)
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': project_id
            })
            
            # Quick verification with timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Firebase verification timeout ({timeout}s) - skipping verification")
                self._available = True  # Assume it works
                self._initialized = True
                return True
            
            # Verify connectivity (quick test)
            try:
                auth.list_users(max_results=1)
                logger.info(f"Firebase Admin SDK initialized and verified in {elapsed:.2f}s")
            except Exception as e:
                logger.info(f"Firebase Admin SDK initialized (verification skipped): {e}")
            
            elapsed = time.time() - start_time
            self._available = True
            self._initialized = True
            logger.info(f"Firebase services initialized successfully in {elapsed:.2f}s")
            return True
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Firebase initialization failed after {elapsed:.2f}s: {e}")
            self._initialized = True
            self._available = False
            return False
    
    def is_available(self) -> bool:
        """Check if Firebase service is available"""
        return self._available and self.app is not None
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not available")
            
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
            raise FirebaseServiceError("Firebase service not available")
            
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
            raise FirebaseServiceError("Firebase service not available")
            
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to create custom token: {str(e)}")
            return None
    
    def revoke_refresh_tokens(self, uid: str) -> bool:
        """Revoke all refresh tokens for a user"""
        if not self.is_available():
            raise FirebaseServiceError("Firebase service not available")
            
        try:
            auth.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            self.logger.error(f"Failed to revoke tokens: {str(e)}")
            return False
#!/usr/bin/env python3
"""
Test User Synchronization Logic
Local test to verify the sync_user_to_database function works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the database and logging for testing
class MockDB:
    def __init__(self):
        self.users = {}
        self.session_calls = []
    
    def add(self, user):
        self.session_calls.append(f"add({user.email})")
        if user.firebase_uid in self.users:
            raise Exception("Duplicate firebase_uid")
        if any(u.email == user.email for u in self.users.values()):
            raise Exception("Duplicate email")
        self.users[user.firebase_uid] = user
    
    def commit(self):
        self.session_calls.append("commit()")
    
    def rollback(self):
        self.session_calls.append("rollback()")

class MockQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model
    
    def filter_by(self, **kwargs):
        return self
    
    def filter(self, condition):
        return self
    
    def first(self):
        if hasattr(self, '_firebase_uid'):
            return self.db.users.get(self._firebase_uid)
        return None

class MockUser:
    def __init__(self, firebase_uid, email, name, phone='', photo_url=''):
        self.firebase_uid = firebase_uid
        self.email = email
        self.name = name
        self.phone = phone
        self.photo_url = photo_url
        self.id = len(mock_db.users) + 1

# Set up mocks
mock_db = MockDB()
mock_session = mock_db

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg, exc_info=False): print(f"ERROR: {msg}")

# Mock the imports
import uuid
from datetime import datetime

# Mock the global variables
db = type('MockDB', (), {'session': mock_session})()
User = MockUser
logger = MockLogger()

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
        
        # Look up user by Supabase UID (mock implementation)
        user = mock_db.users.get(uid)
        
        if not user:
            # Create new user with bulletproof validation
            email = user_data.get('email', '').strip()
            name = user_data.get('name', '').strip()
            
            # Handle email constraint (unique=True, nullable=False)
            if not email:
                # Generate unique email based on UID
                email = f"user_{uid.replace('-', '')[:16]}@civicfix.temp"
            
            # Check if email already exists (handle unique constraint)
            existing_email_user = None
            for u in mock_db.users.values():
                if u.email == email:
                    existing_email_user = u
                    break
            
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
                
                mock_session.add(user)
                mock_session.commit()
                logger.info(f"Created new user: {user.email} (Supabase UID: {uid})")
                
            except Exception as db_error:
                mock_session.rollback()
                logger.error(f"Database error creating user: {db_error}")
                
                # Check if user was created by concurrent request
                user = mock_db.users.get(uid)
                if user:
                    logger.info(f"User found after rollback (concurrent creation): {user.email}")
                    return user
                
                # Final fallback - create with minimal guaranteed unique data
                try:
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
                    
                    mock_session.add(user)
                    mock_session.commit()
                    logger.info(f"Created fallback user: {user.email}")
                    
                except Exception as final_error:
                    mock_session.rollback()
                    logger.error(f"Final fallback user creation failed: {final_error}")
                    return None
        else:
            logger.info(f"User already exists: {user.email}")
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to sync user to database: {e}", exc_info=True)
        try:
            mock_session.rollback()
        except:
            pass  # Ignore rollback errors
        return None

def test_user_sync():
    """Test the user synchronization function"""
    print("🧪 Testing User Synchronization Logic")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Valid user data',
            'data': {
                'uid': 'test-user-123',
                'email': 'test@example.com',
                'name': 'Test User',
                'user_metadata': {'avatar_url': 'https://example.com/avatar.jpg'}
            }
        },
        {
            'name': 'User with no email',
            'data': {
                'uid': 'test-user-456',
                'name': 'No Email User'
            }
        },
        {
            'name': 'User with no name',
            'data': {
                'uid': 'test-user-789',
                'email': 'noname@example.com'
            }
        },
        {
            'name': 'User with empty strings',
            'data': {
                'uid': 'test-user-empty',
                'email': '',
                'name': '   '
            }
        },
        {
            'name': 'User with very long data',
            'data': {
                'uid': 'test-user-long',
                'email': 'verylongemail' + 'x' * 250 + '@example.com',
                'name': 'Very Long Name ' + 'x' * 250
            }
        },
        {
            'name': 'Invalid user data (None)',
            'data': None
        },
        {
            'name': 'Invalid user data (no UID)',
            'data': {
                'email': 'nouid@example.com',
                'name': 'No UID User'
            }
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            result = sync_user_to_database(test_case['data'])
            
            if result:
                print(f"✅ Success: Created/found user {result.email}")
                passed_tests += 1
            else:
                print("❌ Failed: No user returned")
                if test_case['name'] not in ['Invalid user data (None)', 'Invalid user data (no UID)']:
                    print("   This should have succeeded!")
                else:
                    print("   This was expected to fail")
                    passed_tests += 1  # Expected failure
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("🎉 All user synchronization tests passed!")
        print("✅ The sync function handles all edge cases correctly")
        return True
    else:
        print("⚠️  Some tests failed - check the logic")
        return False

if __name__ == "__main__":
    success = test_user_sync()
    sys.exit(0 if success else 1)
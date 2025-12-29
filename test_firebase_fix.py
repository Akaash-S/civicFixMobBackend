#!/usr/bin/env python3
"""
Test Firebase Base64 credentials fix
"""

import os
import base64
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_firebase_credentials():
    """Test Firebase credentials decoding and validation"""
    print("🔥 Testing Firebase Credentials Fix")
    print("=" * 40)
    
    b64_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT_B64')
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    
    if not b64_creds or not project_id:
        print("❌ Firebase environment variables not found")
        return False
    
    try:
        # Decode Base64
        json_str = base64.b64decode(b64_creds).decode('utf-8')
        cred_dict = json.loads(json_str)
        
        print("✅ Base64 decoding successful")
        print(f"   Project ID: {cred_dict.get('project_id')}")
        print(f"   Client Email: {cred_dict.get('client_email')}")
        
        # Check private key format
        private_key = cred_dict.get('private_key', '')
        if private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("✅ Private key format looks correct")
        else:
            print("❌ Private key format is invalid")
            return False
        
        # Test Firebase initialization
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            # Clean up any existing app
            try:
                firebase_admin.delete_app(firebase_admin.get_app())
            except ValueError:
                pass
            
            # Initialize Firebase
            cred = credentials.Certificate(cred_dict)
            app = firebase_admin.initialize_app(cred)
            
            print("✅ Firebase Admin SDK initialization successful")
            
            # Test basic functionality
            from firebase_admin import auth
            try:
                auth.get_user_by_email("nonexistent@example.com")
            except firebase_admin.exceptions.FirebaseError as e:
                if "USER_NOT_FOUND" in str(e):
                    print("✅ Firebase authentication service is working")
                else:
                    print(f"⚠️ Firebase error: {e}")
            
            # Clean up
            firebase_admin.delete_app(app)
            
            return True
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Credentials validation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase_credentials()
    if success:
        print("\n🎉 Firebase credentials are working correctly!")
    else:
        print("\n❌ Firebase credentials need to be fixed")
#!/usr/bin/env python3
"""
Test app.py syntax and basic functionality
"""

import sys
import os

def test_app_syntax():
    """Test that app.py has correct syntax and can be imported"""
    
    print("🔍 Testing app.py syntax and imports...")
    
    try:
        # Test syntax by compiling
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'app.py', 'exec')
        print("✅ Syntax check passed")
        
        # Test imports
        sys.path.insert(0, '.')
        
        # Set required environment variables for testing
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        os.environ['SUPABASE_JWT_SECRET'] = 'sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE'
        
        # Skip S3 for testing by not setting AWS credentials
        if 'AWS_S3_BUCKET_NAME' in os.environ:
            del os.environ['AWS_S3_BUCKET_NAME']
        
        # Try to import the app
        import app
        print("✅ Import successful")
        
        # Test that key functions exist
        functions_to_check = [
            'get_supabase_jwt_secret',
            'verify_supabase_token', 
            'require_auth',
            'sync_user_to_database',
            'check_user_permissions'
        ]
        
        for func_name in functions_to_check:
            if hasattr(app, func_name):
                print(f"✅ Function {func_name} exists")
            else:
                print(f"❌ Function {func_name} missing")
                return False
        
        # Test JWT secret loading
        secret = app.get_supabase_jwt_secret()
        if secret:
            print(f"✅ JWT secret loaded: {secret[:20]}...")
        else:
            print("❌ JWT secret not loaded")
            return False
        
        print("\n🎉 All tests passed!")
        print("✅ app.py syntax is correct")
        print("✅ All required functions exist")
        print("✅ JWT secret is properly configured")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_app_syntax()
    sys.exit(0 if success else 1)
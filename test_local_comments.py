#!/usr/bin/env python3
"""
Test Local Comments Functionality
Test the comments system locally to identify the issue
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Comment, Issue, User
import jwt
import time

def create_test_token():
    """Create a test JWT token"""
    payload = {
        'sub': 'test-user-local',
        'email': 'local-test@civicfix.com',
        'name': 'Local Test User',
        'aud': 'authenticated',
        'role': 'authenticated',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,
        'user_metadata': {
            'full_name': 'Local Test User',
            'email': 'local-test@civicfix.com'
        }
    }
    return jwt.encode(payload, 'sb_secret_etWJpQeFCiW8bzj12DyUiw_y2N-1cQE', algorithm='HS256')

def test_local_comments():
    """Test comments functionality locally"""
    print("🧪 Testing Local Comments System")
    print("=" * 40)
    
    with app.app_context():
        # Check if tables exist
        print("1. Checking database tables...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"   Available tables: {tables}")
            
            if 'comments' in tables:
                print("   ✅ Comments table exists")
                columns = inspector.get_columns('comments')
                print("   Columns:")
                for col in columns:
                    print(f"     - {col['name']}: {col['type']}")
            else:
                print("   ❌ Comments table does not exist")
                return False
                
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return False
        
        # Test Comment model
        print("\n2. Testing Comment model...")
        try:
            # Check if we have any issues to comment on
            issue_count = Issue.query.count()
            print(f"   Issues in database: {issue_count}")
            
            if issue_count == 0:
                print("   ⚠️ No issues found, creating a test issue...")
                # Create a test user first
                test_user = User.query.filter_by(email='local-test@civicfix.com').first()
                if not test_user:
                    test_user = User(
                        firebase_uid='test-local-uid',
                        email='local-test@civicfix.com',
                        name='Local Test User'
                    )
                    db.session.add(test_user)
                    db.session.commit()
                
                # Create a test issue
                test_issue = Issue(
                    title='Test Issue for Comments',
                    description='This is a test issue',
                    category='Other',
                    latitude=0.0,
                    longitude=0.0,
                    created_by=test_user.id
                )
                db.session.add(test_issue)
                db.session.commit()
                print(f"   ✅ Created test issue with ID: {test_issue.id}")
            
            # Get first issue
            first_issue = Issue.query.first()
            print(f"   Using issue ID: {first_issue.id}")
            
            # Test getting comments
            comments = Comment.query.filter_by(issue_id=str(first_issue.id)).all()  # Convert to string
            print(f"   Existing comments: {len(comments)}")
            
            # Test creating a comment
            print("\n3. Testing comment creation...")
            test_user = User.query.first()
            if not test_user:
                print("   ❌ No users found")
                return False
            
            import uuid
            new_comment = Comment(
                id=str(uuid.uuid4()),  # Generate UUID
                text='This is a test comment',
                issue_id=str(first_issue.id),  # Convert to string
                user_id=str(test_user.id)  # Convert to string
            )
            
            db.session.add(new_comment)
            db.session.commit()
            print(f"   ✅ Comment created with ID: {new_comment.id}")
            print(f"   Comment dict: {new_comment.to_dict()}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Comment model error: {e}")
            db.session.rollback()
            return False

def test_with_flask_client():
    """Test using Flask test client"""
    print("\n4. Testing with Flask client...")
    
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"   Health endpoint: {response.status_code}")
        
        # Test comments endpoint without auth
        response = client.get('/api/v1/issues/1/comments')
        print(f"   Comments GET (no auth): {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.get_json()}")
        
        # Test with auth
        token = create_test_token()
        headers = {'Authorization': f'Bearer {token}'}
        
        response = client.get('/api/v1/issues/1/comments', headers=headers)
        print(f"   Comments GET (with auth): {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   ✅ Success: {len(data.get('comments', []))} comments")
        else:
            print(f"   ❌ Error: {response.get_json()}")

if __name__ == "__main__":
    print("🚀 Starting Local Comments Test")
    print("-" * 40)
    
    success = test_local_comments()
    
    if success:
        test_with_flask_client()
        print("\n✅ Local comments system working!")
    else:
        print("\n❌ Local comments system has issues!")
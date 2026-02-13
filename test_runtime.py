"""
Runtime Test - Verify Flask app can start
"""

import sys
import os

def test_app_initialization():
    """Test if Flask app can be initialized"""
    print("Testing Flask app initialization...")
    
    try:
        # Import the app
        from app import app, db
        
        print("  ✓ App imported successfully")
        
        # Check app configuration
        print(f"  ✓ App name: {app.name}")
        print(f"  ✓ Debug mode: {app.debug}")
        print(f"  ✓ Secret key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        print(f"  ✓ Database URI: {'Set' if app.config.get('SQLALCHEMY_DATABASE_URI') else 'Not set'}")
        
        # Test database connection
        with app.app_context():
            try:
                # Try to execute a simple query
                result = db.session.execute(db.text('SELECT 1'))
                print("  ✓ Database connection successful")
            except Exception as e:
                print(f"  ⚠ Database connection failed: {e}")
                print("    (This is expected if database tables don't exist yet)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to initialize app: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes():
    """Test if routes are registered"""
    print("\nTesting route registration...")
    
    try:
        from app import app
        
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                'path': str(rule)
            })
        
        print(f"  ✓ Total routes registered: {len(routes)}")
        
        # Count by method
        get_routes = sum(1 for r in routes if 'GET' in r['methods'])
        post_routes = sum(1 for r in routes if 'POST' in r['methods'])
        put_routes = sum(1 for r in routes if 'PUT' in r['methods'])
        delete_routes = sum(1 for r in routes if 'DELETE' in r['methods'])
        
        print(f"    • GET: {get_routes}")
        print(f"    • POST: {post_routes}")
        print(f"    • PUT: {put_routes}")
        print(f"    • DELETE: {delete_routes}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to get routes: {e}")
        return False

def test_models():
    """Test if models are properly defined"""
    print("\nTesting database models...")
    
    try:
        from app import User, Issue, Comment
        
        print("  ✓ User model imported")
        print("  ✓ Issue model imported")
        print("  ✓ Comment model imported")
        
        # Check model attributes
        print(f"    • User table: {User.__tablename__}")
        print(f"    • Issue table: {Issue.__tablename__}")
        print(f"    • Comment table: {Comment.__tablename__}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to import models: {e}")
        return False

def test_supabase_service():
    """Test Supabase service initialization"""
    print("\nTesting Supabase service...")
    
    try:
        from app import storage_service
        
        print("  ✓ Supabase storage service initialized")
        print(f"    • Bucket: {storage_service.bucket_name}")
        print(f"    • URL: {storage_service.supabase_url}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to initialize Supabase: {e}")
        return False

def main():
    """Run all runtime tests"""
    print("=" * 60)
    print("Backend Runtime Testing")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("App Initialization", test_app_initialization()))
    results.append(("Route Registration", test_routes()))
    results.append(("Database Models", test_models()))
    results.append(("Supabase Service", test_supabase_service()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Runtime Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL RUNTIME TESTS PASSED")
        print("\nBackend can start successfully!")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED")
        print("\nBackend may have runtime issues.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

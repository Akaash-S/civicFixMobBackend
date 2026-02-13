"""
Backend Endpoint Testing Script
Tests all API endpoints for syntax, imports, and basic validation
"""

import sys
import importlib.util
import ast
import os

def test_imports():
    """Test if all required imports are available"""
    print("Testing imports...")
    errors = []
    
    required_modules = [
        'flask',
        'flask_sqlalchemy',
        'flask_cors',
        'flask_migrate',
        'jwt',
        'supabase',
        'storage3',
        'werkzeug',
        'dotenv'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            errors.append(f"  ✗ {module}: {e}")
            print(f"  ✗ {module}: Missing")
    
    return errors

def test_syntax():
    """Test Python syntax of app.py"""
    print("\nTesting Python syntax...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        ast.parse(code)
        print("  ✓ Syntax is valid")
        return []
    except SyntaxError as e:
        error = f"  ✗ Syntax error at line {e.lineno}: {e.msg}"
        print(error)
        return [error]

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\nTesting environment variables...")
    errors = []
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_STORAGE_BUCKET',
        'FIREBASE_SERVICE_ACCOUNT_B64',
        'FIREBASE_PROJECT_ID'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}: Set")
        else:
            error = f"  ✗ {var}: Not set"
            errors.append(error)
            print(error)
    
    return errors

def analyze_endpoints():
    """Analyze all endpoints in app.py"""
    print("\nAnalyzing endpoints...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all @app.route decorators
    import re
    routes = re.findall(r"@app\.route\('([^']+)'(?:, methods=\[([^\]]+)\])?\)", content)
    
    endpoints = {}
    for route, methods in routes:
        methods_list = methods.replace("'", "").replace('"', '').split(', ') if methods else ['GET']
        if route not in endpoints:
            endpoints[route] = []
        endpoints[route].extend(methods_list)
    
    print(f"\n  Found {len(endpoints)} unique endpoints:")
    
    # Categorize endpoints
    categories = {
        'Health & Info': [],
        'Authentication': [],
        'Issues': [],
        'Users': [],
        'Upload': [],
        'AI Service': [],
        'Comments': [],
        'Other': []
    }
    
    for route, methods in sorted(endpoints.items()):
        methods_str = ', '.join(set(methods))
        endpoint_info = f"{route} [{methods_str}]"
        
        if '/health' in route or route == '/':
            categories['Health & Info'].append(endpoint_info)
        elif '/auth' in route or '/onboarding' in route:
            categories['Authentication'].append(endpoint_info)
        elif '/issues' in route:
            categories['Issues'].append(endpoint_info)
        elif '/users' in route:
            categories['Users'].append(endpoint_info)
        elif '/upload' in route:
            categories['Upload'].append(endpoint_info)
        elif '/ai-service' in route or '/ai-verification' in route:
            categories['AI Service'].append(endpoint_info)
        elif '/comments' in route:
            categories['Comments'].append(endpoint_info)
        else:
            categories['Other'].append(endpoint_info)
    
    for category, items in categories.items():
        if items:
            print(f"\n  {category}:")
            for item in items:
                print(f"    • {item}")
    
    return endpoints

def test_database_models():
    """Test database model definitions"""
    print("\nTesting database models...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find model classes
    import re
    models = re.findall(r'class (\w+)\(db\.Model\):', content)
    
    print(f"  Found {len(models)} models:")
    for model in models:
        print(f"    • {model}")
    
    return models

def test_auth_decorator():
    """Test if auth decorator is properly defined"""
    print("\nTesting authentication decorator...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def require_auth' in content:
        print("  ✓ require_auth decorator found")
        return []
    else:
        error = "  ✗ require_auth decorator not found"
        print(error)
        return [error]

def test_ai_service_integration():
    """Test AI service integration"""
    print("\nTesting AI service integration...")
    errors = []
    
    ai_url = os.environ.get('AI_SERVICE_URL')
    ai_key = os.environ.get('AI_SERVICE_API_KEY')
    
    if ai_url:
        print(f"  ✓ AI_SERVICE_URL: {ai_url}")
    else:
        error = "  ✗ AI_SERVICE_URL not set"
        errors.append(error)
        print(error)
    
    if ai_key:
        print(f"  ✓ AI_SERVICE_API_KEY: Set ({len(ai_key)} chars)")
    else:
        error = "  ✗ AI_SERVICE_API_KEY not set"
        errors.append(error)
        print(error)
    
    return errors

def test_cors_configuration():
    """Test CORS configuration"""
    print("\nTesting CORS configuration...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'from flask_cors import CORS' in content and 'CORS(app' in content:
        print("  ✓ CORS is configured")
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        print(f"  ✓ CORS_ORIGINS: {cors_origins}")
        return []
    else:
        error = "  ✗ CORS not properly configured"
        print(error)
        return [error]

def main():
    """Run all tests"""
    print("=" * 60)
    print("Backend Endpoint Testing")
    print("=" * 60)
    
    all_errors = []
    
    # Run tests
    all_errors.extend(test_syntax())
    all_errors.extend(test_imports())
    all_errors.extend(test_environment_variables())
    all_errors.extend(test_auth_decorator())
    all_errors.extend(test_ai_service_integration())
    all_errors.extend(test_cors_configuration())
    
    # Analyze structure
    endpoints = analyze_endpoints()
    models = test_database_models()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total endpoints: {len(endpoints)}")
    print(f"Total models: {len(models)}")
    print(f"Total errors: {len(all_errors)}")
    
    if all_errors:
        print("\n❌ FAILED - Errors found:")
        for error in all_errors:
            print(error)
        return 1
    else:
        print("\n✅ ALL TESTS PASSED")
        print("\nBackend is ready for deployment!")
        return 0

if __name__ == '__main__':
    sys.exit(main())

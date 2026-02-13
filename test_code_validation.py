"""
Backend Code Validation - No Docker Required
Tests code syntax, imports, configuration, and structure
"""

import sys
import os
import ast
import importlib.util
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, passed, message=""):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"  {message}")

def test_file_exists(filepath, description):
    """Test if a file exists"""
    exists = os.path.exists(filepath)
    print_test(f"{description} exists", exists, filepath if exists else f"Missing: {filepath}")
    return exists

def test_python_syntax(filepath):
    """Test if Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print_test(f"Syntax: {os.path.basename(filepath)}", True, "Valid Python syntax")
        return True
    except SyntaxError as e:
        print_test(f"Syntax: {os.path.basename(filepath)}", False, f"Syntax error: {e}")
        return False
    except Exception as e:
        print_test(f"Syntax: {os.path.basename(filepath)}", False, f"Error: {e}")
        return False

def test_imports(filepath):
    """Test if all imports in a file are valid"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        
        # Check if imports are available
        missing = []
        for imp in set(imports):
            if imp in ['app', 'ai_service_client', 'timeline_service']:
                continue  # Local modules
            
            try:
                spec = importlib.util.find_spec(imp)
                if spec is None:
                    missing.append(imp)
            except (ImportError, ModuleNotFoundError):
                missing.append(imp)
        
        if missing:
            print_test(f"Imports: {os.path.basename(filepath)}", False, 
                      f"Missing: {', '.join(missing)}")
            return False
        else:
            print_test(f"Imports: {os.path.basename(filepath)}", True, 
                      f"{len(set(imports))} imports available")
            return True
    except Exception as e:
        print_test(f"Imports: {os.path.basename(filepath)}", False, f"Error: {e}")
        return False

def test_requirements_file():
    """Test requirements.txt"""
    filepath = 'requirements.txt'
    
    if not os.path.exists(filepath):
        print_test("requirements.txt", False, "File not found")
        return False
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                pkg = line.split('==')[0].split('>=')[0].split('<=')[0]
                packages.append(pkg)
        
        # Check for essential packages
        essential = ['Flask', 'gunicorn', 'psycopg2-binary', 'supabase']
        missing = [pkg for pkg in essential if pkg not in packages]
        
        if missing:
            print_test("requirements.txt", False, f"Missing: {', '.join(missing)}")
            return False
        else:
            print_test("requirements.txt", True, f"{len(packages)} packages defined")
            return True
    except Exception as e:
        print_test("requirements.txt", False, f"Error: {e}")
        return False

def test_env_example():
    """Test .env.example file"""
    filepath = '.env.example'
    
    if not os.path.exists(filepath):
        print_test(".env.example", False, "File not found")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for essential variables
        essential_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        missing = [var for var in essential_vars if var not in content]
        
        if missing:
            print_test(".env.example", False, f"Missing: {', '.join(missing)}")
            return False
        else:
            print_test(".env.example", True, "All essential variables present")
            return True
    except Exception as e:
        print_test(".env.example", False, f"Error: {e}")
        return False

def test_flask_app_structure():
    """Test Flask app structure in app.py"""
    filepath = 'app.py'
    
    if not os.path.exists(filepath):
        print_test("Flask app structure", False, "app.py not found")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential Flask components
        checks = {
            'Flask app initialization': 'Flask(__name__)' in content,
            'Database setup': 'SQLAlchemy' in content,
            'CORS configuration': 'CORS' in content,
            'Route definitions': '@app.route' in content or '@app.' in content,
            'Error handling': 'try:' in content or 'except' in content,
        }
        
        all_passed = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        
        if all_passed:
            print_test("Flask app structure", True, "All components present")
            return True
        else:
            print_test("Flask app structure", False, f"Missing: {', '.join(failed)}")
            return False
    except Exception as e:
        print_test("Flask app structure", False, f"Error: {e}")
        return False

def test_database_models():
    """Test if database models are defined"""
    filepath = 'app.py'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for model definitions
        has_models = 'db.Model' in content or 'class User' in content or 'class Issue' in content
        
        if has_models:
            print_test("Database models", True, "Models defined")
            return True
        else:
            print_test("Database models", False, "No models found")
            return False
    except Exception as e:
        print_test("Database models", False, f"Error: {e}")
        return False

def test_api_routes():
    """Test if API routes are defined"""
    filepath = 'app.py'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential routes
        routes = {
            'Health check': '/health' in content,
            'API endpoints': '/api/v1/' in content,
            'Upload endpoint': '/upload' in content or 'upload' in content.lower(),
        }
        
        passed = sum(routes.values())
        total = len(routes)
        
        if passed >= 2:  # At least 2 out of 3
            print_test("API routes", True, f"{passed}/{total} route types found")
            return True
        else:
            print_test("API routes", False, f"Only {passed}/{total} route types found")
            return False
    except Exception as e:
        print_test("API routes", False, f"Error: {e}")
        return False

def test_render_config():
    """Test Render configuration files"""
    results = []
    
    # Test Procfile
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            content = f.read()
        has_gunicorn = 'gunicorn' in content
        has_app = 'app:app' in content
        results.append(('Procfile', has_gunicorn and has_app, 
                       "Valid" if has_gunicorn and has_app else "Invalid format"))
    else:
        results.append(('Procfile', False, "File not found"))
    
    # Test runtime.txt
    if os.path.exists('runtime.txt'):
        with open('runtime.txt', 'r') as f:
            content = f.read().strip()
        has_python = content.startswith('python-')
        results.append(('runtime.txt', has_python, 
                       f"Python version: {content}" if has_python else "Invalid format"))
    else:
        results.append(('runtime.txt', False, "File not found"))
    
    # Test render.yaml
    if os.path.exists('render.yaml'):
        results.append(('render.yaml', True, "Blueprint file present"))
    else:
        results.append(('render.yaml', False, "File not found"))
    
    for name, passed, msg in results:
        print_test(f"Render config: {name}", passed, msg)
    
    return all(r[1] for r in results)

def test_security():
    """Test security configurations"""
    filepath = 'app.py'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'SECRET_KEY check': 'SECRET_KEY' in content,
            'Environment variables': 'os.environ' in content or 'getenv' in content,
            'CORS configured': 'CORS' in content,
            'JWT handling': 'jwt' in content.lower() or 'JWT' in content,
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        if passed >= 3:
            print_test("Security", True, f"{passed}/{total} security features present")
            return True
        else:
            failed = [k for k, v in checks.items() if not v]
            print_test("Security", False, f"Missing: {', '.join(failed)}")
            return False
    except Exception as e:
        print_test("Security", False, f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print(f"{Colors.BLUE}Backend Code Validation - No Docker Required{Colors.RESET}")
    print("=" * 70)
    print()
    
    # Change to backend directory if needed
    if os.path.exists('backend'):
        os.chdir('backend')
        print(f"{Colors.YELLOW}Changed to backend directory{Colors.RESET}")
        print()
    
    results = []
    
    # File existence tests
    print(f"{Colors.BLUE}=== File Existence Tests ==={Colors.RESET}")
    results.append(test_file_exists('app.py', 'Main application'))
    results.append(test_file_exists('requirements.txt', 'Requirements'))
    results.append(test_file_exists('.env.example', 'Environment template'))
    results.append(test_file_exists('Procfile', 'Procfile'))
    results.append(test_file_exists('runtime.txt', 'Runtime'))
    print()
    
    # Syntax tests
    print(f"{Colors.BLUE}=== Python Syntax Tests ==={Colors.RESET}")
    if os.path.exists('app.py'):
        results.append(test_python_syntax('app.py'))
    if os.path.exists('init_db.py'):
        results.append(test_python_syntax('init_db.py'))
    if os.path.exists('ai_service_client.py'):
        results.append(test_python_syntax('ai_service_client.py'))
    print()
    
    # Import tests
    print(f"{Colors.BLUE}=== Import Tests ==={Colors.RESET}")
    if os.path.exists('app.py'):
        results.append(test_imports('app.py'))
    print()
    
    # Configuration tests
    print(f"{Colors.BLUE}=== Configuration Tests ==={Colors.RESET}")
    results.append(test_requirements_file())
    results.append(test_env_example())
    results.append(test_render_config())
    print()
    
    # Structure tests
    print(f"{Colors.BLUE}=== Structure Tests ==={Colors.RESET}")
    results.append(test_flask_app_structure())
    results.append(test_database_models())
    results.append(test_api_routes())
    results.append(test_security())
    print()
    
    # Summary
    print("=" * 70)
    print(f"{Colors.BLUE}Test Summary{Colors.RESET}")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")
    print(f"Failed: {total - passed}/{total}")
    print()
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All tests passed! Your backend code is ready.{Colors.RESET}")
        print()
        print("Next steps:")
        print("1. Push to GitHub")
        print("2. Deploy on Render")
        print("3. Test with: python test_render_deployment.py <url>")
        return 0
    elif passed >= total * 0.8:
        print(f"{Colors.YELLOW}⚠ Most tests passed ({percentage:.1f}%). Review failures above.{Colors.RESET}")
        return 1
    else:
        print(f"{Colors.RED}✗ Many tests failed ({percentage:.1f}%). Fix issues before deploying.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

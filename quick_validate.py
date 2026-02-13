"""
Quick Backend Validation - 30 Second Check
No Docker, no running server needed
"""

import os
import sys

def check(condition, name):
    """Quick check with colored output"""
    if condition:
        print(f"✓ {name}")
        return True
    else:
        print(f"✗ {name}")
        return False

print("=" * 50)
print("Quick Backend Validation")
print("=" * 50)
print()

# Change to backend directory if needed
if os.path.exists('backend'):
    os.chdir('backend')

results = []

# Essential files
print("Files:")
results.append(check(os.path.exists('app.py'), "app.py exists"))
results.append(check(os.path.exists('requirements.txt'), "requirements.txt exists"))
results.append(check(os.path.exists('Procfile'), "Procfile exists"))
results.append(check(os.path.exists('runtime.txt'), "runtime.txt exists"))
print()

# Requirements content
print("Requirements:")
if os.path.exists('requirements.txt'):
    with open('requirements.txt', 'r') as f:
        reqs = f.read()
    results.append(check('Flask' in reqs, "Flask included"))
    results.append(check('gunicorn' in reqs, "gunicorn included"))
    results.append(check('psycopg2' in reqs, "psycopg2 included"))
    results.append(check('supabase' in reqs, "supabase included"))
print()

# Procfile content
print("Procfile:")
if os.path.exists('Procfile'):
    with open('Procfile', 'r') as f:
        procfile = f.read()
    results.append(check('gunicorn' in procfile, "Uses gunicorn"))
    results.append(check('app:app' in procfile, "Correct app reference"))
print()

# App.py content
print("App Structure:")
if os.path.exists('app.py'):
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    results.append(check('Flask(__name__)' in app_content, "Flask app initialized"))
    results.append(check('SQLAlchemy' in app_content, "Database configured"))
    results.append(check('CORS' in app_content, "CORS enabled"))
    results.append(check('@app.route' in app_content or '@app.' in app_content, "Routes defined"))
print()

# Summary
print("=" * 50)
passed = sum(results)
total = len(results)
print(f"Result: {passed}/{total} checks passed")

if passed == total:
    print("✓ All checks passed! Ready to deploy.")
    sys.exit(0)
elif passed >= total * 0.8:
    print("⚠ Most checks passed. Review failures.")
    sys.exit(0)
else:
    print("✗ Many checks failed. Fix issues first.")
    sys.exit(1)

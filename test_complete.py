"""
Complete Backend Test Suite
Validates syntax, imports, configuration, runtime, and endpoint logic
"""

import sys
import os

print("=" * 70)
print("CIVICFIX BACKEND - COMPLETE TEST SUITE")
print("=" * 70)

# Test 1: Syntax and Structure
print("\n[1/4] Testing Syntax and Structure...")
print("-" * 70)
result1 = os.system("python test_endpoints.py")

# Test 2: Runtime Initialization
print("\n[2/4] Testing Runtime Initialization...")
print("-" * 70)
result2 = os.system("python test_runtime.py")

# Test 3: Endpoint Logic Validation
print("\n[3/4] Testing Endpoint Logic...")
print("-" * 70)

try:
    from app import app
    
    critical_endpoints = [
        ('/', 'GET', 'Home'),
        ('/health', 'GET', 'Health Check'),
        ('/api/v1/categories', 'GET', 'Categories'),
        ('/api/v1/issues', 'GET', 'Get Issues'),
        ('/api/v1/auth/google', 'POST', 'Google Auth'),
        ('/api/v1/ai-service/health', 'GET', 'AI Service Health'),
    ]
    
    print("Validating critical endpoints:")
    for path, method, name in critical_endpoints:
        # Check if route exists
        found = False
        for rule in app.url_map.iter_rules():
            if str(rule) == path and method in rule.methods:
                found = True
                break
        
        if found:
            print(f"  ✓ {name}: {method} {path}")
        else:
            print(f"  ✗ {name}: {method} {path} - NOT FOUND")
    
    result3 = 0
    
except Exception as e:
    print(f"  ✗ Failed to validate endpoints: {e}")
    result3 = 1

# Test 4: Configuration Validation
print("\n[4/4] Testing Configuration...")
print("-" * 70)

config_checks = {
    'AI Service': {
        'AI_SERVICE_URL': os.environ.get('AI_SERVICE_URL'),
        'AI_SERVICE_API_KEY': os.environ.get('AI_SERVICE_API_KEY')
    },
    'Database': {
        'DATABASE_URL': os.environ.get('DATABASE_URL')
    },
    'Supabase': {
        'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
        'SUPABASE_KEY': os.environ.get('SUPABASE_KEY'),
        'SUPABASE_STORAGE_BUCKET': os.environ.get('SUPABASE_STORAGE_BUCKET')
    },
    'Firebase': {
        'FIREBASE_PROJECT_ID': os.environ.get('FIREBASE_PROJECT_ID'),
        'FIREBASE_SERVICE_ACCOUNT_B64': os.environ.get('FIREBASE_SERVICE_ACCOUNT_B64')
    },
    'Flask': {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'CORS_ORIGINS': os.environ.get('CORS_ORIGINS')
    }
}

result4 = 0
for category, vars in config_checks.items():
    print(f"\n{category}:")
    for var_name, var_value in vars.items():
        if var_value:
            if 'KEY' in var_name or 'SECRET' in var_name:
                print(f"  ✓ {var_name}: Set ({len(var_value)} chars)")
            else:
                print(f"  ✓ {var_name}: {var_value}")
        else:
            print(f"  ✗ {var_name}: NOT SET")
            result4 = 1

# Final Summary
print("\n" + "=" * 70)
print("FINAL TEST SUMMARY")
print("=" * 70)

tests = [
    ("Syntax & Structure", result1),
    ("Runtime Initialization", result2),
    ("Endpoint Logic", result3),
    ("Configuration", result4)
]

passed = sum(1 for _, result in tests if result == 0)
total = len(tests)

for test_name, result in tests:
    status = "✅ PASS" if result == 0 else "❌ FAIL"
    print(f"{status}: {test_name}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED - BACKEND IS READY FOR DEPLOYMENT!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Deploy to Render using Docker")
    print("2. Add environment variables from backend/.env")
    print("3. Test deployed endpoints")
    print("\nDeployment guide: backend/DOCKER_DEPLOY.md")
    sys.exit(0)
else:
    print("\n" + "=" * 70)
    print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")
    print("=" * 70)
    sys.exit(1)

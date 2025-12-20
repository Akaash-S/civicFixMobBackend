#!/usr/bin/env python3
"""
Test WSGI Application
Verifies that the WSGI application works correctly
"""

import os
import sys
from run import application

def test_wsgi_interface():
    """Test WSGI interface"""
    print("Testing WSGI interface...")
    
    # Mock WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/health',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '5000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': True,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    # Mock start_response
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    try:
        # Test WSGI call
        result = application(environ, start_response)
        
        print(f"✓ WSGI call successful")
        print(f"✓ Application type: {type(application)}")
        print(f"✓ Response status: {response_data.get('status', 'Not set')}")
        print(f"✓ Response headers count: {len(response_data.get('headers', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ WSGI call failed: {e}")
        return False

def test_application_import():
    """Test application import"""
    print("\nTesting application import...")
    
    try:
        from run import application
        
        print(f"✓ Import successful")
        print(f"✓ Application type: {type(application)}")
        print(f"✓ Is callable: {callable(application)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def main():
    """Run WSGI tests"""
    print("=" * 50)
    print("WSGI Application Test")
    print("=" * 50)
    
    tests = [
        ("Application Import", test_application_import),
        ("WSGI Interface", test_wsgi_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name}: PASSED\n")
            else:
                print(f"✗ {test_name}: FAILED\n")
        except Exception as e:
            print(f"✗ {test_name}: ERROR - {e}\n")
    
    print("=" * 50)
    print(f"WSGI Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 WSGI application is ready for Gunicorn!")
        return True
    else:
        print("⚠️  Some WSGI tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
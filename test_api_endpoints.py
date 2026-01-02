#!/usr/bin/env python3
"""
CivicFix API Endpoint Testing Script
Comprehensive testing of all API endpoints on https://civicfix-server.asolvitra.tech
"""

import requests
import json
import time
import ssl
import socket
from datetime import datetime
from urllib.parse import urljoin
import sys

# Configuration
BASE_URL = "https://civicfix-server.asolvitra.tech"
DOMAIN = "civicfix-server.asolvitra.tech"
TIMEOUT = 30

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    RESET = '\033[0m'

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'tests': []
        }
        
    def log(self, message, color=Colors.WHITE):
        """Print colored log message"""
        print(f"{color}{message}{Colors.RESET}")
        
    def test_endpoint(self, method, endpoint, description, expected_status=200, 
                     headers=None, data=None, auth_token=None):
        """Test a single API endpoint"""
        url = urljoin(self.base_url, endpoint)
        test_headers = headers or {}
        
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'
            
        if data and method in ['POST', 'PUT']:
            test_headers['Content-Type'] = 'application/json'
            
        print(f"\n🧪 Testing {method} {endpoint}")
        print(f"   Description: {description}")
        print(f"   URL: {url}")
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = self.session.get(url, headers=test_headers)
            elif method == 'POST':
                response = self.session.post(url, headers=test_headers, 
                                           json=data if data else None)
            elif method == 'PUT':
                response = self.session.put(url, headers=test_headers, 
                                          json=data if data else None)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers)
            elif method == 'OPTIONS':
                response = self.session.options(url, headers=test_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            # Check status code
            if response.status_code == expected_status:
                self.log(f"   ✅ PASS - Status: {response.status_code} ({response_time}ms)", Colors.GREEN)
                self.results['passed'] += 1
                status = 'PASS'
            else:
                self.log(f"   ❌ FAIL - Expected: {expected_status}, Got: {response.status_code}", Colors.RED)
                self.results['failed'] += 1
                status = 'FAIL'
                
            # Try to parse JSON response
            try:
                json_response = response.json()
                print(f"   📄 Response: {json.dumps(json_response, indent=2)[:200]}...")
            except:
                if response.text:
                    print(f"   📄 Response: {response.text[:200]}...")
                else:
                    print(f"   📄 Response: (empty)")
                    
            # Store test result
            self.results['tests'].append({
                'method': method,
                'endpoint': endpoint,
                'description': description,
                'status': status,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'response_time': response_time,
                'url': url
            })
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.log(f"   ❌ ERROR - {str(e)}", Colors.RED)
            self.results['failed'] += 1
            self.results['tests'].append({
                'method': method,
                'endpoint': endpoint,
                'description': description,
                'status': 'ERROR',
                'error': str(e),
                'url': url
            })
            return None
            
    def test_ssl_certificate(self):
        """Test SSL certificate validity"""
        print(f"\n🔒 Testing SSL Certificate")
        try:
            context = ssl.create_default_context()
            with socket.create_connection((DOMAIN, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=DOMAIN) as ssock:
                    cert = ssock.getpeercert()
                    
            self.log(f"   ✅ SSL Certificate Valid", Colors.GREEN)
            print(f"   📜 Subject: {dict(x[0] for x in cert['subject'])}")
            print(f"   📅 Valid until: {cert['notAfter']}")
            self.results['passed'] += 1
            
        except Exception as e:
            self.log(f"   ❌ SSL Certificate Error: {str(e)}", Colors.RED)
            self.results['failed'] += 1
            
    def test_http_redirect(self):
        """Test HTTP to HTTPS redirect"""
        print(f"\n🔄 Testing HTTP to HTTPS Redirect")
        try:
            http_url = f"http://{DOMAIN}/"
            response = requests.get(http_url, allow_redirects=False, timeout=10)
            
            if response.status_code == 301:
                location = response.headers.get('Location', '')
                if location.startswith('https://'):
                    self.log(f"   ✅ PASS - 301 redirect to HTTPS", Colors.GREEN)
                    self.results['passed'] += 1
                else:
                    self.log(f"   ⚠️  WARNING - 301 but not to HTTPS: {location}", Colors.YELLOW)
                    self.results['warnings'] += 1
            else:
                self.log(f"   ❌ FAIL - Expected 301, got {response.status_code}", Colors.RED)
                self.results['failed'] += 1
                
        except Exception as e:
            self.log(f"   ❌ ERROR - {str(e)}", Colors.RED)
            self.results['failed'] += 1
            
    def run_basic_tests(self):
        """Run basic connectivity and health tests"""
        self.log("\n🌐 Basic Connectivity Tests", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Test home endpoint
        self.test_endpoint('GET', '/', 'Home endpoint')
        
        # Test health check
        self.test_endpoint('GET', '/health', 'Backend health check')
        
        # Test Nginx health check
        self.test_endpoint('GET', '/nginx-health', 'Nginx health check')
        
    def run_public_api_tests(self):
        """Run tests for public API endpoints (no auth required)"""
        self.log("\n📊 Public API Endpoints", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Get all issues
        self.test_endpoint('GET', '/api/v1/issues', 'Get all issues')
        
        # Get categories
        self.test_endpoint('GET', '/api/v1/categories', 'Get issue categories')
        
        # Get status options
        self.test_endpoint('GET', '/api/v1/status-options', 'Get status options')
        
        # Get priority options
        self.test_endpoint('GET', '/api/v1/priority-options', 'Get priority options')
        
        # Get system statistics
        self.test_endpoint('GET', '/api/v1/stats', 'Get system statistics')
        
        # Get nearby issues (with sample coordinates)
        self.test_endpoint('GET', '/api/v1/issues/nearby?lat=12.9716&lng=77.5946&radius=5', 
                          'Get nearby issues')
        
        # Try to get a specific issue (ID 1)
        self.test_endpoint('GET', '/api/v1/issues/1', 'Get specific issue (ID 1)', 
                          expected_status=200)  # Might be 404 if no issues exist
        
    def run_auth_tests(self):
        """Run tests for authentication-required endpoints"""
        self.log("\n🔐 Authentication Required Endpoints", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # These should fail with 401 without authentication
        self.test_endpoint('GET', '/api/v1/users/me', 'Get current user (no auth)', 
                          expected_status=401)
        
        self.test_endpoint('GET', '/api/v1/auth/test', 'Test authentication (no auth)', 
                          expected_status=401)
        
        self.test_endpoint('POST', '/api/v1/issues', 'Create issue (no auth)', 
                          expected_status=401)
        
        self.test_endpoint('POST', '/api/v1/upload', 'Upload file (no auth)', 
                          expected_status=401)
        
    def run_error_handling_tests(self):
        """Run tests for error handling"""
        self.log("\n🧪 Error Handling Tests", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Non-existent endpoint
        self.test_endpoint('GET', '/api/v1/nonexistent', 'Non-existent endpoint', 
                          expected_status=404)
        
        # Invalid issue ID
        self.test_endpoint('GET', '/api/v1/issues/99999', 'Invalid issue ID', 
                          expected_status=404)
        
        # Invalid method
        self.test_endpoint('DELETE', '/', 'Invalid method on home endpoint', 
                          expected_status=405)
        
    def run_security_tests(self):
        """Run security and performance tests"""
        self.log("\n🔒 Security & Performance Tests", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Test SSL certificate
        self.test_ssl_certificate()
        
        # Test HTTP redirect
        self.test_http_redirect()
        
        # Test CORS
        cors_headers = {
            'Origin': 'https://example.com',
            'Access-Control-Request-Method': 'GET'
        }
        response = self.test_endpoint('OPTIONS', '/api/v1/issues', 'CORS preflight test', 
                                    expected_status=200, headers=cors_headers)
        
        # Test security headers
        print(f"\n🛡️  Testing Security Headers")
        response = self.test_endpoint('GET', '/', 'Security headers check')
        if response:
            security_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options', 
                'X-XSS-Protection',
                'Referrer-Policy'
            ]
            
            for header in security_headers:
                if header in response.headers:
                    self.log(f"   ✅ {header}: {response.headers[header]}", Colors.GREEN)
                else:
                    self.log(f"   ⚠️  Missing: {header}", Colors.YELLOW)
                    self.results['warnings'] += 1
                    
    def run_performance_tests(self):
        """Run basic performance tests"""
        self.log("\n⚡ Performance Tests", Colors.CYAN)
        self.log("=" * 50, Colors.CYAN)
        
        # Test response time
        print(f"\n⏱️  Testing Response Times")
        endpoints = ['/health', '/api/v1/issues', '/api/v1/categories']
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.session.get(urljoin(self.base_url, endpoint))
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response_time < 1000:  # Less than 1 second
                self.log(f"   ✅ {endpoint}: {response_time}ms", Colors.GREEN)
            elif response_time < 3000:  # Less than 3 seconds
                self.log(f"   ⚠️  {endpoint}: {response_time}ms (slow)", Colors.YELLOW)
                self.results['warnings'] += 1
            else:
                self.log(f"   ❌ {endpoint}: {response_time}ms (very slow)", Colors.RED)
                self.results['failed'] += 1
                
    def print_summary(self):
        """Print test summary"""
        self.log("\n📋 Test Summary", Colors.WHITE)
        self.log("=" * 50, Colors.WHITE)
        
        total_tests = self.results['passed'] + self.results['failed']
        
        self.log(f"Total Tests: {total_tests}", Colors.WHITE)
        self.log(f"✅ Passed: {self.results['passed']}", Colors.GREEN)
        self.log(f"❌ Failed: {self.results['failed']}", Colors.RED)
        self.log(f"⚠️  Warnings: {self.results['warnings']}", Colors.YELLOW)
        
        if self.results['failed'] == 0:
            self.log(f"\n🎉 All tests passed!", Colors.GREEN)
        else:
            self.log(f"\n⚠️  Some tests failed. Check the details above.", Colors.YELLOW)
            
        # Print useful URLs
        self.log(f"\n🔗 Useful URLs:", Colors.CYAN)
        urls = [
            f"{BASE_URL}/",
            f"{BASE_URL}/health", 
            f"{BASE_URL}/api/v1/issues",
            f"{BASE_URL}/api/v1/categories",
            f"{BASE_URL}/api/v1/stats"
        ]
        
        for url in urls:
            print(f"   • {url}")
            
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'summary': {
                    'total': total_tests,
                    'passed': self.results['passed'],
                    'failed': self.results['failed'],
                    'warnings': self.results['warnings']
                },
                'tests': self.results['tests']
            }, f, indent=2)
            
        self.log(f"\n📄 Detailed results saved to: {results_file}", Colors.BLUE)
        
    def run_all_tests(self):
        """Run all test suites"""
        self.log(f"🚀 CivicFix API Testing Suite", Colors.WHITE)
        self.log(f"=" * 50, Colors.WHITE)
        self.log(f"Base URL: {self.base_url}", Colors.WHITE)
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)
        
        try:
            self.run_basic_tests()
            self.run_public_api_tests()
            self.run_auth_tests()
            self.run_error_handling_tests()
            self.run_security_tests()
            self.run_performance_tests()
            
        except KeyboardInterrupt:
            self.log(f"\n⚠️  Testing interrupted by user", Colors.YELLOW)
        except Exception as e:
            self.log(f"\n❌ Unexpected error: {str(e)}", Colors.RED)
        finally:
            self.print_summary()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
        
    tester = APITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
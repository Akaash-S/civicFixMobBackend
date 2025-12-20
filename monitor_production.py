#!/usr/bin/env python3
"""
Production Monitoring Script for CivicFix Backend
Monitors application health, performance, and logs alerts
"""

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class ProductionMonitor:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.container_name = "civicfix-backend-prod"
        self.log_file = Path("logs/monitor.log")
        self.alert_file = Path("logs/alerts.log")
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup monitoring logging"""
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('monitor')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_alert(self, message):
        """Log alert to separate file"""
        with open(self.alert_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - ALERT: {message}\n")
        self.logger.error(f"ALERT: {message}")
    
    def check_health(self):
        """Check application health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, "Health check passed"
                else:
                    return False, f"Unhealthy status: {data}"
            else:
                return False, f"Health check failed with status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Health check request failed: {str(e)}"
    
    def check_container_status(self):
        """Check Docker container status"""
        try:
            result = subprocess.run([
                'docker', 'ps', '-f', f'name={self.container_name}', 
                '--format', '{{.Status}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                if 'Up' in status:
                    return True, f"Container running: {status}"
                else:
                    return False, f"Container not running: {status}"
            else:
                return False, "Container not found"
                
        except subprocess.TimeoutExpired:
            return False, "Container status check timed out"
        except Exception as e:
            return False, f"Container status check failed: {str(e)}"
    
    def check_database_connection(self):
        """Check database connectivity through API"""
        try:
            # Try to access an endpoint that requires database
            response = requests.get(f"{self.base_url}/api/v1/issues", timeout=10)
            
            if response.status_code in [200, 401]:  # 401 is OK (auth required)
                return True, "Database connection OK"
            else:
                return False, f"Database check failed with status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Database check request failed: {str(e)}"
    
    def check_memory_usage(self):
        """Check container memory usage"""
        try:
            result = subprocess.run([
                'docker', 'stats', self.container_name, '--no-stream', 
                '--format', '{{.MemUsage}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                mem_usage = result.stdout.strip()
                return True, f"Memory usage: {mem_usage}"
            else:
                return False, "Could not get memory usage"
                
        except subprocess.TimeoutExpired:
            return False, "Memory check timed out"
        except Exception as e:
            return False, f"Memory check failed: {str(e)}"
    
    def get_container_logs(self, lines=50):
        """Get recent container logs"""
        try:
            result = subprocess.run([
                'docker', 'logs', '--tail', str(lines), self.container_name
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error getting logs: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Log retrieval timed out"
        except Exception as e:
            return f"Log retrieval failed: {str(e)}"
    
    def run_health_checks(self):
        """Run all health checks"""
        checks = [
            ("Container Status", self.check_container_status),
            ("Health Endpoint", self.check_health),
            ("Database Connection", self.check_database_connection),
            ("Memory Usage", self.check_memory_usage),
        ]
        
        results = {}
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                results[check_name] = {
                    'passed': passed,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                if passed:
                    self.logger.info(f"✓ {check_name}: {message}")
                else:
                    self.logger.error(f"✗ {check_name}: {message}")
                    self.log_alert(f"{check_name} failed: {message}")
                    all_passed = False
                    
            except Exception as e:
                error_msg = f"Check failed with exception: {str(e)}"
                results[check_name] = {
                    'passed': False,
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                self.logger.error(f"✗ {check_name}: {error_msg}")
                self.log_alert(f"{check_name} exception: {error_msg}")
                all_passed = False
        
        return all_passed, results
    
    def monitor_continuous(self, interval=60):
        """Run continuous monitoring"""
        self.logger.info("Starting continuous monitoring...")
        self.logger.info(f"Check interval: {interval} seconds")
        
        consecutive_failures = 0
        max_failures = 3
        
        try:
            while True:
                self.logger.info("Running health checks...")
                
                all_passed, results = self.run_health_checks()
                
                if all_passed:
                    consecutive_failures = 0
                    self.logger.info("All health checks passed ✓")
                else:
                    consecutive_failures += 1
                    self.logger.error(f"Health checks failed ({consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        self.log_alert(f"Critical: {consecutive_failures} consecutive failures detected!")
                        
                        # Get recent logs for debugging
                        logs = self.get_container_logs(100)
                        self.logger.error("Recent container logs:")
                        self.logger.error(logs)
                
                # Wait for next check
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.log_alert(f"Monitoring crashed: {str(e)}")
            raise
    
    def run_single_check(self):
        """Run a single health check"""
        self.logger.info("Running single health check...")
        
        all_passed, results = self.run_health_checks()
        
        # Print summary
        print("\n" + "="*50)
        print("HEALTH CHECK SUMMARY")
        print("="*50)
        
        for check_name, result in results.items():
            status = "PASS" if result['passed'] else "FAIL"
            print(f"{check_name:20} [{status}] {result['message']}")
        
        print("="*50)
        
        if all_passed:
            print("Overall Status: HEALTHY ✓")
            return 0
        else:
            print("Overall Status: UNHEALTHY ✗")
            return 1

def main():
    """Main monitoring function"""
    monitor = ProductionMonitor()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'continuous':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            monitor.monitor_continuous(interval)
        elif command == 'check':
            sys.exit(monitor.run_single_check())
        elif command == 'logs':
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            print(monitor.get_container_logs(lines))
        else:
            print("Usage: python monitor_production.py {continuous|check|logs} [options]")
            print("")
            print("Commands:")
            print("  continuous [interval] - Run continuous monitoring (default: 60s)")
            print("  check                 - Run single health check")
            print("  logs [lines]          - Show container logs (default: 50 lines)")
            sys.exit(1)
    else:
        # Default: run single check
        sys.exit(monitor.run_single_check())

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Fix RDS Connection Issues
This script diagnoses and provides solutions for RDS connection problems
"""

import os
import boto3
import socket
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_current_ip():
    """Get current public IP address"""
    try:
        import requests
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return None

def test_rds_connectivity():
    """Test RDS connectivity and diagnose issues"""
    print("=" * 60)
    print("RDS Connection Diagnostics")
    print("=" * 60)
    
    # Get configuration
    db_host = "civicfix-db.ctousuwme9up.ap-south-1.rds.amazonaws.com"
    db_port = 5432
    db_name = "civicfix-db"
    db_user = "civicfix_admin"
    
    # Test both password variants
    passwords = ["CivicFixAdmin2025", "CivixFixAdmin2025"]
    
    print(f"Testing connection to: {db_host}:{db_port}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    
    # Get current IP
    current_ip = get_current_ip()
    if current_ip:
        print(f"Your current IP: {current_ip}")
    else:
        print("Could not determine your IP address")
    
    print("\n1. Testing network connectivity...")
    
    # Test network connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((db_host, db_port))
        sock.close()
        
        if result == 0:
            print("✓ Network connectivity: OK")
        else:
            print("✗ Network connectivity: FAILED")
            print("  - Check if RDS instance is running")
            print("  - Verify security group allows inbound connections on port 5432")
            return False
    except Exception as e:
        print(f"✗ Network test failed: {e}")
        return False
    
    print("\n2. Testing database authentication...")
    
    # Test database connection with different passwords
    for i, password in enumerate(passwords, 1):
        print(f"\nTrying password variant {i}: {password}")
        
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=password,
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()
            
            print(f"✓ Authentication successful with password: {password}")
            print(f"✓ PostgreSQL version: {version[0]}")
            
            cursor.close()
            conn.close()
            
            # Update .env file with correct password
            update_env_password(password)
            return True
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            print(f"✗ Authentication failed: {error_msg}")
            
            if "password authentication failed" in error_msg:
                print("  - Password is incorrect")
            elif "no pg_hba.conf entry" in error_msg:
                print("  - Security group doesn't allow your IP address")
                if current_ip:
                    print(f"  - Add inbound rule for IP: {current_ip}/32")
            elif "timeout" in error_msg:
                print("  - Connection timeout - check network/firewall")
    
    return False

def update_env_password(correct_password):
    """Update .env file with correct password"""
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Update the password in the DATABASE_URL
        old_url = f"postgresql://civicfix_admin:CivixFixAdmin2025@"
        new_url = f"postgresql://civicfix_admin:{correct_password}@"
        content = content.replace(old_url, new_url)
        
        # Update the DB_PASSWORD line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('DB_PASSWORD='):
                lines[i] = f'DB_PASSWORD={correct_password}'
        
        with open('.env', 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✓ Updated .env file with correct password: {correct_password}")
        
    except Exception as e:
        print(f"✗ Failed to update .env file: {e}")

def fix_security_group():
    """Attempt to fix RDS security group"""
    print("\n3. Checking RDS security group...")
    
    try:
        # Get current IP
        current_ip = get_current_ip()
        if not current_ip:
            print("✗ Cannot determine your IP address")
            return False
        
        # Initialize AWS clients
        ec2 = boto3.client('ec2', region_name='ap-south-1')
        rds = boto3.client('rds', region_name='ap-south-1')
        
        # Get RDS instance details
        response = rds.describe_db_instances(DBInstanceIdentifier='civicfix-db')
        db_instance = response['DBInstances'][0]
        
        # Get security groups
        security_groups = db_instance['VpcSecurityGroups']
        
        for sg in security_groups:
            sg_id = sg['VpcSecurityGroupId']
            print(f"Checking security group: {sg_id}")
            
            # Get security group rules
            sg_response = ec2.describe_security_groups(GroupIds=[sg_id])
            sg_details = sg_response['SecurityGroups'][0]
            
            # Check if PostgreSQL port is open for current IP
            has_rule = False
            for rule in sg_details['IpPermissions']:
                if rule.get('FromPort') == 5432:
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range['CidrIp'] == f"{current_ip}/32" or ip_range['CidrIp'] == '0.0.0.0/0':
                            has_rule = True
                            print(f"✓ Found rule allowing access from {ip_range['CidrIp']}")
            
            if not has_rule:
                print(f"✗ No rule found for your IP: {current_ip}")
                print("Adding security group rule...")
                
                try:
                    ec2.authorize_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=[
                            {
                                'IpProtocol': 'tcp',
                                'FromPort': 5432,
                                'ToPort': 5432,
                                'IpRanges': [
                                    {
                                        'CidrIp': f'{current_ip}/32',
                                        'Description': f'PostgreSQL access from {current_ip}'
                                    }
                                ]
                            }
                        ]
                    )
                    print(f"✓ Added security group rule for {current_ip}/32")
                    return True
                    
                except Exception as e:
                    if 'InvalidPermission.Duplicate' in str(e):
                        print("✓ Rule already exists")
                        return True
                    else:
                        print(f"✗ Failed to add rule: {e}")
                        return False
        
        return True
        
    except Exception as e:
        print(f"✗ Security group check failed: {e}")
        print("Manual steps:")
        print("1. Go to AWS EC2 Console > Security Groups")
        print("2. Find the security group attached to your RDS instance")
        print("3. Add inbound rule:")
        print("   - Type: PostgreSQL")
        print("   - Port: 5432")
        if current_ip:
            print(f"   - Source: {current_ip}/32")
        else:
            print("   - Source: Your IP address/32")
        return False

def main():
    """Main function"""
    print("CivicFix RDS Connection Fixer")
    print("This script will diagnose and fix RDS connection issues")
    print()
    
    # Test connectivity
    if test_rds_connectivity():
        print("\n" + "=" * 60)
        print("SUCCESS: RDS connection is working!")
        print("=" * 60)
        print("You can now use PostgreSQL in your application.")
        print("Update your .env file to use the PostgreSQL DATABASE_URL")
        return True
    
    # Try to fix security group
    print("\nAttempting to fix security group...")
    if fix_security_group():
        print("\nSecurity group updated. Waiting 30 seconds for changes to take effect...")
        import time
        time.sleep(30)
        
        # Test again
        if test_rds_connectivity():
            print("\n" + "=" * 60)
            print("SUCCESS: RDS connection fixed!")
            print("=" * 60)
            return True
    
    print("\n" + "=" * 60)
    print("MANUAL INTERVENTION REQUIRED")
    print("=" * 60)
    print("Please check the following:")
    print("1. RDS instance is running and publicly accessible")
    print("2. Security group allows inbound connections on port 5432")
    print("3. Database credentials are correct")
    print("4. Your IP address is whitelisted")
    print()
    print("For now, the application will use SQLite for development.")
    
    return False

if __name__ == "__main__":
    main()
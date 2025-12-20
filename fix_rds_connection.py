#!/usr/bin/env python3
"""
RDS Connection Troubleshooting and Fix Script
Diagnoses and fixes common RDS connection issues
"""

import boto3
import socket
import os
from dotenv import load_dotenv

load_dotenv()

def test_network_connectivity(host, port=5432):
    """Test if we can reach the RDS endpoint"""
    print(f"\nTesting network connectivity to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"SUCCESS: Port {port} is reachable")
            return True
        else:
            print(f"FAILED: Port {port} is not reachable (Error code: {result})")
            return False
    except socket.gaierror:
        print(f"FAILED: Could not resolve hostname {host}")
        return False
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def check_rds_instance():
    """Check RDS instance status"""
    print("\nChecking RDS instance status...")
    try:
        rds = boto3.client('rds', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        
        # Get DB instance identifier from endpoint
        db_endpoint = os.getenv('DB_HOST', '')
        db_identifier = db_endpoint.split('.')[0] if db_endpoint else 'civicfix-db'
        
        response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
        db_instance = response['DBInstances'][0]
        
        print(f"Instance ID: {db_instance['DBInstanceIdentifier']}")
        print(f"Status: {db_instance['DBInstanceStatus']}")
        print(f"Endpoint: {db_instance['Endpoint']['Address']}:{db_instance['Endpoint']['Port']}")
        print(f"Publicly Accessible: {db_instance['PubliclyAccessible']}")
        print(f"VPC: {db_instance['DBSubnetGroup']['VpcId']}")
        
        # Check security groups
        print(f"\nSecurity Groups:")
        for sg in db_instance['VpcSecurityGroups']:
            print(f"  - {sg['VpcSecurityGroupId']} ({sg['Status']})")
        
        return db_instance
        
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return None

def check_security_group(db_instance):
    """Check security group rules"""
    print("\nChecking security group rules...")
    try:
        ec2 = boto3.client('ec2', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        
        for sg in db_instance['VpcSecurityGroups']:
            sg_id = sg['VpcSecurityGroupId']
            response = ec2.describe_security_groups(GroupIds=[sg_id])
            
            print(f"\nSecurity Group: {sg_id}")
            
            has_postgres_rule = False
            for rule in response['SecurityGroups'][0]['IpPermissions']:
                if rule.get('FromPort') == 5432:
                    has_postgres_rule = True
                    print(f"  PostgreSQL Rule Found:")
                    print(f"    Port: {rule['FromPort']}-{rule['ToPort']}")
                    for ip_range in rule.get('IpRanges', []):
                        print(f"    Allowed from: {ip_range['CidrIp']}")
            
            if not has_postgres_rule:
                print(f"  WARNING: No PostgreSQL (port 5432) inbound rule found!")
                return False
            
        return True
        
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def fix_security_group(db_instance):
    """Add PostgreSQL inbound rule to security group"""
    print("\nAttempting to fix security group...")
    try:
        ec2 = boto3.client('ec2', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        
        sg_id = db_instance['VpcSecurityGroups'][0]['VpcSecurityGroupId']
        
        # Add inbound rule for PostgreSQL
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 5432,
                    'ToPort': 5432,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'PostgreSQL access from anywhere'}]
                }
            ]
        )
        
        print(f"SUCCESS: Added PostgreSQL inbound rule to {sg_id}")
        print("Note: Allowing 0.0.0.0/0 is not recommended for production!")
        print("Consider restricting to your IP address for better security.")
        return True
        
    except Exception as e:
        if 'InvalidPermission.Duplicate' in str(e):
            print("Rule already exists")
            return True
        else:
            print(f"FAILED: {str(e)}")
            return False

def get_my_ip():
    """Get current public IP"""
    try:
        import requests
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip = response.json()['ip']
        print(f"\nYour public IP: {ip}")
        return ip
    except:
        print("\nCould not determine your public IP")
        return None

def test_database_connection():
    """Test actual database connection"""
    print("\nTesting database connection...")
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"SUCCESS: Connected to PostgreSQL")
        print(f"Version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("RDS Connection Troubleshooting Tool")
    print("=" * 60)
    
    # Check environment variables
    print("\nChecking environment variables...")
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("Please configure your .env file")
        return False
    
    print("All required environment variables are set")
    
    # Get your public IP
    my_ip = get_my_ip()
    
    # Test network connectivity
    db_host = os.getenv('DB_HOST')
    if not test_network_connectivity(db_host):
        print("\nDIAGNOSIS: Cannot reach RDS endpoint")
        print("\nPossible causes:")
        print("1. RDS instance is not running")
        print("2. Security group is blocking connections")
        print("3. RDS is not publicly accessible")
        print("4. Network/firewall issues")
        
        # Check RDS instance
        db_instance = check_rds_instance()
        if db_instance:
            # Check if publicly accessible
            if not db_instance['PubliclyAccessible']:
                print("\nERROR: RDS instance is not publicly accessible!")
                print("You need to modify the instance to allow public access:")
                print("1. Go to AWS RDS Console")
                print("2. Select your instance")
                print("3. Click 'Modify'")
                print("4. Under 'Connectivity', set 'Public access' to 'Yes'")
                print("5. Apply changes")
                return False
            
            # Check security group
            if not check_security_group(db_instance):
                print("\nAttempting to fix security group...")
                if fix_security_group(db_instance):
                    print("\nSecurity group fixed! Please wait 30 seconds and try again.")
                    return True
                else:
                    print("\nCould not fix security group automatically.")
                    print("Please add the rule manually:")
                    print("1. Go to AWS EC2 Console > Security Groups")
                    print(f"2. Find security group: {db_instance['VpcSecurityGroups'][0]['VpcSecurityGroupId']}")
                    print("3. Add inbound rule:")
                    print("   - Type: PostgreSQL")
                    print("   - Port: 5432")
                    if my_ip:
                        print(f"   - Source: {my_ip}/32 (your IP)")
                    else:
                        print("   - Source: 0.0.0.0/0 (anywhere - not recommended for production)")
                    return False
    else:
        print("\nNetwork connectivity OK!")
        
        # Test database connection
        if test_database_connection():
            print("\n" + "=" * 60)
            print("SUCCESS: RDS connection is working!")
            print("=" * 60)
            print("\nYou can now start your backend:")
            print("  python run.py")
            return True
        else:
            print("\nDIAGNOSIS: Can reach RDS but authentication failed")
            print("\nPossible causes:")
            print("1. Incorrect database credentials")
            print("2. Database does not exist")
            print("3. User does not have permissions")
            print("\nPlease verify your .env file settings:")
            print(f"  DB_HOST: {os.getenv('DB_HOST')}")
            print(f"  DB_NAME: {os.getenv('DB_NAME')}")
            print(f"  DB_USER: {os.getenv('DB_USER')}")
            print(f"  DB_PASSWORD: [hidden]")
            return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n" + "=" * 60)
            print("TEMPORARY SOLUTION: Use SQLite for development")
            print("=" * 60)
            print("\nEdit your .env file and change:")
            print("  DATABASE_URL=sqlite:///civicfix.db")
            print("\nThis will allow you to develop locally while fixing RDS.")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()

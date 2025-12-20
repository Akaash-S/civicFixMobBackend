#!/usr/bin/env python3
"""
AWS RDS Setup Script for CivicFix
Creates and configures PostgreSQL RDS instance
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError

class RDSSetup:
    def __init__(self):
        self.rds_client = boto3.client('rds')
        self.ec2_client = boto3.client('ec2')
        
    def create_security_group(self):
        """Create security group for RDS"""
        try:
            # Create security group
            response = self.ec2_client.create_security_group(
                GroupName='civicfix-rds-sg',
                Description='Security group for CivicFix RDS instance'
            )
            
            security_group_id = response['GroupId']
            print(f"✅ Created security group: {security_group_id}")
            
            # Add inbound rule for PostgreSQL
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 5432,
                        'ToPort': 5432,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'PostgreSQL access'}]
                    }
                ]
            )
            
            print("✅ Added PostgreSQL inbound rule")
            return security_group_id
            
        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                print("⚠️  Security group already exists")
                # Get existing security group
                response = self.ec2_client.describe_security_groups(
                    GroupNames=['civicfix-rds-sg']
                )
                return response['SecurityGroups'][0]['GroupId']
            else:
                print(f"❌ Error creating security group: {e}")
                return None
    
    def create_db_subnet_group(self):
        """Create DB subnet group"""
        try:
            # Get default VPC subnets
            vpcs = self.ec2_client.describe_vpcs(
                Filters=[{'Name': 'is-default', 'Values': ['true']}]
            )
            
            if not vpcs['Vpcs']:
                print("❌ No default VPC found")
                return None
            
            vpc_id = vpcs['Vpcs'][0]['VpcId']
            
            # Get subnets in different AZs
            subnets = self.ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets'][:2]]
            
            if len(subnet_ids) < 2:
                print("❌ Need at least 2 subnets in different AZs")
                return None
            
            # Create DB subnet group
            self.rds_client.create_db_subnet_group(
                DBSubnetGroupName='civicfix-subnet-group',
                DBSubnetGroupDescription='Subnet group for CivicFix RDS',
                SubnetIds=subnet_ids
            )
            
            print("✅ Created DB subnet group")
            return 'civicfix-subnet-group'
            
        except ClientError as e:
            if 'DBSubnetGroupAlreadyExists' in str(e):
                print("⚠️  DB subnet group already exists")
                return 'civicfix-subnet-group'
            else:
                print(f"❌ Error creating subnet group: {e}")
                return None
    
    def create_rds_instance(self, security_group_id, subnet_group_name):
        """Create RDS PostgreSQL instance"""
        try:
            db_instance_identifier = 'civicfix-db'
            db_name = 'civicfix'
            master_username = ''
            master_password = ''  # Change this!
            
            print("🚀 Creating RDS instance (this may take 10-15 minutes)...")
            
            response = self.rds_client.create_db_instance(
                DBInstanceIdentifier=db_instance_identifier,
                DBInstanceClass='db.t3.micro',  # Free tier eligible
                Engine='postgres',
                EngineVersion='15.4',
                MasterUsername=master_username,
                MasterUserPassword=master_password,
                DBName=db_name,
                AllocatedStorage=20,
                StorageType='gp2',
                VpcSecurityGroupIds=[security_group_id],
                DBSubnetGroupName=subnet_group_name,
                BackupRetentionPeriod=7,
                MultiAZ=False,
                PubliclyAccessible=True,
                StorageEncrypted=True,
                DeletionProtection=False,
                EnablePerformanceInsights=False
            )
            
            print("✅ RDS instance creation initiated")
            
            # Wait for instance to be available
            print("⏳ Waiting for RDS instance to be available...")
            waiter = self.rds_client.get_waiter('db_instance_available')
            waiter.wait(
                DBInstanceIdentifier=db_instance_identifier,
                WaiterConfig={'Delay': 30, 'MaxAttempts': 40}
            )
            
            # Get instance details
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )
            
            db_instance = response['DBInstances'][0]
            endpoint = db_instance['Endpoint']['Address']
            port = db_instance['Endpoint']['Port']
            
            print("✅ RDS instance is ready!")
            print(f"   Endpoint: {endpoint}")
            print(f"   Port: {port}")
            print(f"   Database: {db_name}")
            print(f"   Username: {master_username}")
            print(f"   Password: {master_password}")
            
            # Generate connection string
            connection_string = f"postgresql://{master_username}:{master_password}@{endpoint}:{port}/{db_name}"
            
            return {
                'endpoint': endpoint,
                'port': port,
                'database': db_name,
                'username': master_username,
                'password': master_password,
                'connection_string': connection_string
            }
            
        except ClientError as e:
            if 'DBInstanceAlreadyExists' in str(e):
                print("⚠️  RDS instance already exists")
                # Get existing instance details
                response = self.rds_client.describe_db_instances(
                    DBInstanceIdentifier='civicfix-db'
                )
                db_instance = response['DBInstances'][0]
                endpoint = db_instance['Endpoint']['Address']
                port = db_instance['Endpoint']['Port']
                
                return {
                    'endpoint': endpoint,
                    'port': port,
                    'database': 'civicfix',
                    'username': 'civicfix_user',
                    'password': 'CivicFix2024!',
                    'connection_string': f"postgresql://civicfix_user:CivicFix2024!@{endpoint}:{port}/civicfix"
                }
            else:
                print(f"❌ Error creating RDS instance: {e}")
                return None
    
    def update_env_file(self, db_config):
        """Update .env file with RDS configuration"""
        try:
            env_file = '.env'
            
            # Read current .env file
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update database configuration
            updated_lines = []
            for line in lines:
                if line.startswith('DATABASE_URL='):
                    updated_lines.append(f"DATABASE_URL={db_config['connection_string']}\n")
                elif line.startswith('DB_HOST='):
                    updated_lines.append(f"DB_HOST={db_config['endpoint']}\n")
                elif line.startswith('DB_PORT='):
                    updated_lines.append(f"DB_PORT={db_config['port']}\n")
                elif line.startswith('DB_NAME='):
                    updated_lines.append(f"DB_NAME={db_config['database']}\n")
                elif line.startswith('DB_USER='):
                    updated_lines.append(f"DB_USER={db_config['username']}\n")
                elif line.startswith('DB_PASSWORD='):
                    updated_lines.append(f"DB_PASSWORD={db_config['password']}\n")
                else:
                    updated_lines.append(line)
            
            # Write updated .env file
            with open(env_file, 'w') as f:
                f.writelines(updated_lines)
            
            print("✅ Updated .env file with RDS configuration")
            
        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
    
    def setup_rds(self):
        """Main setup function"""
        print("🚀 Setting up AWS RDS for CivicFix")
        print("=" * 50)
        
        # Create security group
        security_group_id = self.create_security_group()
        if not security_group_id:
            return False
        
        # Create subnet group
        subnet_group_name = self.create_db_subnet_group()
        if not subnet_group_name:
            return False
        
        # Create RDS instance
        db_config = self.create_rds_instance(security_group_id, subnet_group_name)
        if not db_config:
            return False
        
        # Update .env file
        self.update_env_file(db_config)
        
        print("\n🎉 AWS RDS setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run database migrations: flask db upgrade")
        print("3. Start the application: python run.py")
        print("\n⚠️  Important: Change the default password in production!")
        
        return True

def main():
    """Main function"""
    try:
        # Check AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            print("❌ AWS credentials not configured")
            print("Please configure AWS CLI or set environment variables:")
            print("  AWS_ACCESS_KEY_ID")
            print("  AWS_SECRET_ACCESS_KEY")
            print("  AWS_DEFAULT_REGION")
            return
        
        print(f"✅ Using AWS region: {session.region_name}")
        
        # Setup RDS
        rds_setup = RDSSetup()
        rds_setup.setup_rds()
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
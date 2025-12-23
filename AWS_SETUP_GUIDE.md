# CivicFix Backend - AWS Setup Guide

## 🎯 Overview
This guide helps you set up AWS RDS and S3 for the CivicFix backend.

## 📋 Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured (optional)

## 🗄️ AWS RDS Setup

### 1. Create RDS PostgreSQL Instance
```bash
# Using AWS CLI (optional)
aws rds create-db-instance \
    --db-instance-identifier civicfix-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username civicfix_admin \
    --master-user-password YourSecurePassword123 \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-name civicfix_db \
    --backup-retention-period 7 \
    --multi-az false \
    --publicly-accessible true
```

### 2. Manual RDS Setup (AWS Console)
1. Go to AWS RDS Console
2. Click "Create database"
3. Choose "PostgreSQL"
4. Select "Free tier" template
5. Configure:
   - **DB instance identifier**: `civicfix-db`
   - **Master username**: `civicfix_admin`
   - **Master password**: `YourSecurePassword123`
   - **DB name**: `civicfix_db`
6. Configure connectivity:
   - **Public access**: Yes
   - **VPC security group**: Create new or use existing
7. Click "Create database"

### 3. Configure Security Group
1. Go to EC2 Console → Security Groups
2. Find your RDS security group
3. Add inbound rule:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: Your IP or 0.0.0.0/0 (for testing)

### 4. Get Connection String
```
postgresql://civicfix_admin:YourSecurePassword123@your-rds-endpoint:5432/civicfix_db
```

## 🪣 AWS S3 Setup

### 1. Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://civicfix-media-uploads --region us-east-1
```

### 2. Manual S3 Setup (AWS Console)
1. Go to AWS S3 Console
2. Click "Create bucket"
3. Configure:
   - **Bucket name**: `civicfix-media-uploads` (must be globally unique)
   - **Region**: `us-east-1` (or your preferred region)
   - **Block Public Access**: Uncheck "Block all public access"
4. Click "Create bucket"

### 3. Configure Bucket Policy
1. Go to your bucket → Permissions → Bucket Policy
2. Add this policy (replace `civicfix-media-uploads` with your bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::civicfix-media-uploads/*"
        }
    ]
}
```

### 4. Configure CORS
1. Go to your bucket → Permissions → CORS
2. Add this configuration:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## 👤 IAM User Setup

### 1. Create IAM User
1. Go to AWS IAM Console
2. Click "Users" → "Add user"
3. Configure:
   - **User name**: `civicfix-backend`
   - **Access type**: Programmatic access
4. Click "Next: Permissions"

### 2. Attach Policies
Create and attach a custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::civicfix-media-uploads/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::civicfix-media-uploads"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Get Access Keys
1. Complete user creation
2. Download the CSV file with:
   - **Access Key ID**
   - **Secret Access Key**
3. Store these securely

## 🔧 Environment Configuration

Update your `.env` file:

```env
# AWS RDS Database
DATABASE_URL=postgresql://civicfix_admin:YourSecurePassword123@your-rds-endpoint:5432/civicfix_db

# AWS Configuration
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET_NAME=civicfix-media-uploads
AWS_REGION=us-east-1
```

## ✅ Testing the Setup

### 1. Test Database Connection
```bash
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://civicfix_admin:YourSecurePassword123@your-rds-endpoint:5432/civicfix_db')
print('Database connection successful!')
conn.close()
"
```

### 2. Test S3 Access
```bash
python -c "
import boto3
s3 = boto3.client('s3', 
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)
print(s3.list_objects_v2(Bucket='civicfix-media-uploads'))
"
```

### 3. Test Backend
```bash
python app.py
curl http://localhost:5000/health
```

## 💰 Cost Optimization

### RDS
- Use `db.t3.micro` for development (free tier eligible)
- Enable automated backups with 7-day retention
- Consider Multi-AZ for production

### S3
- Use Standard storage class
- Enable lifecycle policies for old files
- Monitor usage with CloudWatch

## 🔒 Security Best Practices

1. **RDS Security**
   - Use strong passwords
   - Restrict security group access
   - Enable encryption at rest
   - Regular security updates

2. **S3 Security**
   - Use least privilege IAM policies
   - Enable versioning for important data
   - Monitor access with CloudTrail
   - Consider server-side encryption

3. **IAM Security**
   - Rotate access keys regularly
   - Use IAM roles when possible
   - Enable MFA for console access
   - Monitor usage with CloudTrail

## 🎉 Ready!
Your AWS infrastructure is now ready for the CivicFix backend!
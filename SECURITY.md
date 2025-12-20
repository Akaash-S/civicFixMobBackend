# Security Guidelines for CivicFix Backend

## Environment Variables and Secrets Management

### ⚠️ IMPORTANT: Never commit secrets to version control

This project has been cleaned of all hardcoded secrets. Follow these guidelines to maintain security:

## 1. Environment Files

### Development Setup
```bash
# Copy the example file
cp .env.example .env

# Edit with your development credentials
nano .env
```

### Production Setup
```bash
# Copy the example file
cp .env.example .env.production

# Edit with your production credentials
nano .env.production
```

## 2. Required Secrets

### Flask Configuration
- `SECRET_KEY`: Generate a secure random key
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### Database (AWS RDS)
- `DATABASE_URL`: Full PostgreSQL connection string
- `DB_HOST`: RDS endpoint
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### AWS Configuration
- `AWS_ACCESS_KEY_ID`: IAM user access key
- `AWS_SECRET_ACCESS_KEY`: IAM user secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `S3_BUCKET_NAME`: S3 bucket for media uploads

### Firebase Configuration
- `FIREBASE_PROJECT_ID`: Firebase project ID
- `FIREBASE_SERVICE_ACCOUNT_PATH`: Path to service account JSON file

## 3. Service Account Files

### Firebase Service Account
1. Download from Firebase Console → Project Settings → Service Accounts
2. Save as `service-account.json` in backend directory
3. **Never commit this file to git**

## 4. AWS IAM Permissions

Create an IAM user with these minimal permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name"
        }
    ]
}
```

## 5. Production Deployment Security

### Docker Secrets
Use Docker secrets or environment variables:
```bash
# Set environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://..."

# Or use Docker secrets
docker secret create db_password /path/to/password.txt
```

### AWS EC2 Security
- Use IAM roles instead of access keys when possible
- Store secrets in AWS Systems Manager Parameter Store
- Use AWS Secrets Manager for database credentials

### Environment Variables on EC2
```bash
# Set in /etc/environment or systemd service
echo 'SECRET_KEY=your-secret-key' >> /etc/environment
```

## 6. Security Checklist

### Before Deployment
- [ ] All `.env*` files are in `.gitignore`
- [ ] No hardcoded secrets in source code
- [ ] Service account files are not committed
- [ ] Generated strong SECRET_KEY
- [ ] AWS IAM user has minimal permissions
- [ ] Database uses strong password
- [ ] CORS origins are properly configured

### Production Security
- [ ] Use HTTPS in production
- [ ] Enable database SSL
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup encryption keys

## 7. Emergency Response

### If Secrets Are Compromised
1. **Immediately rotate all affected credentials**
2. **Revoke old AWS access keys**
3. **Change database passwords**
4. **Generate new Firebase service account**
5. **Update all deployment environments**
6. **Review access logs for unauthorized usage**

### Git History Cleanup
If secrets were accidentally committed:
```bash
# Remove from git history (DANGEROUS - coordinate with team)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch .env .env.production service-account.json' \
--prune-empty --tag-name-filter cat -- --all

# Force push (only if absolutely necessary)
git push origin --force --all
```

## 8. Monitoring and Alerts

### Set up alerts for:
- Failed authentication attempts
- Unusual API usage patterns
- Database connection failures
- AWS cost spikes
- Error rate increases

### Log Security Events
- Authentication attempts
- Permission changes
- File uploads
- Database queries
- API rate limiting

## 9. Development Best Practices

### Code Reviews
- Check for hardcoded secrets
- Verify environment variable usage
- Review IAM permissions
- Validate input sanitization

### Testing
- Use test databases
- Mock external services
- Test with minimal permissions
- Validate error handling

## 10. Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [Flask Security](https://flask.palletsprojects.com/en/2.0.x/security/)
- [Docker Security](https://docs.docker.com/engine/security/)

---

**Remember: Security is an ongoing process, not a one-time setup. Regularly review and update your security practices.**
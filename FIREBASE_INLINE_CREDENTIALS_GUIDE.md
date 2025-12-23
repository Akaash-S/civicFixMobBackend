# Firebase Inline Credentials Guide

## Overview
The CivicFix backend now supports Firebase service account credentials as inline JSON in environment variables, which is more secure and deployment-friendly than using file paths.

## Configuration Options

### Option 1: Inline JSON (Recommended)
Set the Firebase service account as a JSON string in your environment variables:

```bash
# In .env or .env.production
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"your-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token"}
FIREBASE_PROJECT_ID=your-firebase-project-id
```

### Option 2: File Path (Fallback)
If you prefer using a file, you can still use the file path approach:

```bash
# In .env or .env.production
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id
```

## How to Get Your Firebase Service Account JSON

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings (gear icon)
4. Navigate to "Service accounts" tab
5. Click "Generate new private key"
6. Download the JSON file
7. Copy the entire JSON content as a single line

## Converting JSON File to Single Line

If you have a Firebase service account JSON file, convert it to a single line:

### Using Python:
```python
import json

# Read the JSON file
with open('service-account.json', 'r') as f:
    data = json.load(f)

# Convert to single line
single_line = json.dumps(data, separators=(',', ':'))
print(single_line)
```

### Using jq (Linux/Mac):
```bash
jq -c . service-account.json
```

### Using Node.js:
```javascript
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('service-account.json', 'utf8'));
console.log(JSON.stringify(data));
```

## Environment Variable Setup

### For Development (.env):
```bash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
FIREBASE_PROJECT_ID=your-project-id
```

### For Production (.env.production):
```bash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
FIREBASE_PROJECT_ID=your-project-id
```

### For Docker Environment:
The Docker Compose configuration will automatically use the environment variables from `.env.production`.

## Security Benefits

### ✅ Advantages of Inline JSON:
- No file system dependencies
- Easier deployment to cloud platforms
- Better for containerized environments
- No risk of missing files
- Environment-specific configuration
- Better for CI/CD pipelines

### ✅ Security Features:
- Credentials are not stored in files
- Environment variables are not logged
- Automatic validation of JSON structure
- Placeholder detection prevents accidental deployment

## Deployment Process

1. **Set Environment Variables:**
   ```bash
   # Copy template
   cp .env.example .env.production
   
   # Edit .env.production with your credentials
   nano .env.production
   ```

2. **Add Firebase Credentials:**
   ```bash
   FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-actual-project-id",...}
   FIREBASE_PROJECT_ID=your-actual-project-id
   ```

3. **Deploy:**
   ```bash
   ./deploy-resilient.sh
   ```

## Validation

The Firebase service will automatically:
- ✅ Validate JSON structure
- ✅ Check for required fields
- ✅ Detect placeholder values
- ✅ Test connectivity
- ✅ Gracefully fail if invalid

## Troubleshooting

### Common Issues:

1. **Invalid JSON Format:**
   - Ensure the JSON is properly escaped
   - Use single quotes around the entire JSON string
   - Validate JSON syntax online

2. **Missing Required Fields:**
   - Ensure all required fields are present: `type`, `project_id`, `private_key`, `client_email`

3. **Placeholder Values:**
   - Replace all "your-" and "placeholder" values with actual data

4. **Private Key Format:**
   - Ensure private key includes proper line breaks: `\n`
   - Keep the BEGIN/END PRIVATE KEY markers

### Debug Commands:

```bash
# Check if Firebase is initialized
curl http://localhost:5000/health

# Check application logs
docker-compose logs civicfix-backend | grep -i firebase

# Validate JSON format
echo $FIREBASE_SERVICE_ACCOUNT_JSON | python3 -m json.tool
```

## Migration from File Path

If you're currently using file path configuration:

1. **Read your current service account file:**
   ```bash
   cat service-account.json | jq -c .
   ```

2. **Copy the output to your environment variable:**
   ```bash
   FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
   ```

3. **Remove the file path configuration:**
   ```bash
   # Comment out or remove
   # FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
   ```

4. **Redeploy:**
   ```bash
   ./deploy-resilient.sh
   ```

## Best Practices

1. **Never commit credentials to version control**
2. **Use different service accounts for different environments**
3. **Regularly rotate service account keys**
4. **Monitor Firebase usage and access logs**
5. **Use environment-specific project IDs**

The application will automatically detect and use inline JSON credentials when available, falling back to file path if needed.
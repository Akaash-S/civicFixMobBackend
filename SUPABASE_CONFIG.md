# Supabase Configuration for CivicFix Backend

## Required Environment Variables

Add these to your `.env` file or environment variables:

```bash
# Supabase Configuration
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here
```

## How to Get Your Supabase JWT Secret

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Find the **JWT Settings** section
4. Copy the **JWT Secret** (it's a long string starting with something like `your-jwt-secret-key`)

## Example .env file

```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1

# Firebase (optional, for Firebase users)
FIREBASE_SERVICE_ACCOUNT_B64=your_base64_encoded_firebase_credentials

# Supabase (required for Supabase users)
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Flask
SECRET_KEY=your_flask_secret_key
FLASK_ENV=production
```

## Security Notes

1. **Never commit your JWT secret to version control**
2. **Use different secrets for development and production**
3. **Rotate your JWT secret periodically**
4. **Keep your JWT secret secure and private**

## Testing the Configuration

After adding the JWT secret, you can test authentication using:

```bash
python test_submission.py
```

Or use the frontend debug tools at `/debug-auth` in your app.

## Troubleshooting

### "SUPABASE_JWT_SECRET not found"
- Make sure you've added the JWT secret to your environment variables
- Restart your backend server after adding the environment variable

### "Invalid Supabase token"
- Check that your frontend is sending the correct Supabase access token
- Verify the JWT secret matches your Supabase project settings
- Check token expiration (Supabase tokens expire after 1 hour by default)

### "Token verification failed"
- Ensure the JWT secret is exactly as shown in Supabase dashboard
- Check for any extra spaces or characters in the environment variable
- Verify the token format is correct (should be a JWT, not base64 JSON)
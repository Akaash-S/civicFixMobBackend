# URGENT: Fix Bcrypt Error - Container Rebuild Required

## Current Issue
The Docker container is still running the **old version** of the code that has the bcrypt import. Even though I fixed the code, the container needs to be rebuilt to use the new version.

## Error Details
```
ERROR:__main__:Error setting password: No module named 'bcrypt'
POST /api/v1/onboarding/password HTTP/1.1" 500 -
```

## Root Cause
The running Docker container was built with the old code that had:
```python
import bcrypt  # This line was removed but container still has old version
```

## IMMEDIATE FIX REQUIRED

### Step 1: Stop Current Container
```bash
cd backend
docker-compose down
```

### Step 2: Force Rebuild Container
```bash
docker-compose build --no-cache backend
```

### Step 3: Start New Container
```bash
docker-compose up -d backend
```

### Step 4: Verify Fix
```bash
# Check container logs
docker-compose logs backend

# Test health endpoint
curl http://localhost:5000/health

# Test the fixed endpoint (should get 401, not 500)
curl -X POST http://localhost:5000/api/v1/onboarding/password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fake-token" \
  -d '{"password": "test123456"}'
```

## What Was Fixed in Code

### Before (Causing Error)
```python
@app.route('/api/v1/onboarding/password', methods=['POST'])
@require_auth
def set_onboarding_password(current_user):
    try:
        # ... validation code ...
        
        # Hash password
        import bcrypt  # ❌ This caused the error
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

### After (Fixed)
```python
@app.route('/api/v1/onboarding/password', methods=['POST'])
@require_auth
def set_onboarding_password(current_user):
    try:
        # ... validation code ...
        
        # Hash password using existing function
        password_hash = hash_password(password)  # ✅ Uses existing SHA-256 function
```

## Expected Result After Rebuild

### Container Startup
```
🚀 CivicFix Backend - Production Startup
✅ All basic imports successful
🎯 Starting CivicFix Backend...
INFO:werkzeug: * Running on http://127.0.0.1:5000
```

### API Response (Success)
```json
{
  "message": "Password set successfully",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "password_hash": "salt:hash_value"
  }
}
```

### API Response (Auth Error - Expected)
```json
{
  "error": "Authorization header required"
}
```

## Alternative Quick Fix Commands

### One-Line Rebuild
```bash
cd backend && docker-compose down && docker-compose build --no-cache backend && docker-compose up -d backend
```

### Check if Fix Worked
```bash
# Should show no bcrypt errors in logs
docker-compose logs backend | grep -i bcrypt

# Should show healthy status
curl -s http://localhost:5000/health | jq .status
```

## Verification Steps

1. **Container Rebuild**: Must rebuild to get new code
2. **Health Check**: Should return 200 OK
3. **Onboarding Test**: Should get 401 (not 500) without auth
4. **Mobile App Test**: Password setup should work

## Why This Happened

1. **Code was fixed** ✅ - Removed bcrypt import
2. **Container not rebuilt** ❌ - Still running old code
3. **Docker layer caching** - Container didn't pick up changes

## CRITICAL: Run These Commands Now

```bash
# Navigate to backend directory
cd backend

# Stop and rebuild container (REQUIRED)
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d backend

# Wait 30 seconds for startup
sleep 30

# Test the fix
curl http://localhost:5000/health
```

The bcrypt error will be resolved once the container is rebuilt with the fixed code.
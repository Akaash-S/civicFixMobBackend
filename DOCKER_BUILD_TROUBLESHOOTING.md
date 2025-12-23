# Docker Build Troubleshooting Guide

## Issue: Pip Installation Failed

If you're getting a pip installation error during Docker build, here are the solutions:

## ✅ Solution 1: Updated Dockerfile (Recommended)

The Dockerfile has been updated with:
- Simplified single-stage build
- Better system dependency management
- Improved error handling
- Added netcat for database connectivity checks

## ✅ Solution 2: Clean Requirements.txt

The requirements.txt has been cleaned:
- Removed problematic packages (orjson)
- Organized dependencies by category
- Removed empty lines that could cause issues
- Added comments for clarity

## ✅ Solution 3: Build with More Memory

If you're still having issues, try building with more memory:

```bash
# Build with more memory allocated to Docker
docker build --memory=2g -t civicfix-backend .

# Or build with no cache to ensure clean build
docker build --no-cache -t civicfix-backend .
```

## ✅ Solution 4: Alternative Build Approach

If the main build fails, try this step-by-step approach:

### Step 1: Build Base Image
```bash
# Create a base image with system dependencies
docker build -f Dockerfile.base -t civicfix-base .
```

Create `Dockerfile.base`:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libssl-dev libffi-dev libjpeg-dev libpng-dev curl netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel
```

### Step 2: Build Application Image
```bash
# Build the application on top of base image
docker build -f Dockerfile.app -t civicfix-backend .
```

Create `Dockerfile.app`:
```dockerfile
FROM civicfix-base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /bin/bash appuser
RUN mkdir -p logs temp uploads && chown -R appuser:appgroup /app && chmod +x docker-entrypoint.sh

USER appuser
EXPOSE 5000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:application"]
```

## ✅ Solution 5: Manual Dependency Installation

If specific packages are failing, install them individually:

```bash
# Create a custom requirements file with core dependencies only
cat > requirements-core.txt << EOF
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
EOF

# Build with core dependencies first
docker build --build-arg REQUIREMENTS_FILE=requirements-core.txt -t civicfix-backend .
```

## ✅ Solution 6: Platform-Specific Build

If you're on Apple Silicon (M1/M2) or ARM:

```bash
# Build for specific platform
docker build --platform linux/amd64 -t civicfix-backend .

# Or for ARM
docker build --platform linux/arm64 -t civicfix-backend .
```

## ✅ Solution 7: Use Pre-built Base Image

Use a pre-built Python image with common dependencies:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev curl netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in layers
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

COPY requirements-extras.txt .
RUN pip install --no-cache-dir -r requirements-extras.txt

# Rest of Dockerfile...
```

Split requirements.txt into:

**requirements-core.txt:**
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.9
gunicorn==21.2.0
```

**requirements-extras.txt:**
```
firebase-admin==6.4.0
boto3==1.34.0
Flask-SocketIO==5.3.6
# ... other packages
```

## ✅ Solution 8: Debug Build Process

To debug the build process:

```bash
# Build with verbose output
docker build --progress=plain --no-cache -t civicfix-backend .

# Build and stop at specific layer for debugging
docker build --target builder -t civicfix-debug .
docker run -it civicfix-debug /bin/bash
```

## ✅ Solution 9: Use Docker Compose Build

Sometimes docker-compose handles builds better:

```bash
# Build using docker-compose
docker-compose build civicfix-backend

# Build with no cache
docker-compose build --no-cache civicfix-backend
```

## ✅ Solution 10: Check Docker Resources

Ensure Docker has enough resources:

```bash
# Check Docker system info
docker system info

# Clean up Docker to free space
docker system prune -a -f

# Check available disk space
df -h
```

## Common Error Messages and Solutions

### Error: "failed to solve: process did not complete successfully: exit code: 1"

**Solution**: Usually a dependency installation issue. Try:
1. Building with `--no-cache`
2. Using the simplified requirements.txt
3. Building with more memory

### Error: "Package 'xyz' not found"

**Solution**: Missing system dependency. Add to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y package-name
```

### Error: "No space left on device"

**Solution**: Clean up Docker:
```bash
docker system prune -a -f
docker volume prune -f
```

### Error: "Connection timeout"

**Solution**: Increase pip timeout:
```dockerfile
RUN pip install --timeout=300 -r requirements.txt
```

## Final Verification

After successful build, test the image:

```bash
# Test the built image
docker run --rm civicfix-backend python -c "import flask, sqlalchemy; print('Build successful!')"

# Test with environment variables
docker run --rm -e SECRET_KEY=test civicfix-backend python -c "from app import create_app; print('App creation successful!')"
```

## If All Else Fails

Use the working Docker image approach:

1. **Use a working base image**: Start with `python:3.11-slim`
2. **Install dependencies manually**: Copy and run pip install commands one by one
3. **Test each layer**: Build incrementally and test each step
4. **Use multi-stage build**: Separate build and runtime environments

The updated Dockerfile should work in most cases. If you continue having issues, try the step-by-step approach or contact support with the specific error message.
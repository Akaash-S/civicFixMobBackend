#!/bin/bash

# CivicFix Backend - Docker Build Test Script

set -e

echo "🐳 CivicFix Backend - Docker Build Test"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check Docker is running
log_step "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
log_info "Docker is running ✓"

# Check available disk space
log_step "Checking disk space..."
available_space=$(df . | tail -1 | awk '{print $4}')
if [ "$available_space" -lt 2000000 ]; then
    log_warn "Low disk space detected. Consider cleaning up Docker images."
    log_info "Run: docker system prune -a -f"
fi
log_info "Disk space check completed ✓"

# Clean up any existing test images
log_step "Cleaning up previous test builds..."
docker rmi civicfix-backend-test 2>/dev/null || true
log_info "Cleanup completed ✓"

# Test 1: Build with current Dockerfile
log_step "Test 1: Building with current Dockerfile..."
if docker build -t civicfix-backend-test . > build.log 2>&1; then
    log_info "✅ Build successful!"
    
    # Test the built image
    log_step "Testing built image..."
    if docker run --rm civicfix-backend-test python -c "import flask, sqlalchemy, firebase_admin, boto3; print('All imports successful')"; then
        log_info "✅ Image test successful!"
    else
        log_warn "⚠️ Image test failed - but build was successful"
    fi
else
    log_error "❌ Build failed. Check build.log for details."
    echo "Last 20 lines of build log:"
    tail -20 build.log
    
    # Try alternative build
    log_step "Trying alternative build approach..."
    
    # Create minimal requirements for testing
    cat > requirements-minimal.txt << EOF
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-dotenv==1.0.0
EOF
    
    # Create minimal Dockerfile
    cat > Dockerfile.minimal << EOF
FROM python:3.11-slim
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN mkdir -p logs && chown -R appuser:appgroup /app && chmod +x docker-entrypoint.sh
USER appuser
EXPOSE 5000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:application"]
EOF
    
    if docker build -f Dockerfile.minimal -t civicfix-backend-minimal . > build-minimal.log 2>&1; then
        log_info "✅ Minimal build successful!"
        log_info "You can use Dockerfile.minimal as a starting point and add dependencies gradually."
    else
        log_error "❌ Even minimal build failed. Check build-minimal.log for details."
        echo "Last 10 lines of minimal build log:"
        tail -10 build-minimal.log
    fi
fi

# Test 2: Check requirements.txt
log_step "Test 2: Validating requirements.txt..."
if python3 -c "
import pkg_resources
with open('requirements.txt', 'r') as f:
    requirements = f.read().strip().split('\n')
    requirements = [r for r in requirements if r and not r.startswith('#')]
    for req in requirements:
        try:
            pkg_resources.Requirement.parse(req)
        except Exception as e:
            print(f'Invalid requirement: {req} - {e}')
            exit(1)
print('All requirements are valid')
"; then
    log_info "✅ Requirements.txt is valid"
else
    log_warn "⚠️ Requirements.txt has issues"
fi

# Test 3: Check essential files
log_step "Test 3: Checking essential files..."
essential_files=("Dockerfile" "requirements.txt" "docker-entrypoint.sh" "run.py" "gunicorn.conf.py")
missing_files=()

for file in "${essential_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    log_info "✅ All essential files present"
else
    log_warn "⚠️ Missing files: ${missing_files[*]}"
fi

# Test 4: Check Python syntax
log_step "Test 4: Checking Python syntax..."
if find . -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null; then
    log_info "✅ Python syntax check passed"
else
    log_warn "⚠️ Python syntax issues found"
fi

# Summary
echo ""
log_step "Build Test Summary"
echo "=================="

if docker images | grep -q civicfix-backend-test; then
    log_info "✅ Docker image built successfully"
    log_info "Image size: $(docker images civicfix-backend-test --format 'table {{.Size}}' | tail -1)"
    
    echo ""
    log_info "🎉 Build test completed successfully!"
    log_info "You can now deploy using: docker-compose up -d"
    
    # Cleanup
    log_step "Cleaning up test images..."
    docker rmi civicfix-backend-test 2>/dev/null || true
    rm -f build.log build-minimal.log requirements-minimal.txt Dockerfile.minimal 2>/dev/null || true
    
else
    log_error "❌ Build test failed"
    log_info "Check the troubleshooting guide: DOCKER_BUILD_TROUBLESHOOTING.md"
    log_info "Or try building with: docker build --no-cache -t civicfix-backend ."
fi

echo ""
log_info "Build test completed."
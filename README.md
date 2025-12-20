# CivicFix Backend

Production-ready Flask backend for the CivicFix civic issue reporting platform.

## 🏗️ Architecture

- **Framework**: Flask with Socket.IO for real-time features
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Firebase Authentication
- **Storage**: AWS S3 for media uploads
- **Caching**: Redis for rate limiting and sessions
- **Deployment**: Docker + Gunicorn ready

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- AWS Account (for S3)
- Firebase Project (for authentication)

### 1. Environment Setup

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:

```env
# Database (AWS RDS PostgreSQL)
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/civicfix

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication with Google Sign-In
3. Generate a service account key:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save as `firebase-service-account.json` in the backend directory

### 4. AWS Setup

1. Create an AWS account and get access keys
2. The application will automatically create the S3 bucket if it doesn't exist
3. Ensure your AWS user has S3 permissions

### 5. Database Setup

```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Run the Application

```bash
# Development mode
python run.py

# Or with Flask CLI
flask run --host=0.0.0.0 --port=5000
```

## 🐳 Docker Deployment

### Development with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f civicfix-backend

# Stop services
docker-compose down
```

### Production Docker Build

```bash
# Build image
docker build -t civicfix-backend .

# Run container
docker run -p 5000:5000 --env-file .env civicfix-backend
```

## 📡 API Documentation

### Base URL
```
http://localhost:5000/api/v1
```

### Authentication
All protected endpoints require Firebase ID token in Authorization header:
```
Authorization: Bearer <firebase-id-token>
```

### Endpoints

#### Authentication
- `POST /auth/sync-user` - Sync user from Firebase to local DB
- `GET /auth/profile` - Get current user profile
- `PUT /auth/profile` - Update user profile

#### Issues
- `POST /issues` - Create new issue
- `GET /issues` - List issues (with filtering)
- `GET /issues/<id>` - Get specific issue
- `PUT /issues/<id>/status` - Update issue status (Admin only)
- `GET /issues/categories` - Get available categories

#### Media
- `POST /media/presign-url` - Get presigned URL for file upload
- `POST /media/download-url` - Get presigned URL for file download
- `POST /media/file-info` - Get file information

#### Interactions
- `POST /issues/<id>/upvote` - Upvote/remove upvote from issue
- `POST /issues/<id>/comment` - Add comment to issue
- `GET /issues/<id>/comments` - Get issue comments
- `DELETE /comments/<id>` - Delete comment

#### Analytics (Admin only)
- `GET /analytics/summary` - Get analytics summary
- `GET /analytics/issues/heatmap` - Get issue heatmap data

### Real-time Events (Socket.IO)

Connect to Socket.IO endpoint: `ws://localhost:5000`

#### Client Events
- `join_location` - Join location-based updates
- `leave_location` - Leave location updates
- `join_issue` - Join issue-specific updates
- `leave_issue` - Leave issue updates

#### Server Events
- `issue_created` - New issue created
- `issue_status_updated` - Issue status changed
- `issue_upvoted` - Issue upvoted
- `comment_added` - New comment added
- `notification_new` - New notification

## 🔧 Development

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Downgrade migration
flask db downgrade
```

### Seed Data

```bash
# Seed initial data (admin user, categories)
python -c "from app.seed import seed_initial_data; seed_initial_data()"

# Seed demo data for development
python -c "from app.seed import seed_demo_data; seed_demo_data()"
```

### Testing

```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 🚀 Production Deployment

### AWS Deployment

1. **RDS Setup**:
   - Create PostgreSQL RDS instance
   - Configure security groups
   - Update DATABASE_URL in environment

2. **S3 Setup**:
   - Bucket will be created automatically
   - Ensure proper IAM permissions

3. **EC2/ECS Deployment**:
   ```bash
   # Build and push to ECR
   docker build -t civicfix-backend .
   docker tag civicfix-backend:latest <ecr-repo-url>:latest
   docker push <ecr-repo-url>:latest
   ```

4. **Environment Variables**:
   - Set all required environment variables
   - Use AWS Secrets Manager for sensitive data

### Health Checks

The application provides a health check endpoint:
```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "service": "CivicFix API"
}
```

## 📊 Monitoring

### Logging

Logs are written to:
- Console (stdout)
- File: `logs/civicfix.log` (with rotation)

Log levels:
- INFO: General application flow
- WARNING: Potential issues
- ERROR: Error conditions
- DEBUG: Detailed debugging (development only)

### Metrics

The application is ready for monitoring with:
- Prometheus metrics (add prometheus_flask_exporter)
- Health checks for load balancers
- Structured logging for log aggregation

## 🔒 Security

### Implemented Security Features

- Firebase Authentication integration
- Rate limiting (200/day, 50/hour per IP)
- CORS configuration
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- Secure file uploads with presigned URLs
- Private S3 bucket configuration

### Security Best Practices

1. **Environment Variables**: Never commit secrets to version control
2. **HTTPS**: Always use HTTPS in production
3. **Database**: Use connection pooling and prepared statements
4. **File Uploads**: Validate file types and sizes
5. **Rate Limiting**: Implement appropriate rate limits
6. **Logging**: Log security events but not sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the logs for error details

---

**CivicFix Backend** - Empowering citizens to improve their communities through technology.
# ❌ AWS Service Anti-Patterns (What NOT to Do)

## 1. Circular Import Recursion

### ❌ BAD: Circular Dependencies
```python
# aws_service.py
from flask import current_app
from app import create_app  # CIRCULAR IMPORT!

class AWSService:
    def __init__(self):
        app = create_app()  # This creates infinite recursion!
```

### ✅ GOOD: Clean Dependencies
```python
# aws_service.py
import boto3
# No Flask imports in service layer!

class AWSService:
    def initialize(self, config: dict):
        # Config passed from app, no imports needed
        pass
```

## 2. Recursive Constructor Pattern

### ❌ BAD: Self-Calling Constructor
```python
class AWSService:
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialize()
    
    def initialize(self):
        if not self.initialized:
            self.__init__()  # RECURSION!
```

### ✅ GOOD: Initialization Flag
```python
class AWSService:
    def __init__(self):
        self._initialized = False
    
    def initialize(self, config):
        if self._initialized:
            return  # Prevent double initialization
        # ... initialization code ...
        self._initialized = True
```

## 3. Flask Context Recursion

### ❌ BAD: Context Creation in Service
```python
def get_aws_service():
    with app.app_context():  # Creates new context
        if not hasattr(current_app, 'aws_service'):
            current_app.aws_service = AWSService()  # Might trigger recursion
        return current_app.aws_service
```

### ✅ GOOD: Module-Level Singleton
```python
_aws_service = None

def get_aws_service():
    global _aws_service
    return _aws_service  # Simple, no context needed
```

## 4. Logger/Config Circular Dependencies

### ❌ BAD: Service Imports App Components
```python
# aws_service.py
from app.utils.logger import get_logger  # Logger might import services
from app.config import get_config        # Config might import services

class AWSService:
    def __init__(self):
        self.logger = get_logger(__name__)  # POTENTIAL RECURSION
        self.config = get_config()          # POTENTIAL RECURSION
```

### ✅ GOOD: Standard Library Only
```python
# aws_service.py
import logging  # Standard library only

class AWSService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)  # Safe
    
    def initialize(self, config: dict):
        # Config passed as parameter, no imports
        pass
```

## 5. Per-Request Initialization

### ❌ BAD: Initialize on Every Request
```python
@app.route('/upload')
def upload():
    aws_service = AWSService()  # NEW INSTANCE EVERY REQUEST!
    aws_service.initialize()   # EXPENSIVE!
    return aws_service.upload_file()
```

### ✅ GOOD: Singleton Pattern
```python
@app.route('/upload')
def upload():
    aws_service = get_aws_service()  # Reuse existing instance
    return aws_service.upload_file()
```

## 6. Incorrect Singleton Implementation

### ❌ BAD: Non-Thread-Safe Singleton
```python
class AWSService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # RACE CONDITION!
        return cls._instance
```

### ✅ GOOD: Thread-Safe Singleton
```python
import threading

class AWSService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Thread-safe
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

## 7. Mixing Initialization with Business Logic

### ❌ BAD: Initialize During Operation
```python
def upload_file(self, file_data):
    if not self.s3_client:
        self.initialize()  # DANGEROUS! Might fail mid-operation
    return self.s3_client.upload_file(file_data)
```

### ✅ GOOD: Fail Fast Pattern
```python
def upload_file(self, file_data):
    if not self.is_healthy():
        raise AWSServiceError("Service not initialized")
    return self.s3_client.upload_file(file_data)
```

## 8. Global State Mutation

### ❌ BAD: Modifying Global Config
```python
import os

class AWSService:
    def initialize(self):
        os.environ['AWS_REGION'] = 'us-east-1'  # MUTATING GLOBAL STATE!
        # Other services might be affected
```

### ✅ GOOD: Immutable Configuration
```python
class AWSService:
    def initialize(self, config: dict):
        self.region = config.get('AWS_REGION', 'us-east-1')  # Local copy
        # No global state mutation
```

## 9. Exception Swallowing

### ❌ BAD: Silent Failures
```python
def initialize(self):
    try:
        self.s3_client = boto3.client('s3')
    except:
        pass  # SILENT FAILURE! App thinks it's working
```

### ✅ GOOD: Explicit Error Handling
```python
def initialize(self, config):
    try:
        self.s3_client = boto3.client('s3')
    except Exception as e:
        logger.error(f"AWS initialization failed: {e}")
        raise AWSServiceError(f"Failed to initialize: {e}") from e
```

## 10. Lazy Loading in Wrong Places

### ❌ BAD: Lazy Load in Request Handler
```python
@app.route('/health')
def health():
    if not hasattr(current_app, 'aws_service'):
        current_app.aws_service = AWSService()  # SLOW REQUEST!
    return current_app.aws_service.health_check()
```

### ✅ GOOD: Initialize at Startup
```python
# In create_app()
def create_app():
    app = Flask(__name__)
    app.aws_service = initialize_aws_service(config)  # STARTUP TIME
    return app

@app.route('/health')
def health():
    return current_app.aws_service.health_check()  # FAST
```
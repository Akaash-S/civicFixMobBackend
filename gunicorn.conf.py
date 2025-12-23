"""
CivicFix Backend - Gunicorn Production Configuration
Optimized for performance, reliability, and monitoring
"""

import os
import multiprocessing
from pathlib import Path

# ================================
# Server Socket Configuration
# ================================
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# ================================
# Worker Process Configuration
# ================================
# Calculate optimal worker count for Render
cpu_count = multiprocessing.cpu_count()
# Render has memory limits, so use fewer workers
workers = int(os.environ.get('GUNICORN_WORKERS', min(cpu_count * 2 + 1, 4)))

# Worker class - use gevent for better Render compatibility
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', "gevent")
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Timeouts
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))  # Increased for initialization
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Worker lifecycle
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 100))

# ================================
# Logging Configuration
# ================================
# Log to stdout/stderr for Docker
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Custom access log format with more details
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)

# Enable access logging
disable_redirect_access_to_syslog = False

# ================================
# Process Configuration
# ================================
proc_name = "civicfix-backend"
daemon = False
pidfile = "/tmp/civicfix-gunicorn.pid"

# Security - run as non-root user (handled by Docker)
user = None
group = None

# ================================
# Application Configuration
# ================================
# Preload application for better performance and memory sharing
preload_app = True

# Enable sendfile for better file serving performance
sendfile = True

# ================================
# SSL Configuration (if needed)
# ================================
# Uncomment and configure if using SSL termination at Gunicorn level
# keyfile = os.environ.get('SSL_KEYFILE')
# certfile = os.environ.get('SSL_CERTFILE')
# ssl_version = ssl.PROTOCOL_TLS
# ciphers = 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'

# ================================
# Performance Tuning
# ================================
# Enable reuse_port for better load distribution (Linux 3.9+)
reuse_port = True

# Thread configuration for eventlet
threads = int(os.environ.get('GUNICORN_THREADS', 1))

# ================================
# Monitoring and Stats
# ================================
# Enable stats endpoint
statsd_host = os.environ.get('STATSD_HOST')
statsd_prefix = os.environ.get('STATSD_PREFIX', 'civicfix.backend')

# ================================
# Environment Variables
# ================================
raw_env = [
    f"FLASK_ENV={os.environ.get('FLASK_ENV', 'production')}",
    f"PYTHONPATH={os.environ.get('PYTHONPATH', '/app')}",
]

# ================================
# Hooks and Callbacks
# ================================

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 CivicFix Backend - Starting Gunicorn master process")
    server.log.info(f"📊 Configuration: {workers} workers, {worker_class} worker class")
    server.log.info(f"🔧 Timeout: {timeout}s, Keepalive: {keepalive}s")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 Reloading CivicFix Backend workers")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ CivicFix Backend server is ready to accept connections")
    server.log.info(f"🌐 Listening on: {bind}")
    server.log.info(f"👥 Workers: {workers}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"🛑 Worker {worker.pid} received interrupt signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"🔄 Forking worker {worker.age} (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"✨ Worker {worker.age} spawned (pid: {worker.pid})")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"🎯 Worker {worker.pid} initialized successfully")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.error(f"💥 Worker {worker.pid} aborted")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("🔄 Pre-exec: Preparing to fork new master process")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Only log for debug level to avoid spam
    if server.log.level <= 10:  # DEBUG level
        worker.log.debug(f"📥 Processing request: {req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Only log errors and slow requests
    if resp.status_code >= 400:
        worker.log.warning(f"❌ Request failed: {req.method} {req.path} - {resp.status_code}")

def child_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(f"👋 Worker {worker.pid} exited")

def worker_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(f"🚪 Worker {worker.pid} exit")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"👥 Worker count changed: {old_value} → {new_value}")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("👋 CivicFix Backend server shutting down")

# ================================
# Error Handling
# ================================

def worker_connections_handler(worker, req, client, addr):
    """Handle worker connection limits."""
    worker.log.warning(f"⚠️ Worker connection limit reached for {addr}")

# ================================
# Custom Configuration Validation
# ================================

def validate_config():
    """Validate Gunicorn configuration."""
    errors = []
    
    if workers < 1:
        errors.append("Workers must be >= 1")
    
    if timeout < 30:
        errors.append("Timeout should be >= 30 seconds for proper initialization")
    
    if worker_connections < 100:
        errors.append("Worker connections should be >= 100")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Validate configuration on import
validate_config()

# ================================
# Development vs Production Settings
# ================================

if os.environ.get('FLASK_ENV') == 'development':
    # Development overrides
    workers = 1
    reload = True
    loglevel = 'debug'
    timeout = 60
    preload_app = False
    
    def on_starting(server):
        server.log.info("🔧 CivicFix Backend - Development Mode")
        server.log.info("⚠️  Using single worker with auto-reload")

# ================================
# Health Check Configuration
# ================================

def health_check():
    """Simple health check function."""
    try:
        # Basic health check - can be extended
        return True
    except Exception:
        return False
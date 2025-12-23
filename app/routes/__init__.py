from flask import Blueprint
from app.routes.auth import auth_bp
from app.routes.issues import issues_bp
from app.routes.media import media_bp
from app.routes.interactions import interactions_bp
from app.routes.analytics import analytics_bp
from app.routes.health import health_bp

def register_routes(app):
    """Register all route blueprints"""
    
    # API version prefix
    api_prefix = f"/api/{app.config['API_VERSION']}"
    
    # Register health check first (no prefix)
    app.register_blueprint(health_bp)
    
    # Register API blueprints
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(issues_bp, url_prefix=f"{api_prefix}/issues")
    app.register_blueprint(media_bp, url_prefix=f"{api_prefix}/media")
    app.register_blueprint(interactions_bp, url_prefix=f"{api_prefix}")
    app.register_blueprint(analytics_bp, url_prefix=f"{api_prefix}/analytics")
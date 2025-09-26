"""Main Flask application for GuitarTab Pro."""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api, Resource

from app.auth import AuthConfig
from app.database import create_tables
from app.routes.auth import auth_bp
from app.utils.error_handlers import register_error_handlers


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration from environment variables
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["JWT_SECRET_KEY"] = AuthConfig.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = AuthConfig.JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = AuthConfig.JWT_REFRESH_TOKEN_EXPIRES
    app.config["JWT_ALGORITHM"] = AuthConfig.JWT_ALGORITHM
    app.config["JWT_ACCESS_TOKEN_LOCATION"] = AuthConfig.JWT_ACCESS_TOKEN_LOCATION
    app.config["JWT_COOKIE_SECURE"] = AuthConfig.JWT_COOKIE_SECURE
    app.config["JWT_COOKIE_CSRF_PROTECT"] = AuthConfig.JWT_COOKIE_CSRF_PROTECT
    
    # CORS configuration
    CORS(app, origins=["http://localhost:3000", "http://localhost:8080"])
    
    # Initialize JWT
    JWTManager(app)
    
    # Initialize API documentation
    api = Api(
        app,
        version="1.0.0",
        title="GuitarTab Pro API",
        description="REST API for GuitarTab Pro - Guitar TAB and lyrics organizer",
        doc="/api/docs/",
        prefix="/api"
    )
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    
    # Create database tables
    with app.app_context():
        create_tables()
    
    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "guitartab-pro"}, 200
    
    # Root endpoint
    @app.route("/")
    def root():
        """Root endpoint."""
        return {
            "message": "GuitarTab Pro API",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/auth",
                "health": "/health",
                "docs": "/api/docs/"
            }
        }, 200
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

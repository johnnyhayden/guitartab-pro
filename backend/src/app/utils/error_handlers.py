"""Error handlers for Flask application."""

from flask import Flask, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Bad Request",
            "status": 400,
            "detail": str(error.description) if hasattr(error, 'description') else "Bad request",
            "instance": request.url
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
            "title": "Unauthorized",
            "status": 401,
            "detail": str(error.description) if hasattr(error, 'description') else "Authentication required",
            "instance": request.url
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.3",
            "title": "Forbidden",
            "status": 403,
            "detail": str(error.description) if hasattr(error, 'description') else "Access forbidden",
            "instance": request.url
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
            "title": "Not Found",
            "status": 404,
            "detail": str(error.description) if hasattr(error, 'description') else "Resource not found",
            "instance": request.url
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc4918#section-11.2",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": str(error.description) if hasattr(error, 'description') else "Unprocessable entity",
            "instance": request.url
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An internal server error occurred",
            "instance": request.url
        }), 500
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        """Handle Marshmallow validation errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc4918#section-11.2",
            "title": "Validation Error",
            "status": 422,
            "detail": "Input validation failed",
            "errors": error.messages,
            "instance": request.url
        }), 422
    
    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        """Handle database integrity errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc4918#section-11.2",
            "title": "Database Integrity Error",
            "status": 422,
            "detail": "Database constraint violation",
            "instance": request.url
        }), 422
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """Handle general database errors."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
            "title": "Database Error",
            "status": 500,
            "detail": "A database error occurred",
            "instance": request.url
        }), 500
    
    @app.errorhandler(HTTPException)
    def http_exception(error):
        """Handle HTTP exceptions."""
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5",
            "title": error.name,
            "status": error.code,
            "detail": error.description,
            "instance": request.url
        }), error.code

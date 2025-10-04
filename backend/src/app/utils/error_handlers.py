"""Global error handlers for the Flask application."""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError
from marshmallow import ValidationError as MarshmallowValidationError

from .exceptions import APIException


def register_error_handlers(app: Flask):
    """Register common error handlers for the Flask application."""

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        """Handle custom API exceptions."""
        response = jsonify({
            "status": e.status_code,
            "title": e.__class__.__name__,
            "detail": e.detail,
            "code": e.code,
            "type": f"about:blank?type={e.status_code}",
        })
        response.status_code = e.status_code
        return response

    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation_error(e):
        """Handle Pydantic validation errors."""
        response = jsonify({
            "status": 422,
            "title": "Validation Error",
            "detail": "Input validation failed",
            "code": "validation_error",
            "type": "about:blank?type=422",
            "errors": e.errors(),
            "body": e.model._get_model_dump() if hasattr(e, 'model') else None,
        })
        response.status_code = 422
        return response

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(e):
        """Handle Marshmallow validation errors."""
        response = jsonify({
            "status": 422,
            "title": "Validation Error", 
            "detail": "Input validation failed",
            "code": "validation_error",
            "type": "about:blank?type=422",
            "errors": e.messages,
        })
        response.status_code = 422
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions (e.g., 404, 500)."""
        response = e.get_response()
        if response is not None:
            # If the exception already has a response, use it
            return response

        # For other HTTP exceptions, create a JSON response
        response = jsonify(
            {
                "status": e.code,
                "title": e.name,
                "detail": e.description,
                "type": f"about:blank?type={e.code}",
            }
        )
        response.status_code = e.code
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Handle generic exceptions (e.g., unhandled errors)."""
        app.logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
        
        # Log additional context for debugging
        if request:
            app.logger.error(f"Request URL: {request.url}")
            app.logger.error(f"Request Method: {request.method}")
            app.logger.error(f"Request Headers: {dict(request.headers)}")
            if request.is_json:
                app.logger.error(f"Request JSON: {request.get_json()}")
        
        response = jsonify(
            {
                "status": 500,
                "title": "Internal Server Error",
                "detail": "An unexpected error occurred.",
                "type": "about:blank?type=500",
            }
        )
        response.status_code = 500
        return response
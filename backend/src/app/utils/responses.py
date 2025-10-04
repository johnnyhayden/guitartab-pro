"""Standardized response utilities for the GuitarTab Pro API."""

from typing import Any, Dict, List, Optional, Union
from flask import jsonify, Response

from ..schemas.song import SongResponseSchema, SongListResponseSchema


class APIResponse:
    """Utility class for creating standardized API responses."""
    
    @staticmethod
    def success(
        message: str,
        data: Optional[Any] = None,
        status_code: int = 200,
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple[Response, int]:
        """Create a successful response."""
        response_data = {"message": message}
        
        if data is not None:
            response_data["data"] = data
        
        if meta is not None:
            response_data["meta"] = meta
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def created(
        message: str,
        data: Optional[Any] = None,
        location: Optional[str] = None
    ) -> tuple[Response, int, dict]:
        """Create a 201 Created response."""
        response_data = {"message": message}
        
        if data is not None:
            response_data["data"] = data
        
        headers = {}
        if location is not None:
            headers["Location"] = location
        
        return jsonify(response_data), 201, headers
    
    @staticmethod
    def no_content() -> tuple[Response, int]:
        """Create a 204 No Content response."""
        return "", 204
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int,
        per_page: int,
        message: str = "Success"
    ) -> tuple[Response, int]:
        """Create a paginated response."""
        total_pages = (total + per_page - 1) // per_page
        
        response_data = {
            "message": message,
            "items": items,
            "meta": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return jsonify(response_data), 200
    
    @staticmethod
    def bad_request(message: str, errors: Optional[Dict[str, Any]] = None) -> tuple[Response, int]:
        """Create a 400 Bad Request response."""
        response_data = {"message": message}
        
        if errors is not None:
            response_data["errors"] = errors
        
        return jsonify(response_data), 400
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> tuple[Response, int]:
        """Create a 401 Unauthorized response."""
        return jsonify({"message": message}), 401
    
    @staticmethod
    def forbidden(message: str = "Permission denied") -> tuple[Response, int]:
        """Create a 403 Forbidden response."""
        return jsonify({"message": message}), 403
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> tuple[Response, int]:
        """Create a 404 Not Found response."""
        return jsonify({"message": message}), 404
    
    @staticmethod
    def conflict(message: str = "Resource conflict") -> tuple[Response, int]:
        """Create a 409 Conflict response."""
        return jsonify({"message": message}), 409
    
    @staticmethod
    def unprocessable_entity(message: str, errors: Optional[Dict[str, Any]] = None) -> tuple[Response, int]:
        """Create a 422 Unprocessable Entity response."""
        response_data = {"message": message}
        
        if errors is not None:
            response_data["errors"] = errors
        
        return jsonify(response_data), 422
    
    @staticmethod
    def too_many_requests(message: str = "Rate limit exceeded") -> tuple[Response, int]:
        """Create a 429 Too Many Requests response."""
        return jsonify({"message": message}), 429
    
    @staticmethod
    def internal_server_error(message: str = "Internal server error") -> tuple[Response, int]:
        """Create a 500 Internal Server Error response."""
        return jsonify({"message": message}), 500


class SchemaResponse:
    """Utility class for creating responses using Pydantic schemas."""
    
    @staticmethod
    def song_response(song: Any) -> tuple[Response, int]:
        """Create a single song response."""
        schema_data = SongResponseSchema.model_validate(song).model_dump()
        return APIResponse.success("Song retrieved successfully", data=schema_data)
    
    @staticmethod
    def songs_list_response(
        songs: List[Any],
        total: int,
        page: int,
        per_page: int
    ) -> tuple[Response, int]:
        """Create a paginated songs list response."""
        schema_data = [
            SongResponseSchema.model_validate(song).model_dump() 
            for song in songs
        ]
        
        return APIResponse.paginated(
            items=schema_data,
            total=total,
            page=page,
            per_page=per_page,
            message="Songs retrieved successfully"
        )
    
    @staticmethod
    def song_created(song: Any, location: Optional[str] = None) -> tuple[Response, int, dict]:
        """Create a song created response."""
        schema_data = SongResponseSchema.model_validate(song).model_dump()
        headers = {}
        
        if location:
            headers["Location"] = location
        elif hasattr(song, 'id'):
            headers["Location"] = f"/api/songs/{song.id}"
        
        return APIResponse.created(
            message="Song created successfully",
            data=schema_data,
            location=headers.get("Location")
        ), 201, headers
    
    @staticmethod
    def song_updated(song: Any) -> tuple[Response, int]:
        """Create a song updated response."""
        schema_data = SongResponseSchema.model_validate(song).model_dump()
        return APIResponse.success("Song updated successfully", data=schema_data)
    
    @staticmethod
    def song_deleted() -> tuple[Response, int]:
        """Create a song deleted response."""
        return APIResponse.no_content()


class ErrorResponse:
    """Utility class for creating error responses."""
    
    @staticmethod
    def from_exception(exception: Exception) -> tuple[Response, int]:
        """Create an error response from an exception."""
        if hasattr(exception, 'status_code') and hasattr(exception, 'detail'):
            return jsonify({
                "message": exception.detail,
                "code": getattr(exception, 'code', 'unknown'),
                "errors": getattr(exception, 'errors', None)
            }), exception.status_code
        
        return APIResponse.internal_server_error(f"Unexpected error: {str(exception)}")
    
    @staticmethod
    def validation_error(errors: Dict[str, Any]) -> tuple[Response, int]:
        """Create a validation error response."""
        return APIResponse.unprocessable_entity("Validation failed", errors=errors)
    
    @staticmethod
    def service_error(message: str, status_code: int = 500) -> tuple[Response, int]:
        """Create a service error response."""
        return jsonify({"message": message}), status_code

"""Custom exception classes for the GuitarTab Pro API."""

from typing import Any, Dict, Optional


class APIException(Exception):
    """
    Base class for custom API exceptions.
    
    Follows RFC 7807 Problem Details for HTTP APIs.
    See: https://tools.ietf.org/html/rfc7807
    """
    
    status_code: int = 500
    default_detail: str = "A server error occurred."
    default_code: str = "server_error"

    def __init__(
        self, 
        detail: str = None, 
        status_code: int = None, 
        code: str = None,
        errors: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail if detail is not None else self.default_detail
        self.status_code = status_code if status_code is not None else self.status_code
        self.code = code if code is not None else self.default_code
        self.errors = errors
        super().__init__(self.detail)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        result = {
            "detail": self.detail, 
            "code": self.code,
            "status": self.status_code,
            "title": self.__class__.__name__
        }
        if self.errors:
            result["errors"] = self.errors
        return result


class ValidationError(APIException):
    """
    Exception raised for invalid input data.
    
    Maps to HTTP 400 Bad Request for client input errors,
    or HTTP 422 Unprocessable Entity for validation failures.
    """
    status_code = 422
    default_detail = "Invalid input data."
    default_code = "validation_error"

    def __init__(self, detail: str = None, errors: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, errors=errors)
        # Use 400 for simple validation errors, 422 for detailed validation failures
        if errors:
            self.status_code = 422


class NotFoundError(APIException):
    """Exception raised when a resource is not found."""
    status_code = 404
    default_detail = "Resource not found."
    default_code = "not_found"


class ConflictError(APIException):
    """Exception raised when there is a conflict, e.g., duplicate resource."""
    status_code = 409
    default_detail = "Resource conflict."
    default_code = "conflict"


class PermissionDeniedError(APIException):
    """Exception raised when a user does not have permission to perform an action."""
    status_code = 403
    default_detail = "Permission denied."
    default_code = "permission_denied"


class AuthenticationError(APIException):
    """Exception raised when authentication fails."""
    status_code = 401
    default_detail = "Authentication failed."
    default_code = "authentication_failed"


class UnauthorizedError(APIException):
    """Exception raised when a user is not authorized to access a resource."""
    status_code = 401
    default_detail = "Unauthorized access."
    default_code = "unauthorized"


class RateLimitError(APIException):
    """Exception raised when rate limit is exceeded."""
    status_code = 429
    default_detail = "Too many requests."
    default_code = "rate_limit_exceeded"


class ServiceUnavailableError(APIException):
    """Exception raised when a service is temporarily unavailable."""
    status_code = 503
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


# Convenience functions for common exceptions
def raise_validation_error(detail: str = None, errors: Optional[Dict[str, Any]] = None):
    """Raise a ValidationError with optional details."""
    raise ValidationError(detail=detail, errors=errors)


def raise_not_found(resource_name: str = "Resource"):
    """Raise a NotFoundError for a missing resource."""
    raise NotFoundError(detail=f"{resource_name} not found.")


def raise_permission_denied(action: str = "perform this action"):
    """Raise a PermissionDeniedError."""
    raise PermissionDeniedError(detail=f"You do not have permission to {action}.")


def raise_conflict(detail: str = None):
    """Raise a ConflictError."""
    raise ConflictError(detail=detail)


def raise_authentication_failed(detail: str = None):
    """Raise an AuthenticationError."""
    raise AuthenticationError(detail=detail)


def raise_unauthorized(detail: str = None):
    """Raise an UnauthorizedError."""
    raise UnauthorizedError(detail=detail)
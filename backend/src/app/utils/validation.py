"""Centralized validation utilities for the GuitarTab Pro API."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import re
from urllib.parse import urlparse

from ..utils.exceptions import ValidationError


class FieldValidator:
    """Utility class for validating common field types."""
    
    @staticmethod
    def validate_uuid(value: Any, field_name: str = "id") -> UUID:
        """Validate and convert a value to UUID."""
        if isinstance(value, UUID):
            return value
        
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                raise ValidationError(f"Invalid {field_name} format: must be a valid UUID")
        
        raise ValidationError(f"Invalid {field_name} format: expected string or UUID")
    
    @staticmethod
    def validate_email(email: str, field_name: str = "email") -> str:
        """Validate email format."""
        if not email or not isinstance(email, str):
            raise ValidationError(f"{field_name} is required")
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise ValidationError(f"Invalid {field_name} format")
        
        return email.strip().lower()
    
    @staticmethod
    def validate_password_strength(password: str, min_length: int = 8) -> str:
        """Validate password strength."""
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required")
        
        if len(password) < min_length:
            raise ValidationError(f"Password must be at least {min_length} characters long")
        
        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValidationError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return password
    
    @staticmethod
    def validate_url(url: str, field_name: str = "url", allow_empty: bool = True) -> Optional[str]:
        """Validate URL format."""
        if not url:
            if allow_empty:
                return None
            raise ValidationError(f"{field_name} is required")
        
        if not isinstance(url, str):
            raise ValidationError(f"Invalid {field_name} format: expected string")
        
        # Validate URL format
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"Invalid {field_name} format: must include protocol (http/https)")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError(f"Invalid {field_name} format: only HTTP and HTTPS protocols are allowed")
        
        return url.strip()
    
    @staticmethod
    def validate_pagination_params(
        page: Union[int, str],
        per_page: Union[int, str],
        max_per_page: int = 100
    ) -> tuple[int, int]:
        """Validate and normalize pagination parameters."""
        try:
            page = int(page) if isinstance(page, str) else page
            per_page = int(per_page) if isinstance(per_page, str) else per_page
        except (ValueError, TypeError):
            raise ValidationError("Invalid pagination parameters: page and per_page must be integers")
        
        if page < 1:
            raise ValidationError("Invalid page parameter: must be >= 1")
        
        if per_page < 1:
            raise ValidationError("Invalid per_page parameter: must be >= 1")
        
        if per_page > max_per_page:
            raise ValidationError(f"Invalid per_page parameter: maximum allowed is {max_per_page}")
        
        return page, per_page
    
    @staticmethod
    def validate_sort_parameters(
        sort_by: str,
        sort_order: Optional[str] = None,
        allowed_fields: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """Validate sorting parameters."""
        if not sort_by or not isinstance(sort_by, str):
            raise ValidationError("sort_by parameter is required")
        
        # Remove any potentially dangerous characters
        sort_by = re.sub(r'[^a-zA-Z0-9_-]', '', sort_by)
        
        if allowed_fields and sort_by not in allowed_fields:
            raise ValidationError(f"Invalid sort field '{sort_by}'. Allowed fields: {', '.join(allowed_fields)}")
        
        # Normalize sort order
        if sort_order:
            sort_order = sort_order.lower().strip()
            if sort_order not in ['asc', 'desc']:
                raise ValidationError("Invalid sort_order parameter: must be 'asc' or 'desc'")
        else:
            sort_order = 'sort_order'
        
        return sort_by, sort_order


class RequestValidator:
    """Utility class for validating request data."""
    
    @staticmethod
    def validate_query_params(
        params: Dict[str, Any], 
        required: Optional[List[str]] = None,
        optional: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate query parameters."""
        errors = {}
        
        # Check required parameters
        if required:
            for param in required:
                if param not in params or params[param] is None:
                    errors[param] = f"{param} parameter is required"
        
        # Check for unexpected parameters
        if optional:
            allowed_params = set(required or []) | set(optional)
            for param in params:
                if param not in allowed_params:
                    errors[param] = f"Unexpected parameter: {param}"
        
        if errors:
            raise ValidationError("Invalid query parameters", errors=errors)
        
        return params
    
    @staticmethod
    def validate_request_body(
        data: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        optional_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate request body data."""
        errors = {}
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors[field] = f"{field} field is required"
        
        # Check for unexpected fields
        if optional_fields:
            allowed_fields = set(required_fields or []) | set(optional_fields)
            for field in data:
                if field not in allowed_fields:
                    errors[field] = f"Unexpected field: {field}"
        
        if errors:
            raise ValidationError("Invalid request body", errors=errors)
        
        return data


class SchemaValidator:
    """Utility class for validating data against schemas."""
    
    @staticmethod
    def validate_model_data(
        data: Dict[str, Any],
        model_class: Any,
        context: Optional[str] = None
    ) -> Any:
        """Validate data against a Pydantic model."""
        try:
            return model_class(**data)
        except Exception as e:
            error_context = f" ({context})" if context else ""
            raise ValidationError(
                detail=f"Invalid data format{error_context}",
                errors=str(e)
            )
    
    @staticmethod
    def validate_field_constraints(
        data: Dict[str, Any],
        constraints: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate field constraints."""
        errors = {}
        
        for field, constraint in constraints.items():
            if field not in data:
                continue
            
            value = data[field]
            
            # Length constraints
            if 'min_length' in constraint:
                if isinstance(value, str) and len(value) < constraint['min_length']:
                    errors[field] = f"Minimum length: {constraint['min_length']}"
            
            if 'max_length' in constraint:
                if isinstance(value, str) and len(value) > constraint['max_length']:
                    errors[field] = f"Maximum length: {constraint['max_length']}"
            
            # Range constraints
            if 'min_value' in constraint:
                if isinstance(value, (int, float)) and value < constraint['min_value']:
                    errors[field] = f"Minimum value: {constraint['min_value']}"
            
            if 'max_value' in constraint:
                if isinstance(value, (int, float)) and value > constraint['max_value']:
                    errors[field] = f"Maximum value: {constraint['max_value']}"
            
            # Pattern constraints
            if 'pattern' in constraint:
                if isinstance(value, str) and not re.match(constraint['pattern'], value):
                    errors[field] = f"Invalid format: must match pattern {constraint['pattern']}"
        
        if errors:
            raise ValidationError("Field validation failed", errors=errors)
        
        return data

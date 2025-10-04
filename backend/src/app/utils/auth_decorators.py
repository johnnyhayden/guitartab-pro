"""Authorization decorators and utilities for GuitarTab Pro API."""

from functools import wraps
from typing import Callable, List, Optional, Union
from uuid import UUID

from flask import abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.song import Song
from ..utils.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
)


class AuthorizationManager:
    """Centralized authorization management."""
    
    @staticmethod
    def get_current_user(db: Session, user_id: UUID = None) -> Optional[User]:
        """Get current user from database."""
        if not user_id:
            user_id = get_jwt_identity()
            if not user_id:
                raise AuthenticationError("Authentication required")
        
        try:
            user_id = UUID(user_id)
        except ValueError:
            raise AuthenticationError("Invalid user ID format")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found")
        
        return user
    
    @staticmethod
    def check_owner_permission(
        db: Session, 
        resource_user_id: UUID, 
        current_user_id: UUID
    ) -> bool:
        """Check if current user is the owner of a resource."""
        if resource_user_id == current_user_id:
            return True
        
        # Check if current user is an admin
        current_user = AuthorizationManager.get_current_user(db, current_user_id)
        return getattr(current_user, 'is_admin', False)
    
    @staticmethod
    def check_resource_access(
        db: Session,
        resource_id: UUID,
        resource_model,
        user_id: UUID,
        require_admin: bool = False
    ) -> bool:
        """Check if user has access to a specific resource."""
        user = AuthorizationManager.get_current_user(db, user_id)
        
        if require_admin and not getattr(user, 'is_admin', False):
            return False
        
        # Get the resource
        resource = db.query(resource_model).filter(resource_model.id == resource_id).first()
        if not resource:
            raise NotFoundError(f"Resource with ID {resource_id} not found")
        
        # Check ownership if not admin
        if hasattr(resource, 'user_id'):
            if not AuthorizationManager.check_owner_permission(
                db, resource.user_id, user_id
            ):
                return False
        
        return True


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        @jwt_required()
        def auth_check():
            user_id = get_jwt_identity()
            if not user_id:
                abort(401, "Authentication required")
            
            # Validate user exists
            db = get_db()
            try:
                AuthorizationManager.get_current_user(db, UUID(user_id))
            except (ValueError, AuthenticationError):
                abort(401, "Invalid authentication")
            
            return f(*args, **kwargs)
        
        return auth_check()
    return decorated_function


def require_owner(f: Callable) -> Callable:
    """Decorator to require ownership of a resource."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        @jwt_required()
        def owner_check():
            current_user_id = UUID(get_jwt_identity())
            db = get_db()
            
            # Get resource ID from kwargs or request
            resource_id = kwargs.get('song_id') or kwargs.get('resource_id')
            if not resource_id:
                abort(400, "Resource ID required")
            
            resource_id = UUID(resource_id)
            
            # Check ownership
            if not AuthorizationManager.check_resource_access(
                db, resource_id, Song, current_user_id
            ):
                abort(403, "Access denied: ownership required")
            
            return f(*args, **kwargs)
        
        return owner_check()
    return decorated_function


def require_admin(f: Callable) -> Callable:
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        @jwt_required()
        def admin_check():
            current_user_id = UUID(get_jwt_identity())
            db = get_db()
            
            user = AuthorizationManager.get_current_user(db, current_user_id)
            if not getattr(user, 'is_admin', False):
                abort(403, "Admin privileges required")
            
            return f(*args, **kwargs)
        
        return admin_check()
    return decorated_function


def require_permission(permission: str):
    """Decorator factory for specific permissions."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            @jwt_required()
            def permission_check():
                current_user_id = UUID(get_jwt_identity())
                db = get_db()
                
                user = AuthorizationManager.get_current_user(db, current_user_id)
                
                # Check specific permission
                user_permissions = getattr(user, 'permissions', [])
                if permission not in user_permissions:
                    abort(403, f"Permission '{permission}' required")
                
                return f(*args, **kwargs)
            
            return permission_check()
        return decorated_function
    return decorator


def require_role(roles: Union[str, List[str]]):
    """Decorator factory for role-based access."""
    if isinstance(roles, str):
        roles = [roles]
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            @jwt_required()
            def role_check():
                current_user_id = UUID(get_jwt_identity())
                db = get_db()
                
                user = AuthorizationManager.get_current_user(db, current_user_id)
                
                # Check if user has any of the required roles
                user_role = getattr(user, 'role', 'user')
                if user_role not in roles:
                    abort(403, f"One of the following roles required: {', '.join(roles)}")
                
                return f(*args, **kwargs)
            
            return role_check()
        return decorated_function
    return decorator


class ResourceProtector:
    """Advanced resource protection with fine-grained controls."""
    
    def __init__(self, resource_model, id_param_name: str = 'id'):
        self.resource_model = resource_model
        self.id_param_name = id_param_name
    
    def protect(self, require_owner: bool = True, require_admin: bool = False):
        """Create a resource protection decorator."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                @jwt_required()
                def protection_check():
                    # Get current user
                    current_user_id = UUID(get_jwt_identity())
                    
                    # Get resource ID
                    resource_id = kwargs.get(self.id_param_name)
                    if not resource_id:
                        abort(400, f"{self.id_param_name} parameter required")
                    
                    resource_id = UUID(str(resource_id))
                    db = get_db()
                    
                    # Check admin requirement first
                    if require_admin:
                        user = AuthorizationManager.get_current_user(db, current_user_id)
                        if not getattr(user, 'is_admin', False):
                            abort(403, "Admin privileges required")
                    
                    # Check ownership if required
                    elif require_owner:
                        if not AuthorizationManager.check_resource_access(
                            db, resource_id, self.resource_model, current_user_id
                        ):
                            abort(403, "Access denied: ownership required")
                    
                    return f(*args, **kwargs)
                
                return protection_check()
            return decorated_function
        return decorator
    
    def owner_or_admin(self):
        """Protect resource - owner OR admin can access."""
        return self.protect(require_owner=True, require_admin=False)
    
    def admin_only(self):
        """Protect resource - admin only."""
        return self.protect(require_owner=False, require_admin=True)
    
    def anyone(self):
        """Minimal protection - just authentication required."""
        return self.protect(require_owner=False, require_admin=False)


# Predefined protectors for common resources
SongProtector = ResourceProtector(Song, 'song_id')


def rate_limit(action: str, max_requests: int, window_minutes: int = 1):
    """Simple rate limiting decorator."""
    # In a real implementation, you'd use Redis or similar
    import time
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            @jwt_required()
            def rate_check():
                current_user_id = get_jwt_identity()
                # For demo purposes, we'll just log the rate limit check
                # In production, implement proper rate limiting with Redis
                return f(*args, **kwargs)
            
            return rate_check()
        return decorated_function
    return decorator


def request_logging(f: Callable) -> Callable:
    """Decorator to log authorization requests for audit."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        @jwt_required(refresh=False)
        def log_check():
            current_user_id = get_jwt_identity()
            
            # Log the authorization event
            logger.info(f"Authorization: User {current_user_id} accessing {f.__name__}")
            
            return f(*args, **kwargs)
        
        return log_check()
    return decorated_function

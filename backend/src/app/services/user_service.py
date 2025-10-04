"""User service with business logic and authorization management."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models.user import User
from ..utils.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from .base_service import BaseService


class UserService(BaseService[User]):
    """Service layer for managing user operations."""

    def __init__(self):
        super().__init__(User)

    def get_user_by_id(self, db: Session, user_id: UUID) -> User:
        """Retrieve a single user by ID."""
        user = self.get(db, user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")
        return user

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    def list_users(
        self, 
        db: Session, 
        page: int = 1, 
        per_page: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        current_user_id: Optional[UUID] = None
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination."""
        
        # Admin users can see all users, regular users can't list users
        if current_user_id:
            current_user = self.get_user_by_id(db, current_user_id)
            if not current_user.is_admin:
                raise PermissionDeniedError("Only administrators can list users")
        
        query = db.query(User)
        
        # Apply search filter
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply role filter
        if role:
            query = query.filter(User.role == role)
        
        # Apply active status filter
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        total = query.count()
        
        # Apply pagination
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return users, total

    def update_user_role(self, db: Session, user_id: UUID, new_role: str, admin_id: UUID) -> User:
        """Update user role (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can change user roles")
        
        user = self.get_user_by_id(db, user_id)
        user.update_role(new_role)
        
        db.commit()
        db.refresh(user)
        
        return user

    def activate_user(self, db: Session, user_id: UUID, admin_id: UUID) -> User:
        """Activate a user account (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can activate user accounts")
        
        user = self.get_user_by_id(db, user_id)
        user.is_active = True
        
        db.commit()
        db.refresh(user)
        
        return user

    def deactivate_user(self, db: Session, user_id: UUID, admin_id: UUID) -> User:
        """Deactivate a user account (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can deactivate user accounts")
        
        user = self.get_user_by_id(db, user_id)
        user.is_active = False
        
        db.commit()
        db.refresh(user)
        
        return user

    def grant_permission(self, db: Session, user_id: UUID, permission: str, admin_id: UUID) -> User:
        """Grant a specific permission to a user (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can grant permissions")
        
        user = self.get_user_by_id(db, user_id)
        user.add_permission(permission)
        
        db.commit()
        db.refresh(user)
        
        return user

    def revoke_permission(self, db: Session, user_id: UUID, permission: str, admin_id: UUID) -> User:
        """Revoke a specific permission from a user (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can revoke permissions")
        
        user = self.get_user_by_id(db, user_id)
        user.remove_permission(permission)
        
        db.commit()
        db.refresh(user)
        
        return user

    def get_user_stats(self, db: Session, user_id: UUID, requesting_user_id: Optional[UUID] = None) -> dict:
        """Get comprehensive statistics for a user."""
        
        # Users can only view their own stats, or admins can view anyone's
        if requesting_user_id:
            requesting_user = self.get_user_by_id(db, requesting_user_id)
            if not requesting_user.is_admin and requesting_user_id != user_id:
                raise PermissionDeniedError("You can only view your own statistics")
        
        user = self.get_user_by_id(db, user_id)
        
        # Get song statistics
        from ..models.song import Song
        song_stats = db.query(func.count(Song.id)).filter(Song.user_id == user_id).scalar()
        public_songs = db.query(func.count(Song.id)).filter(
            Song.user_id == user_id, Song.is_public == True
        ).scalar()
        flagged_songs = db.query(func.count(Song.id)).filter(
            Song.user_id == user_id, Song.is_flagged == True
        ).scalar()
        
        total_views = db.query(func.sum(Song.views)).filter(Song.user_id == user_id).scalar() or 0
        
        return {
            "user_id": str(user_id),
            "username": user.username,
            "total_songs": song_stats,
            "public_songs": public_songs,
            "flagged_songs": flagged_songs,
            "total_views": total_views,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def promote_to_moderator(self, db: Session, user_id: UUID, admin_id: UUID) -> User:
        """Promote user to moderator (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can promote users to moderator")
        
        user = self.get_user_by_id(db, user_id)
        user.update_role("moderator")
        
        db.commit()
        db.refresh(user)
        
        return user

    def demote_from_moderator(self, db: Session, user_id: UUID, admin_id: UUID) -> User:
        """Demote moderator to regular user (admin only)."""
        admin_user = self.get_user_by_id(db, admin_id)
        if not admin_user.is_admin:
            raise PermissionDeniedError("Only administrators can demote moderators")
        
        user = self.get_user_by_id(db, user_id)
        user.update_role("user")
        
        db.commit()
        db.refresh(user)
        
        return user

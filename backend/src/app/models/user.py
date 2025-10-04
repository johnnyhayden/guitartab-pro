"""User model for GuitarTab Pro application."""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, DateTime, String, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from ..database import Base


class User(Base):
    """Represents a user in the GuitarTab Pro application."""

    __tablename__ = "users"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: str = Column(String(50), unique=True, nullable=False)
    email: str = Column(String(100), unique=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    first_name: Optional[str] = Column(String(100), nullable=True)
    last_name: Optional[str] = Column(String(100), nullable=True)
    
    # Authorization fields
    role: str = Column(String(20), default="user", nullable=False)  # user, moderator, admin
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_admin: bool = Column(Boolean, default=False, nullable=False)
    is_moderator: bool = Column(Boolean, default=False, nullable=False)
    permissions: Dict[str, Any] = Column(JSON, default=dict, nullable=False)
    
    # Profile fields
    bio: Optional[str] = Column(Text, nullable=True)
    avatar_url: Optional[str] = Column(String(500), nullable=True)
    website_url: Optional[str] = Column(String(500), nullable=True)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    songs: Mapped[List["Song"]] = relationship("Song", back_populates="uploader")
    songlists: Mapped[List["Songlist"]] = relationship("Songlist", back_populates="owner")
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", uselist=False
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    @property
    def initials(self) -> str:
        """Get user's initials."""
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials or self.username[0:2].upper()

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_admin:
            return True  # Admins have all permissions
        
        # Check role-based permissions
        role_permissions = self._get_role_permissions()
        if permission in role_permissions:
            return True
        
        # Check explicit permissions
        return permission in self.permissions.get('explicit', [])

    def can_read_resource(self, resource_user_id: UUID) -> bool:
        """Check if user can read a resource."""
        if self.is_admin or self.id == resource_user_id:
            return True
        return False

    def can_write_resource(self, resource_user_id: UUID) -> bool:
        """Check if user can modify a resource."""
        if self.is_admin or self.is_moderator:
            return True
        return self.id == resource_user_id

    def can_delete_resource(self, resource_user_id: UUID) -> bool:
        """Check if user can delete a resource."""
        if self.is_admin:
            return True
        return self.id == resource_user_id

    def can_moderate(self) -> bool:
        """Check if user can moderate content."""
        return self.is_moderator or self.is_admin

    def _get_role_permissions(self) -> List[str]:
        """Get permissions based on user role."""
        role_permissions = {
            "user": [
                "read:own_songs",
                "write:own_songs", 
                "delete:own_songs",
                "read:public_songs",
                "read:filter_options",
                "rate:songs"
            ],
            "moderator": [
                "read:any_songs",
                "write:any_songs",
                "moderate:songs",
                "read:song_reports",
                "manage:song_flags"
            ],
            "admin": [
                "manage:users",
                "manage:system",
                "manage:songs",
                "manage:content",
                "view:analytics",
                "manage:roles"
            ]
        }
        return role_permissions.get(self.role, [])

    def add_permission(self, permission: str) -> None:
        """Add a specific permission to user."""
        if 'explicit' not in self.permissions:
            self.permissions['explicit'] = []
        if permission not in self.permissions['explicit']:
            self.permissions['explicit'].append(permission)

    def remove_permission(self, permission: str) -> None:
        """Remove a specific permission from user."""
        if 'explicit' in self.permissions:
            self.permissions['explicit'] = [
                p for p in self.permissions['explicit'] if p != permission
            ]

    def update_role(self, new_role: str) -> None:
        """Update user role."""
        valid_roles = ["user", "moderator", "admin"]
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role: {new_role}. Valid roles: {valid_roles}")
        
        old_role = self.role
        self.role = new_role
        
        # Update boolean flags based on role
        self.is_admin = new_role == "admin"
        self.is_moderator = new_role == "moderator"
        
        # Clear explicit permissions on role change
        self.permissions = {'explicit': []}

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary."""
        data = {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "initials": self.initials,
            "role": self.role,
            "is_active": self.is_active,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "website_url": self.website_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if self.is_admin and include_sensitive:
            data.update({
                "permissions": self.permissions,
                "has_role": self.has_role,
                "has_permission": self.has_permission,
            })
        
        return data

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"
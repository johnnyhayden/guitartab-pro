"""User model for authentication and user management."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    # Primary key
    user_id = Column(String(36), primary_key=True, index=True)

    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    songs = relationship("Song", back_populates="creator", cascade="all, delete-orphan")
    songlists = relationship("Songlist", back_populates="owner", cascade="all, delete-orphan")
    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.user_id}, username={self.username}, email={self.email})>"

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

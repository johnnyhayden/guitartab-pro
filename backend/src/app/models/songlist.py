"""Songlist model for organizing songs into collections."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Songlist(Base):
    """Songlist model for organizing songs into collections."""

    __tablename__ = "songlists"

    # Primary key
    songlist_id = Column(String(36), primary_key=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Visibility and sharing
    is_public = Column(Boolean, default=False, nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="songlists")
    songlist_songs = relationship(
        "SonglistSong", back_populates="songlist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Songlist."""
        return f"<Songlist(id={self.songlist_id}, name={self.name}, user_id={self.user_id})>"

    @property
    def song_count(self) -> int:
        """Get the number of songs in this songlist."""
        return len(self.songlist_songs)

    @property
    def songs(self) -> List["Song"]:
        """Get all songs in this songlist, ordered by position."""
        return [
            songlist_song.song
            for songlist_song in sorted(self.songlist_songs, key=lambda x: x.position)
        ]

    def to_dict(self) -> dict:
        """Convert songlist to dictionary."""
        return {
            "songlist_id": self.songlist_id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "is_shared": self.is_shared,
            "user_id": self.user_id,
            "song_count": self.song_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

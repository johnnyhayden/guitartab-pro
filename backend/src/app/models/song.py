"""Song model for storing song metadata, chords, and lyrics."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Song(Base):
    """Song model for storing song metadata, chords, and lyrics."""

    __tablename__ = "songs"

    # Primary key
    song_id = Column(String(36), primary_key=True, index=True)

    # Basic song information
    title = Column(String(500), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=True, index=True)

    # Musical information
    key = Column(String(10), nullable=True)  # e.g., "C", "Am", "F#m"
    tempo = Column(Integer, nullable=True)  # BPM
    difficulty_level = Column(Integer, nullable=True)  # 1-10 scale
    capo_position = Column(Integer, nullable=True, default=0)

    # Song content
    chord_progression = Column(Text, nullable=True)  # JSON or custom format
    lyrics = Column(Text, nullable=True)
    tablature = Column(Text, nullable=True)  # Guitar tab

    # Source information
    source = Column(String(100), nullable=True)  # e.g., "ultimate_guitar", "songsterr"
    source_id = Column(String(255), nullable=True, index=True)
    source_url = Column(String(500), nullable=True)

    # Metadata
    duration_seconds = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_original = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    created_by = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="songs")
    songlist_songs = relationship(
        "SonglistSong", back_populates="song", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Song."""
        return f"<Song(id={self.song_id}, title={self.title}, artist={self.artist})>"

    @property
    def display_name(self) -> str:
        """Get the song's display name."""
        return f"{self.title} by {self.artist}"

    def to_dict(self) -> dict:
        """Convert song to dictionary."""
        return {
            "song_id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "key": self.key,
            "tempo": self.tempo,
            "difficulty_level": self.difficulty_level,
            "capo_position": self.capo_position,
            "chord_progression": self.chord_progression,
            "lyrics": self.lyrics,
            "tablature": self.tablature,
            "source": self.source,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "duration_seconds": self.duration_seconds,
            "is_public": self.is_public,
            "is_original": self.is_original,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

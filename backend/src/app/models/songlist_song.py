"""SonglistSong junction model for many-to-many relationship between songlists and songs."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class SonglistSong(Base):
    """SonglistSong junction model for many-to-many relationship between songlists and songs."""

    __tablename__ = "songlist_songs"

    # Primary key (composite)
    songlist_id = Column(String(36), ForeignKey("songlists.songlist_id"), primary_key=True)
    song_id = Column(String(36), ForeignKey("songs.song_id"), primary_key=True)

    # Ordering and metadata
    position = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    songlist = relationship("Songlist", back_populates="songlist_songs")
    song = relationship("Song", back_populates="songlist_songs")

    # Constraints
    __table_args__ = (UniqueConstraint("songlist_id", "position", name="uk_songlist_position"),)

    def __repr__(self) -> str:
        """String representation of SonglistSong."""
        return f"<SonglistSong(songlist_id={self.songlist_id}, song_id={self.song_id}, position={self.position})>"

    def to_dict(self) -> dict:
        """Convert songlist_song to dictionary."""
        return {
            "songlist_id": self.songlist_id,
            "song_id": self.song_id,
            "position": self.position,
            "notes": self.notes,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }

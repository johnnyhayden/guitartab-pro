"""Song model for GuitarTab Pro application."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from ..database import Base


class Song(Base):
    """Represents a song in the GuitarTab Pro application."""

    __tablename__ = "songs"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: UUID = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: str = Column(String(255), nullable=False)
    artist: str = Column(String(255), nullable=False)
    album: Optional[str] = Column(String(255), nullable=True)
    lyrics: Optional[str] = Column(Text, nullable=True)
    chords: Optional[str] = Column(Text, nullable=True)
    tab: Optional[str] = Column(Text, nullable=True)
    genre: Optional[str] = Column(String(100), nullable=True)
    year: Optional[int] = Column(Integer, nullable=True)
    source_url: Optional[str] = Column(String(500), nullable=True)
    
    # Visibility and moderation
    is_public: bool = Column(Boolean, default=True, nullable=False)
    is_featured: bool = Column(Boolean, default=False, nullable=False)
    is_flagged: bool = Column(Boolean, default=False, nullable=False)
    flagged_reason: Optional[str] = Column(String(500), nullable=True)
    
    # Statistics
    views: int = Column(Integer, default=0, nullable=False)
    rating: float = Column(Float, default=0.0, nullable=False)
    rating_count: int = Column(Integer, default=0, nullable=False)
    difficulty: int = Column(Integer, default=1, nullable=False)  # 1-5 scale
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # Moderator actions
    moderated_at: Optional[datetime] = Column(DateTime, nullable=True)
    moderated_by: Optional[UUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    uploader: Mapped["User"] = relationship("User", back_populates="songs")
    moderator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[moderated_by])
    songlist_associations: Mapped[List["SonglistSong"]] = relationship(
        "SonglistSong", back_populates="song", cascade="all, delete-orphan"
    )

    @property
    def is_moderated(self) -> bool:
        """Check if song has been moderated."""
        return self.moderated_at is not None

    @property
    def is_approved(self) -> bool:
        """Check if song is approved by moderator."""
        return self.is_moderated and not self.is_flagged

    def can_be_viewed_by(self, user_id: UUID = None, is_admin: bool = False, is_moderator: bool = False) -> bool:
        """Check if song can be viewed by a specific user."""
        # Admins and moderators can view everything
        if is_admin or is_moderator:
            return True
        
        # Owner can always view their songs
        if user_id == self.user_id:
            return True
        
        # Public songs are viewable by everyone
        return self.is_public and self.is_approved

    def can_be_edited_by(self, user_id: UUID = None, is_admin: bool = False, is_moderator: bool = False) -> bool:
        """Check if song can be edited by a specific user."""
        # Admins can edit everything
        if is_admin:
            return True
        
        # Moderators can edit flagged or flagged songs
        if is_moderator and (self.is_flagged or not self.is_public):
            return True
        
        # Owners can edit their own songs
        if user_id == self.user_id:
            return True
        
        return False

    def can_be_deleted_by(self, user_id: UUID = None, is_admin: bool = False, is_moderator: bool = False) -> bool:
        """Check if song can be deleted by a specific user."""
        # Admins can delete everything
        if is_admin:
            return True
        
        # Moderators can delete flagged content
        if is_moderator and self.is_flagged:
            return True
        
        # Owners can delete their own songs
        if user_id == self.user_id:
            return True
        
        return False

    def flag_song(self, reason: str, moderator_id: UUID = None) -> None:
        """Flag a song for moderation."""
        self.is_flagged = True
        self.flagged_reason = reason
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()

    def unflag_song(self, moderator_id: UUID = None) -> None:
        """Remove flag from song."""
        self.is_flagged = False
        self.flagged_reason = None
        if moderator_id:
            self.moderated_by = moderator_id
            self.moderated_at = datetime.utcnow()

    def set_featured(self, featured: bool = True) -> None:
        """Set or unset featured status."""
        self.is_featured = featured

    def make_public(self, public: bool = True) -> None:
        """Make song public or private."""
        self.is_public = public
        # If making public, ensure it's not flagged
        if public and self.is_flagged:
            self.unflag_song()

    def increment_views(self) -> None:
        """Increment view count."""
        self.views += 1
        self.updated_at = datetime.utcnow()

    def update_rating(self, new_rating: float) -> None:
        """Update average rating."""
        # Simple average calculation - in production you might want weighted averages
        if self.rating_count == 0:
            self.rating = new_rating
            self.rating_count = 1
        else:
            total_rating = self.rating * self.rating_count
            self.rating_count += 1
            self.rating = (total_rating + new_rating) / self.rating_count
        
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        visibility = "Public" if self.is_public else "Private"
        flagged = " (Flagged)" if self.is_flagged else ""
        return f"<Song(title='{self.title}', artist='{self.artist}' {visibility}{flagged})>"
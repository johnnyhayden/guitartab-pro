"""UserPreferences model for storing user-specific display and behavior settings."""

from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class UserPreferences(Base):
    """UserPreferences model for storing user-specific display and behavior settings."""

    __tablename__ = "user_preferences"

    # Primary key (one-to-one with User)
    user_id = Column(String(36), ForeignKey("users.user_id"), primary_key=True)

    # Display preferences
    chord_color = Column(String(7), nullable=True, default="#FF6B6B")  # Hex color
    lyric_color = Column(String(7), nullable=True, default="#333333")  # Hex color
    background_color = Column(String(7), nullable=True, default="#FFFFFF")  # Hex color
    title_color = Column(String(7), nullable=True, default="#2C3E50")  # Hex color
    font_size = Column(Integer, nullable=True, default=16)  # Font size in pixels
    font_family = Column(String(100), nullable=True, default="Arial, sans-serif")

    # Behavior preferences
    auto_scroll_speed = Column(Integer, nullable=True, default=50)  # Scroll speed (1-100)
    auto_scroll_enabled = Column(Boolean, nullable=True, default=False)
    metronome_enabled = Column(Boolean, nullable=True, default=False)
    metronome_volume = Column(Integer, nullable=True, default=50)  # Volume (0-100)
    metronome_tempo = Column(Integer, nullable=True, default=120)  # Default BPM

    # Display mode preferences
    display_mode = Column(
        String(20), nullable=True, default="chords_above"
    )  # chords_above, chords_inline, tab_only
    show_capo = Column(Boolean, nullable=True, default=True)
    show_key = Column(Boolean, nullable=True, default=True)
    show_tempo = Column(Boolean, nullable=True, default=True)
    show_difficulty = Column(Boolean, nullable=True, default=True)

    # Advanced settings (stored as JSON)
    metronome_settings = Column(JSONB, nullable=True, default=dict)
    display_settings = Column(JSONB, nullable=True, default=dict)
    keyboard_shortcuts = Column(JSONB, nullable=True, default=dict)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        """String representation of UserPreferences."""
        return f"<UserPreferences(user_id={self.user_id})>"

    def to_dict(self) -> dict:
        """Convert user preferences to dictionary."""
        return {
            "user_id": self.user_id,
            "chord_color": self.chord_color,
            "lyric_color": self.lyric_color,
            "background_color": self.background_color,
            "title_color": self.title_color,
            "font_size": self.font_size,
            "font_family": self.font_family,
            "auto_scroll_speed": self.auto_scroll_speed,
            "auto_scroll_enabled": self.auto_scroll_enabled,
            "metronome_enabled": self.metronome_enabled,
            "metronome_volume": self.metronome_volume,
            "metronome_tempo": self.metronome_tempo,
            "display_mode": self.display_mode,
            "show_capo": self.show_capo,
            "show_key": self.show_key,
            "show_tempo": self.show_tempo,
            "show_difficulty": self.show_difficulty,
            "metronome_settings": self.metronome_settings,
            "display_settings": self.display_settings,
            "keyboard_shortcuts": self.keyboard_shortcuts,
        }

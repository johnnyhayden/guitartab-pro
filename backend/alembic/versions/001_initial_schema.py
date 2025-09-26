"""Initial database schema with all core tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all core tables."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_user_id"), "users", ["user_id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    # Create songs table
    op.create_table(
        "songs",
        sa.Column("song_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("artist", sa.String(255), nullable=False),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("key", sa.String(10), nullable=True),
        sa.Column("tempo", sa.Integer(), nullable=True),
        sa.Column("difficulty_level", sa.Integer(), nullable=True),
        sa.Column("capo_position", sa.Integer(), nullable=True, default=0),
        sa.Column("chord_progression", sa.Text(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("tablature", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_original", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("song_id"),
    )
    op.create_index(op.f("ix_songs_song_id"), "songs", ["song_id"], unique=False)
    op.create_index(op.f("ix_songs_title"), "songs", ["title"], unique=False)
    op.create_index(op.f("ix_songs_artist"), "songs", ["artist"], unique=False)
    op.create_index(op.f("ix_songs_genre"), "songs", ["genre"], unique=False)
    op.create_index(op.f("ix_songs_source_id"), "songs", ["source_id"], unique=False)
    op.create_index(op.f("ix_songs_created_by"), "songs", ["created_by"], unique=False)

    # Create songlists table
    op.create_table(
        "songlists",
        sa.Column("songlist_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_shared", sa.Boolean(), nullable=False, default=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("songlist_id"),
    )
    op.create_index(op.f("ix_songlists_songlist_id"), "songlists", ["songlist_id"], unique=False)
    op.create_index(op.f("ix_songlists_name"), "songlists", ["name"], unique=False)
    op.create_index(op.f("ix_songlists_user_id"), "songlists", ["user_id"], unique=False)

    # Create songlist_songs table
    op.create_table(
        "songlist_songs",
        sa.Column("songlist_id", sa.String(36), nullable=False),
        sa.Column("song_id", sa.String(36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, default=0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["song_id"],
            ["songs.song_id"],
        ),
        sa.ForeignKeyConstraint(
            ["songlist_id"],
            ["songlists.songlist_id"],
        ),
        sa.PrimaryKeyConstraint("songlist_id", "song_id"),
        sa.UniqueConstraint("songlist_id", "position", name="uk_songlist_position"),
    )

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("chord_color", sa.String(7), nullable=True, default="#FF6B6B"),
        sa.Column("lyric_color", sa.String(7), nullable=True, default="#333333"),
        sa.Column("background_color", sa.String(7), nullable=True, default="#FFFFFF"),
        sa.Column("title_color", sa.String(7), nullable=True, default="#2C3E50"),
        sa.Column("font_size", sa.Integer(), nullable=True, default=16),
        sa.Column("font_family", sa.String(100), nullable=True, default="Arial, sans-serif"),
        sa.Column("auto_scroll_speed", sa.Integer(), nullable=True, default=50),
        sa.Column("auto_scroll_enabled", sa.Boolean(), nullable=True, default=False),
        sa.Column("metronome_enabled", sa.Boolean(), nullable=True, default=False),
        sa.Column("metronome_volume", sa.Integer(), nullable=True, default=50),
        sa.Column("metronome_tempo", sa.Integer(), nullable=True, default=120),
        sa.Column("display_mode", sa.String(20), nullable=True, default="chords_above"),
        sa.Column("show_capo", sa.Boolean(), nullable=True, default=True),
        sa.Column("show_key", sa.Boolean(), nullable=True, default=True),
        sa.Column("show_tempo", sa.Boolean(), nullable=True, default=True),
        sa.Column("show_difficulty", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "metronome_settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=dict,
        ),
        sa.Column(
            "display_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=dict
        ),
        sa.Column(
            "keyboard_shortcuts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            default=dict,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("user_preferences")
    op.drop_table("songlist_songs")
    op.drop_table("songlists")
    op.drop_table("songs")
    op.drop_table("users")

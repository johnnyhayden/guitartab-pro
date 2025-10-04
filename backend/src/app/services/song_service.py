"""Song service with business logic and data access."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from ..models.song import Song
from ..schemas.song import SongCreateSchema, SongUpdateSchema, SongQueryParams
from ..utils.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from .base_service import BaseService


class SongService(BaseService[Song]):
    """
    Service layer for managing song operations.
    Extends BaseService to provide specific song-related business logic.
    """

    def __init__(self):
        super().__init__(Song)

    def create_song(self, db: Session, song_in: SongCreateSchema, user_id: UUID) -> Song:
        """Create a new song for a given user."""
        return self.create(db, song_in.model_dump(), user_id)

    def get_song(self, db: Session, song_id: UUID) -> Song:
        """Retrieve a single song by its ID."""
        song = self.get(db, song_id)
        if not song:
            raise NotFoundError(f"Song with ID {song_id} not found.")
        return song

    def list_songs(
        self, db: Session, query_params: SongQueryParams, current_user_id: Optional[UUID] = None
    ) -> Tuple[List[Song], int]:
        """
        Retrieve a list of songs based on various query parameters,
        including search, filters, pagination, and sorting.
        """
        query = db.query(self.model)

        # Apply scope filtering
        if query_params.user_id:
            query = query.filter(self.model.user_id == query_params.user_id)
        elif current_user_id:
            query = query.filter(self.model.user_id == current_user_id)
        else:
            # Default to public songs if no user context
            query = query.filter(self.model.is_public == True)

        # Apply search filter
        if query_params.search:
            search = f"%{query_params.search}%"
            search_filter = or_(
                self.model.title.ilike(search),
                self.model.artist.ilike(search),
                self.model.album.ilike(search)
            )
            query = query.filter(search_filter)

        # Apply genre filter
        if query_params.genre:
            query = query.filter(self.model.genre.ilike(f"%{query_params.genre}%"))

        # Apply difficulty range filter
        if query_params.difficulty_min is not None:
            query = query.filter(self.model.difficulty >= query_params.difficulty_min)
        if query_params.difficulty_max is not None:
            query = query.filter(self.model.difficulty <= query_params.difficulty_max)

        # Apply year range filter
        if query_params.year_from is not None:
            query = query.filter(self.model.year >= query_params.year_from)
        if query_params.year_to is not None:
            query = query.filter(self.model.year <= query_params.year_to)

        # Apply is_public filter if explicitly provided
        if query_params.is_public is not None:
            query = query.filter(self.model.is_public == query_params.is_public)

        total = query.count()

        # Apply sorting
        if query_params.sort_by:
            sort_column = getattr(self.model, query_params.sort_by)
            if query_params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Apply pagination
        songs = query.offset((query_params.page - 1) * query_params.per_page).limit(
            query_params.per_page
        ).all()

        return songs, total

    def update_song(
        self, db: Session, song_id: UUID, song_in: SongUpdateSchema, user_id: UUID
    ) -> Song:
        """Update an existing song, ensuring ownership."""
        db_song = self.get_song(db, song_id)
        if db_song.user_id != user_id:
            raise PermissionDeniedError("You do not have permission to update this song.")
        return self.update(db, db_song, song_in.model_dump(exclude_unset=True), user_id)

    def delete_song(self, db: Session, song_id: UUID, user_id: UUID):
        """Delete a song, ensuring ownership."""
        db_song = self.get_song(db, song_id)
        if db_song.user_id != user_id:
            raise PermissionDeniedError("You do not have permission to delete this song.")
        return self.delete(db, db_song, user_id)

    def increment_view_count(self, db: Session, song_id: UUID) -> Song:
        """Increment the view count for a song."""
        song = self.get_song(db, song_id)
        song.views += 1
        db.commit()
        db.refresh(song)
        return song

    def update_rating(self, db: Session, song_id: UUID, new_rating: float) -> Song:
        """Update the rating for a song."""
        song = self.get_song(db, song_id)
        song.rating = new_rating
        db.commit()
        db.refresh(song)
        return song

    def get_popular_songs(self, db: Session, limit: int = 10) -> List[Song]:
        """Get the most popular songs based on views."""
        return (
            db.query(self.model)
            .filter(self.model.is_public == True)
            .order_by(self.model.views.desc())
            .limit(limit)
            .all()
        )

    def get_top_rated_songs(self, db: Session, limit: int = 10) -> List[Song]:
        """Get the highest rated songs."""
        return (
            db.query(self.model)
            .filter(self.model.is_public == True)
            .filter(self.model.rating > 0)
            .order_by(self.model.rating.desc())
            .limit(limit)
            .all()
        )

    def get_recent_songs(self, db: Session, limit: int = 10) -> List[Song]:
        """Get songs ordered by creation date."""
        return (
            db.query(self.model)
            .filter(self.model.is_public == True)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_artist_songs(self, db: Session, artist: str, limit: int = 20) -> Tuple[List[Song], int]:
        """Get songs by a specific artist."""
        query = db.query(self.model).filter(
            and_(
                self.model.artist.ilike(f"%{artist}%"),
                self.model.is_public == True
            )
        )
        
        total = query.count()
        songs = query.limit(limit).all()
        
        return songs, total

    def get_genre_songs(self, db: Session, genre: str, limit: int = 20) -> Tuple[List[Song], int]:
        """Get songs in a specific genre."""
        query = db.query(self.model).filter(
            and_(
                self.model.genre.ilike(f"%{genre}%"),
                self.model.is_public == True
            )
        )
        
        total = query.count()
        songs = query.limit(limit).all()
        
        return songs, total

    def search_songs_advanced(
        self, 
        db: Session, 
        search_term: str,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        difficulty_min: Optional[int] = None,
        difficulty_max: Optional[int] = None,
        rating_min: Optional[float] = None,
        rating_max: Optional[float] = None,
        limit: int = 20
    ) -> Tuple[List[Song], int]:
        """Advanced search with multiple criteria."""
        query = db.query(self.model).filter(self.model.is_public == True)

        # Apply search term
        if search_term:
            search_filter = or_(
                self.model.title.ilike(f"%{search_term}%"),
                self.model.artist.ilike(f"%{search_term}%"),
                self.model.album.ilike(f"%{search_term}%"),
                self.model.lyrics.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Apply specific filters
        if artist:
            query = query.filter(self.model.artist.ilike(f"%{artist}%"))
        
        if album:
            query = query.filter(self.model.album.ilike(f"%{album}%"))
        
        if genre:
            query = query.filter(self.model.genre.ilike(f"%{genre}%"))
        
        if year_from:
            query = query.filter(self.model.year >= year_from)
        
        if year_to:
            query = query.filter(self.model.year <= year_to)
        
        if difficulty_min:
            query = query.filter(self.model.difficulty >= difficulty_min)
        
        if difficulty_max:
            query = query.filter(self.model.difficulty <= difficulty_max)
        
        if rating_min:
            query = query.filter(self.model.rating >= rating_min)
        
        if rating_max:
            query = query.filter(self.model.rating <= rating_max)

        total = query.count()
        songs = query.limit(limit).all()
        
        return songs, total

    def bulk_update_songs(self, db: Session, song_updates: List[dict], user_id: UUID) -> List[Song]:
        """Update multiple songs in a single transaction."""
        updated_songs = []
        
        for update_data in song_updates:
            song_id = update_data.get('id')
            if not song_id:
                continue
            
            try:
                # Verify ownership
                song = self.get_song(db, UUID(song_id))
                if song.user_id != user_id:
                    continue  # Skip songs not owned by user
                
                # Update the song
                update_fields = {k: v for k, v in update_data.items() if k != 'id' and v is not None}
                if update_fields:
                    updated_song = self.update(db, song, update_fields, user_id)
                    updated_songs.append(updated_song)
                    
            except Exception:
                continue  # Skip songs that can't be processed
        
        return updated_songs

    def bulk_delete_songs(self, db: Session, song_ids: List[UUID], user_id: UUID) -> int:
        """Delete multiple songs in a single transaction."""
        deleted_count = 0
        
        for song_id in song_ids:
            try:
                # Verify ownership
                song = self.get_song(db, song_id)
                if song.user_id != user_id:
                    continue  # Skip songs not owned by user
                
                # Delete the song
                self.delete(db, song, user_id)
                deleted_count += 1
                
            except Exception:
                continue  # Skip songs that can't be processed
        
        return deleted_count
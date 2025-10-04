from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, root_validator, validator

# Max content size for lyrics, chords, tab (50KB)
MAX_CONTENT_SIZE_KB = 50
MAX_CONTENT_SIZE_BYTES = MAX_CONTENT_SIZE_KB * 1024


class SongBaseSchema(BaseModel):
    """Base schema for song data."""

    title: str = Field(
        ..., min_length=1, max_length=255, example="Stairway to Heaven"
    )
    artist: str = Field(
        ..., min_length=1, max_length=255, example="Led Zeppelin"
    )
    album: Optional[str] = Field(
        None, max_length=255, example="Led Zeppelin IV"
    )
    lyrics: Optional[str] = Field(
        None,
        max_length=MAX_CONTENT_SIZE_BYTES,
        description="Full lyrics of the song (max 50KB)",
    )
    chords: Optional[str] = Field(
        None,
        max_length=MAX_CONTENT_SIZE_BYTES,
        description="Chords for the song (max 50KB)",
    )
    tab: Optional[str] = Field(
        None,
        max_length=MAX_CONTENT_SIZE_BYTES,
        description="Tablature for the song (max 50KB)",
    )
    genre: Optional[str] = Field(
        None, max_length=100, example="Classic Rock"
    )
    year: Optional[int] = Field(
        None, ge=1900, le=datetime.now().year, example=1971
    )
    source_url: Optional[HttpUrl] = Field(
        None, example="https://www.ultimate-guitar.com/tabs/l/led_zeppelin/stairway_to_heaven_tab.htm"
    )
    difficulty: int = Field(
        1, ge=1, le=5, example=3, description="Difficulty on a scale of 1 to 5"
    )

    @validator("lyrics", "chords", "tab", pre=True, always=True)
    def check_content_size(cls, v):
        if v is not None and len(v.encode("utf-8")) > MAX_CONTENT_SIZE_BYTES:
            raise ValueError(
                f"Content exceeds {MAX_CONTENT_SIZE_KB}KB limit. "
                f"Current size: {len(v.encode('utf-8')) / 1024:.2f}KB"
            )
        return v

    class Config:
        from_attributes = True  # Changed from orm_mode = True for Pydantic v2
        json_schema_extra = {
            "examples": [
                {
                    "title": "Stairway to Heaven",
                    "artist": "Led Zeppelin",
                    "album": "Led Zeppelin IV",
                    "lyrics": "...",
                    "chords": "...",
                    "tab": "...",
                    "genre": "Classic Rock",
                    "year": 1971,
                    "source_url": "https://www.example.com/stairway",
                    "difficulty": 3,
                }
            ]
        }


class SongCreateSchema(SongBaseSchema):
    """Schema for creating a new song."""
    # All fields from SongBaseSchema are required for creation unless explicitly made optional here
    pass


class SongUpdateSchema(SongBaseSchema):
    """Schema for updating an existing song."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist: Optional[str] = Field(None, min_length=1, max_length=255)
    # Other fields are already Optional in SongBaseSchema or explicitly made optional here

    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the schema


class SongResponseSchema(SongBaseSchema):
    """Schema for returning song data in API responses."""

    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174001")
    views: int = Field(0, ge=0, example=150)
    rating: float = Field(0.0, ge=0.0, le=5.0, example=4.5)
    created_at: datetime = Field(..., example="2023-01-01T12:00:00Z")
    updated_at: datetime = Field(..., example="2023-01-01T12:30:00Z")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "123e4567-e89b-12d3-a456-426614174001",
                    "title": "Stairway to Heaven",
                    "artist": "Led Zeppelin",
                    "album": "Led Zeppelin IV",
                    "lyrics": "...",
                    "chords": "...",
                    "tab": "...",
                    "genre": "Classic Rock",
                    "year": 1971,
                    "source_url": "https://www.example.com/stairway",
                    "views": 150,
                    "rating": 4.5,
                    "difficulty": 3,
                    "created_at": "2023-01-01T12:00:00Z",
                    "updated_at": "2023-01-01T12:30:00Z",
                }
            ]
        }


class SongListResponseSchema(BaseModel):
    """Schema for paginated list of songs."""

    items: List[SongResponseSchema]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)

    class Config:
        from_attributes = True


class SongQueryParams(BaseModel):
    """Schema for query parameters for listing songs."""

    page: int = Field(1, ge=1, description="Page number for pagination")
    per_page: int = Field(25, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(
        "created_at",
        pattern="^(title|artist|created_at|views|rating|difficulty|year)$",
        description="Field to sort by",
    )
    sort_order: Optional[str] = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"
    )
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search term for title, artist, or album",
    )
    genre: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Filter by genre"
    )
    difficulty_min: Optional[int] = Field(
        None, ge=1, le=5, description="Minimum difficulty level"
    )
    difficulty_max: Optional[int] = Field(
        None, ge=1, le=5, description="Maximum difficulty level"
    )
    year_from: Optional[int] = Field(
        None, ge=1900, le=datetime.now().year, description="Filter by year from"
    )
    year_to: Optional[int] = Field(
        None, ge=1900, le=datetime.now().year, description="Filter by year to"
    )
    rating_min: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="Minimum rating"
    )
    rating_max: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="Maximum rating"
    )
    user_id: Optional[UUID] = Field(
        None, description="Filter by user ID (owner of the song)"
    )
    is_public: Optional[bool] = Field(
        None, description="Filter by public/private status"
    )

    @root_validator(pre=True)
    def validate_difficulty_range(cls, values):
        min_val = values.get("difficulty_min")
        max_val = values.get("difficulty_max")
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValueError("difficulty_min cannot be greater than difficulty_max")
        return values

    @root_validator(pre=True)
    def validate_year_range(cls, values):
        min_val = values.get("year_from")
        max_val = values.get("year_to")
        if min_val is not None and max_val is not None:
            if min_val > max_val:
                raise ValueError("year_from cannot be greater than year_to")
        return values

    @root_validator(pre=True)
    def validate_rating_range(cls, values):
        min_val = values.get("rating_min")
        max_val = values.get("rating_max")
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValueError("rating_min cannot be greater than rating_max")
        return values


class AdvancedSearchParams(BaseModel):
    """Schema for advanced search parameters."""
    
    query: Optional[str] = Field(None, description="Main search query")
    artist: Optional[str] = Field(None, description="Specific artist name")
    album: Optional[str] = Field(None, description="Specific album name")
    genre: Optional[List[str]] = Field(None, description="List of genres to filter by")
    year_from: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    year_to: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    difficulty_range: Optional[List[int]] = Field(None, description="Difficulty levels [1,2,3,4,5]")
    rating_min: Optional[float] = Field(None, ge=0.0, le=5.0)
    rating_max: Optional[float] = Field(None, ge=0.0, le=5.0)
    has_lyrics: Optional[bool] = Field(None, description="Filter songs with lyrics")
    has_chords: Optional[bool] = Field(None, description="Filter songs with chords")
    has_tab: Optional[bool] = Field(None, description="Filter songs with tablature")
    has_rating: Optional[bool] = Field(None, description="Filter songs with ratings")
    is_public: Optional[bool] = Field(True, description="Filter by public status")
    
    # Pagination
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field("created_at", pattern="^(title|artist|created_at|views|rating|difficulty|year)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class BulkUpdateSchema(BaseModel):
    """Schema for bulk song updates."""
    
    songs: List[dict] = Field(..., description="List of song update objects")
    
    class Config:
        json_schema_extra = {
            "example": {
                "songs": [
                    {"id": "song-uuid-1", "genre": "Rock", "difficulty": 3},
                    {"id": "song-uuid-2", "rating": 4.5, "views": 100},
                ]
            }
        }


class FilterOptionsSchema(BaseModel):
    """Schema for available filter options."""
    
    genres: List[str] = Field(..., description="Available genres")
    artists: List[str] = Field(..., description="Popular artists")
    albums: List[str] = Field(..., description="Popular albums")
    years: List[int] = Field(..., description="Available years")
    difficulties: List[int] = Field(..., description="Available difficulty levels")
    
    class Config:
        json_schema_extra = {
            "example": {
                "genres": ["Rock", "Pop", "Classical", "Jazz"],
                "artists": ["Led Zeppelin", "The Beatles", "Pink Floyd"],
                "albums": ["Led Zeppelin IV", "Abbey Road", "Dark Side of the Moon"],
                "years": [1970, 1971, 1972, 1973],
                "difficulties": [1, 2, 3, 4, 5],
            }
        }
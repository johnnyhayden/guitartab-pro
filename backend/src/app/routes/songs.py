"""Song CRUD API routes for GuitarTab Pro API."""

from uuid import UUID

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from ..database import get_db
from ..schemas.song import (
    SongCreateSchema,
    SongQueryParams,
    SongUpdateSchema,
    SongResponseSchema,
    SongListResponseSchema,
)
from ..services.song_service import SongService
from ..utils.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..utils.responses import SchemaResponse, ErrorResponse
from ..utils.validation import FieldValidator, RequestValidator

# Create namespace
songs_ns = Namespace("songs", description="Song operations")

# Initialize SongService
song_service = SongService()


@songs_ns.route("/")
class SongList(Resource):
    @songs_ns.doc("list_songs")
    @jwt_required()
    def get(self):
        """List songs with optional filtering, sorting, and pagination."""
        try:
            # Validate and parse query parameters
            query_params = SongQueryParams(**request.args)
            
            # Additional validation for pagination
            page, per_page = FieldValidator.validate_pagination_params(
                query_params.page, query_params.per_page
            )
            query_params.page = page
            query_params.per_page = per_page
            
            # Validate sort parameters
            sort_by, sort_order = FieldValidator.validate_sort_parameters(
                query_params.sort_by or "created_at",
                query_params.sort_order,
                allowed_fields=["title", "artist", "created_at", "views", "rating", "difficulty", "year"]
            )
            query_params.sort_by = sort_by
            query_params.sort_order = sort_order

            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Get songs through service
            songs, total = song_service.list_songs(
                db=db, query_params=query_params, current_user_id=current_user_id
            )

            return SchemaResponse.songs_list_response(songs, total, page, per_page)

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to retrieve songs: {str(e)}")

    @songs_ns.doc("create_song")
    @jwt_required()
    def post(self):
        """Create a new song."""
        try:
            # Validate request body
            RequestValidator.validate_request_body(
                request.json,
                required_fields=["title", "artist"],
                optional_fields=[
                    "album", "genre", "year", "lyrics", "chords", "tab", 
                    "source_url", "difficulty"
                ]
            )

            # Validate and parse input data
            song_data = SongCreateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Create song through service
            new_song = song_service.create_song(db, song_data, current_user_id)

            return SchemaResponse.song_created(new_song)

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to create song: {str(e)}")


@songs_ns.route("/<uuid:song_id>")
@songs_ns.param("song_id", "The song identifier")
class SongResource(Resource):
    @songs_ns.doc("get_song")
    def get(self, song_id: UUID):
        """Get a song by ID."""
        try:
            db = get_db()

            # Get song through service
            song = song_service.get_song(db, song_id)

            # Increment view count
            song_service.increment_view_count(db, song_id)

            return SchemaResponse.song_response(song)

        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to retrieve song: {str(e)}")

    @songs_ns.doc("update_song")
    @jwt_required()
    def put(self, song_id: UUID):
        """Update a song, ensuring ownership."""
        try:
            # Validate and parse input data
            song_data = SongUpdateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Update song through service
            updated_song = song_service.update_song(db, song_id, song_data, current_user_id)

            return SchemaResponse.song_updated(updated_song)

        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to update song: {str(e)}")

    @songs_ns.doc("delete_song")
    @jwt_required()
    def delete(self, song_id: UUID):
        """Delete a song, ensuring ownership."""
        try:
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Delete song through service
            song_service.delete_song(db, song_id, current_user_id)

            return SchemaResponse.song_deleted()

        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to delete song: {str(e)}")


@songs_ns.route("/<uuid:song_id>/rate")
@songs_ns.param("song_id", "The song identifier")
class SongRating(Resource):
    @songs_ns.doc("rate_song")
    @jwt_required()
    def post(self, song_id: UUID):
        """Rate a song."""
        try:
            # Validate request body
            RequestValidator.validate_request_body(
                request.json,
                required_fields=["rating"],
                optional_fields=[]
            )

            # Get and validate rating from request
            rating_data = request.get_json()
            rating = float(rating_data["rating"])
            
            if rating < 0.0 or rating > 5.0:
                raise ValidationError("Rating must be between 0.0 and 5.0")

            db = get_db()

            # Update rating through service
            song_service.update_rating(db, song_id, rating)

            return SchemaResponse.success("Song rated successfully")

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except ValueError as e:
            return ErrorResponse.validation_error({"rating": f"Invalid rating value: {str(e)}"})
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to update song rating: {str(e)}")
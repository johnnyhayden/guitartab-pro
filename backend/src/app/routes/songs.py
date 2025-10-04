"""Song CRUD API routes for GuitarTab Pro API."""

from uuid import UUID

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from ..database import get_db
from ..schemas.song import (
    SongCreateSchema,
    SongListResponseSchema,
    SongQueryParams,
    SongResponseSchema,
    SongUpdateSchema,
)
from ..services.song_service import SongService
from ..utils.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

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
            # Parse query parameters
            query_params = SongQueryParams(**request.args)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Get songs through service
            songs, total = song_service.list_songs(
                db=db, query_params=query_params, current_user_id=current_user_id
            )

            # Calculate pagination
            total_pages = (total + query_params.per_page - 1) // query_params.per_page

            return (
                SongListResponseSchema(
                    items=[SongResponseSchema.model_validate(song) for song in songs],
                    total=total,
                    page=query_params.page,
                    per_page=query_params.per_page,
                    pages=total_pages,
                ).model_dump(),
                200,
            )

        except Exception as e:
            return {"message": "Failed to retrieve songs", "error": str(e)}, 500

    @songs_ns.doc("create_song")
    @jwt_required()
    def post(self):
        """Create a new song."""
        try:
            # Validate input data
            song_data = SongCreateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Create song through service
            new_song = song_service.create_song(db, song_data, current_user_id)

            return (
                SongResponseSchema.model_validate(new_song).model_dump(),
                201,
                {"location": f"/api/songs/{new_song.id}"},
            )

        except ValidationError as e:
            return {"message": "Validation failed", "errors": e.detail}, 422
        except ConflictError as e:
            return {"message": str(e)}, 409
        except Exception as e:
            return {"message": "Failed to create song", "error": str(e)}, 500


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
            song = song_service.increment_view_count(db, song_id)

            return SongResponseSchema.model_validate(song).model_dump(), 200

        except NotFoundError as e:
            return {"message": str(e)}, 404
        except Exception as e:
            return {"message": "Failed to retrieve song", "error": str(e)}, 500

    @songs_ns.doc("update_song")
    @jwt_required()
    def put(self, song_id: UUID):
        """Update a song, ensuring ownership."""
        try:
            # Validate input data
            song_data = SongUpdateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Update song through service
            updated_song = song_service.update_song(db, song_id, song_data, current_user_id)

            return SongResponseSchema.model_validate(updated_song).model_dump(), 200

        except NotFoundError as e:
            return {"message": str(e)}, 404
        except PermissionDeniedError as e:
            return {"message": str(e)}, 403
        except ValidationError as e:
            return {"message": "Validation failed", "errors": e.detail}, 422
        except Exception as e:
            return {"message": "Failed to update song", "error": str(e)}, 500

    @songs_ns.doc("delete_song")
    @jwt_required()
    def delete(self, song_id: UUID):
        """Delete a song, ensuring ownership."""
        try:
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Delete song through service
            song_service.delete_song(db, song_id, current_user_id)

            return "", 204

        except NotFoundError as e:
            return {"message": str(e)}, 404
        except PermissionDeniedError as e:
            return {"message": str(e)}, 403
        except Exception as e:
            return {"message": "Failed to delete song", "error": str(e)}, 500


@songs_ns.route("/<uuid:song_id>/rate")
@songs_ns.param("song_id", "The song identifier")
class SongRating(Resource):
    @songs_ns.doc("rate_song")
    @jwt_required()
    def post(self, song_id: UUID):
        """Rate a song."""
        try:
            # Get rating from request
            rating_data = request.get_json()
            if not rating_data or "rating" not in rating_data:
                return {"message": "Rating value is required"}, 422

            rating = float(rating_data["rating"])
            if rating < 0.0 or rating > 5.0:
                return {"message": "Rating must be between 0.0 and 5.0"}, 422

            db = get_db()

            # Update rating through service
            song_service.update_rating(db, song_id, rating)

            return {"message": "Song rated successfully"}, 200

        except ValueError as e:
            return {"message": f"Invalid rating value: {str(e)}"}, 422
        except NotFoundError as e:
            return {"message": str(e)}, 404
        except Exception as e:
            return {"message": "Failed to update song rating", "error": str(e)}, 500

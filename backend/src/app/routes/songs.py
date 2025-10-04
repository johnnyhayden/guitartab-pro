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
    AdvancedSearchParams,
    BulkUpdateSchema,
    FilterOptionsSchema,
)
from ..services.song_service import SongService
from ..utils.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..utils.responses import SchemaResponse, APIResponse, ErrorResponse
from ..utils.validation import FieldValidator, RequestValidator
from ..utils.pagination import AdvancedPagination, PaginationBuilder

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

            # Get songs through enhanced service
            songs, total = song_service.list_songs(
                db=db, query_params=query_params, current_user_id=current_user_id
            )

            # Create pagination info using advanced pagination
            pagination_info = AdvancedPagination.offset_based_paginate(
                db.query(song_service.model), 
                page=page, 
                per_page=per_page
            )[1]

            return SchemaResponse.songs_list_response(songs, pagination_info.total, page, per_page)

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


@songs_ns.route("/advanced-search")
class AdvancedSearch(Resource):
    @songs_ns.doc("advanced_search")
    @jwt_required()
    def post(self):
        """Advanced search with multiple criteria."""
        try:
            # Validate advanced search parameters
            search_params = AdvancedSearchParams(**request.json)
            
            db = get_db()

            # Perform advanced search
            songs, total = song_service.search_songs_advanced(
                db=db,
                search_term=search_params.query or "",
                artist=search_params.artist,
                album=search_params.album,
                genre=",".join(search_params.genre) if search_params.genre else None,
                year_from=search_params.year_from,
                year_to=search_params.year_to,
                difficulty_min=min(search_params.difficulty_range) if search_params.difficulty_range else None,
                difficulty_max=max(search_params.difficulty_range) if search_params.difficulty_range else None,
                rating_min=search_params.rating_min,
                rating_max=search_params.rating_max,
                limit=search_params.per_page
            )

            return SchemaResponse.songs_list_response(
                songs, total, search_params.page, search_params.per_page
            )

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Advanced search failed: {str(e)}")


@songs_ns.route("/popular")
class PopularSongs(Resource):
    @songs_ns.doc("popular_songs")
    def get(self):
        """Get popular songs based on views."""
        try:
            limit = int(request.args.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            db = get_db()
            songs = song_service.get_popular_songs(db, limit)
            
            return APIResponse.success(
                f"Retrieved {len(songs)} popular songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get popular songs: {str(e)}")


@songs_ns.route("/top-rated")
class TopRatedSongs(Resource):
    @songs_ns.doc("top_rated_songs")
    def get(self):
        """Get top-rated songs."""
        try:
            limit = int(request.args.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            db = get_db()
            songs = song_service.get_top_rated_songs(db, limit)
            
            return APIResponse.success(
                f"Retrieved {len(songs)} top-rated songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get top-rated songs: {str(e)}")


@songs_ns.route("/recent")
class RecentSongs(Resource):
    @songs_ns.doc("recent_songs")
    def get(self):
        """Get recent songs."""
        try:
            limit = int(request.args.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            db = get_db()
            songs = song_service.get_recent_songs(db, limit)
            
            return APIResponse.success(
                f"Retrieved {len(songs)} recent songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get recent songs: {str(e)}")


@songs_ns.route("/filter-options")
class FilterOptions(Resource):
    @songs_ns.doc("get_filter_options")
    def get(self):
        """Get available filter options."""
        try:
            db = get_db()
            
            # Get distinct values for filter options
            genres = db.query(song_service.model.genre).filter(
                song_service.model.genre.isnot(None),
                song_service.model.is_public == True
            ).distinct().all()
            
            artists = db.query(song_service.model.artist).filter(
                song_service.model.is_public == True
            ).distinct().limit(50).all()
            
            albums = db.query(song_service.model.album).filter(
                song_service.model.album.isnot(None),
                song_service.model.is_public == True
            ).distinct().limit(50).all()
            
            years = db.query(song_service.model.year).filter(
                song_service.model.year.isnot(None),
                song_service.model.is_public == True
            ).distinct().all()
            
            filter_options = FilterOptionsSchema(
                genres=[g[0] for g in genres if g[0]],
                artists=[a[0] for a in artists if a[0]],
                albums=[al[0] for al in albums if al[0]],
                years=sorted([y[0] for y in years if y[0]], reverse=True),
                difficulties=[1, 2, 3, 4, 5]
            )
            
            return APIResponse.success(
                "Filter options retrieved",
                data=filter_options.model_dump()
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get filter options: {str(e)}")


@songs_ns.route("/bulk-update")
class BulkUpdate(Resource):
    @songs_ns.doc("bulk_update_songs")
    @jwt_required()
    def put(self):
        """Update multiple songs in bulk."""
        try:
            # Validate bulk update data
            bulk_data = BulkUpdateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            # Perform bulk update
            updated_songs = song_service.bulk_update_songs(
                db, bulk_data.songs, current_user_id
            )
            
            return APIResponse.success(
                f"Updated {len(updated_songs)} songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in updated_songs]
            )

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Bulk update failed: {str(e)}")


@songs_ns.route("/bulk-delete")
class BulkDelete(Resource):
    @songs_ns.doc("bulk_delete_songs")
    @jwt_required()
    def delete(self):
        """Delete multiple songs in bulk."""
        try:
            # Get song IDs from request
            data = request.get_json()
            if not data or 'song_ids' not in data:
                return ErrorResponse.bad_request("song_ids array is required")
            
            song_ids = [UUID(sid) for sid in data['song_ids']]
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            # Perform bulk delete
            deleted_count = song_service.bulk_delete_songs(
                db, song_ids, current_user_id
            )
            
            return APIResponse.success(f"Deleted {deleted_count} songs")

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Bulk delete failed: {str(e)}")


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


@songs_ns.route("/artist/<string:artist_name>")
class ArtistSongs(Resource):
    @songs_ns.doc("get_artist_songs")
    def get(self, artist_name: str):
        """Get songs by a specific artist."""
        try:
            limit = int(request.args.get('limit', 20))
            limit = min(max(limit, 1), 100)  # Between 1 and 100
            
            db = get_db()
            songs, total = song_service.get_artist_songs(db, artist_name, limit)
            
            return APIResponse.success(
                f"Found {total} songs by {artist_name}",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get artist songs: {str(e)}")


@songs_ns.route("/genre/<string:genre_name>")
class GenreSongs(Resource):
    @songs_ns.doc("get_genre_songs")
    def get(self, genre_name: str):
        """Get songs in a specific genre."""
        try:
            limit = int(request.args.get('limit', 20))
            limit = min(max(limit, 1), 100)  # Between 1 and 100
            
            db = get_db()
            songs, total = song_service.get_genre_songs(db, genre_name, limit)
            
            return APIResponse.success(
                f"Found {total} songs in genre {genre_name}",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get genre songs: {str(e)}")


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

            return APIResponse.success("Song rated successfully")

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except ValueError as e:
            return ErrorResponse.validation_error({"rating": f"Invalid rating value: {str(e)}"})
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to update song rating: {str(e)}")
"""Song CRUD API routes for GuitarTab Pro API with enhanced authorization."""

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
from ..utils.responses import APIResponse, ErrorResponse
from ..utils.validation import FieldValidator, RequestValidator
from ..utils.pagination import AdvancedPagination
from ..utils.auth_decorators import (
    require_auth,
    require_owner,
    require_admin,
    require_role,
    SongProtector,
    AuthorizationManager,
)


# Create namespace
songs_ns = Namespace("songs", description="Song operations")

# Initialize SongService
song_service = SongService()


@songs_ns.route("/")
class SongList(Resource):
    @songs_ns.doc("list_songs")
    @require_auth
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

            # Get current user for authorization context
            current_user = AuthorizationManager.get_current_user(db, current_user_id)

            # Get songs through enhanced service
            songs, total = song_service.list_songs(
                db=db, query_params=query_params, current_user_id=current_user_id
            )

            # Filter songs based on user permissions
            filtered_songs = []
            for song in songs:
                if song.can_be_viewed_by(
                    user_id=current_user_id,
                    is_admin=current_user.is_admin,
                    is_moderator=current_user.is_moderator
                ):
                    filtered_songs.append(song)

            return SchemaResponse.songs_list_response(filtered_songs, len(filtered_songs), page, per_page)

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to retrieve songs: {str(e)}")

    @songs_ns.doc("create_song")
    @require_auth
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


@songs_ns.route("/moderation")
class SongModeration(Resource):
    @songs_ns.doc("get_flagged_songs")
    @require_role(["moderator", "admin"])
    def get(self):
        """Get flagged songs for moderation."""
        try:
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            # Get flagged songs
            flagged_songs = db.query(song_service.model).filter(
                song_service.model.is_flagged == True
            ).all()
            
            return APIResponse.success(
                f"Found {len(flagged_songs)} flagged songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in flagged_songs]
            )
            
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get flagged songs: {str(e)}")
    
    @songs_ns.doc("approve_song")
    @require_role(["moderator", "admin"])
    def post(self):
        """Approve a flagged song."""
        try:
            song_id = request.json.get('song_id')
            if not song_id:
                return ErrorResponse.bad_request("song_id is required")
            
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            # Get song
            song = song_service.get_song(db, UUID(song_id))
            
            # Approve song
            song.unflag_song(current_user_id)
            song.make_public(True)
            
            db.commit()
            
            return APIResponse.success("Song approved successfully")
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to approve song: {str(e)}")
    
    @songs_ns.doc("reject_song")
    @require_role(["moderator", "admin"])
    def delete(self):
        """Reject and delete a flagged song."""
        try:
            song_id = request.json.get('song_id')
            if not song_id:
                return ErrorResponse.bad_request("song_id is required")
            
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            # Delete song
            song_service.delete_song(db, UUID(song_id), UUID(song_id))
            
            return APIResponse.success("Song rejected and deleted")
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to reject song: {str(e)}")


@songs_ns.route("/popular")
class PopularSongs(Resource):
    @songs_ns.doc("popular_songs")
    def get(self):
        """Get popular songs based on views."""
        try:
            limit = int(request.args.get('limit', 10))
            limit = min(max(limit, 1), 50)  # Between 1 and 50
            
            db = get_db()
            current_user_id = None
            
            # Get current user if authenticated
            try:
                current_user_id = UUID(get_jwt_identity())
                current_user = AuthorizationManager.get_current_user(db, current_user_id)
            except:
                current_user_id = None
                current_user = None
            
            songs = song_service.get_popular_songs(db, limit)
            
            # Filter based on user permissions
            filtered_songs = []
            for song in songs:
                if song.can_be_viewed_by(
                    user_id=current_user_id,
                    is_admin=getattr(current_user, 'is_admin', False),
                    is_moderator=getattr(current_user, 'is_moderator', False)
                ):
                    filtered_songs.append(song)
            
            return APIResponse.success(
                f"Retrieved {len(filtered_songs)} popular songs",
                data=[SongResponseSchema.model_validate(song).model_dump() for song in filtered_songs]
            )

        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get popular songs: {str(e)}")


@songs_ns.route("/advanced-search")
class AdvancedSearch(Resource):
    @songs_ns.doc("advanced_search")
    @require_auth
    def post(self):
        """Advanced search with multiple criteria."""
        try:
            # Validate advanced search parameters
            search_params = AdvancedSearchParams(**request.json)
            
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            current_user = AuthorizationManager.get_current_user(db, current_user_id)

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

            # Filter based on permissions
            filtered_songs = []
            for song in songs:
                if song.can_be_viewed_by(
                    user_id=current_user_id,
                    is_admin=current_user.is_admin,
                    is_moderator=current_user.is_moderator
                ):
                    filtered_songs.append(song)

            return SchemaResponse.songs_list_response(
                filtered_songs, len(filtered_songs), search_params.page, search_params.per_page
            )

        except ValidationError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Advanced search failed: {str(e)}")


@songs_ns.route("/bulk-update")
class BulkUpdate(Resource):
    @songs_ns.doc("bulk_update_songs")
    @require_auth
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
            
            # Check if current user can view this song
            current_user_id = None
            try:
                current_user_id = UUID(get_jwt_identity())
                current_user = AuthorizationManager.get_current_user(db, current_user_id)
            except:
                current_user = None
            
            if not song.can_be_viewed_by(
                user_id=current_user_id,
                is_admin=getattr(current_user, 'is_admin', False),
                is_moderator=getattr(current_user, 'is_moderator', False)
            ):
                return ErrorResponse.forbidden("You do not have permission to view this song")

            # Increment view count
            song_service.increment_view_count(db, song_id)

            return SchemaResponse.song_response(song)

        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to retrieve song: {str(e)}")

    @songs_ns.doc("update_song")
    @SongProtector.owner_or_admin()
    def put(self, song_id: UUID):
        """Update a song, ensuring ownership or admin privileges."""
        try:
            # Validate and parse input data
            song_data = SongUpdateSchema(**request.json)
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Get current user for authorization
            current_user = AuthorizationManager.get_current_user(db, current_user_id)

            # Check specific edit permissions
            song = song_service.get_song(db, song_id)
            if not song.can_be_edited_by(
                user_id=current_user_id,
                is_admin=current_user.is_admin,
                is_moderator=current_user.is_moderator
            ):
                return ErrorResponse.forbidden("You do not have permission to edit this song")

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
    @SongProtector.owner_or_admin()
    def delete(self, song_id: UUID):
        """Delete a song, ensuring ownership or admin privileges."""
        try:
            db = get_db()
            current_user_id = UUID(get_jwt_identity())

            # Get current user for authorization
            current_user = AuthorizationManager.get_current_user(db, current_user_id)

            # Check specific delete permissions
            song = song_service.get_song(db, song_id)
            if not song.can_be_deleted_by(
                user_id=current_user_id,
                is_admin=current_user.is_admin,
                is_moderator=current_user.is_moderator
            ):
                return ErrorResponse.forbidden("You do not have permission to delete this song")

            # Delete song through service
            song_service.delete_song(db, song_id, current_user_id)

            return SchemaResponse.song_deleted()

        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to delete song: {str(e)}")


@songs_ns.route("/<uuid:song_id>/feature")
class SongFeatureControl(Resource):
    @songs_ns.doc("feature_song")
    @require_admin
    def post(self, song_id: UUID):
        """Feature a song (admin only)."""
        try:
            db = get_db()
            
            song = song_service.get_song(db, song_id)
            song.set_featured(True)
            db.commit()
            
            return APIResponse.success("Song featured successfully")
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to feature song: {str(e)}")
    
    @songs_ns.doc("unfeature_song")
    @require_admin
    def delete(self, song_id: UUID):
        """Remove featured status (admin only)."""
        try:
            db = get_db()
            
            song = song_service.get_song(db, song_id)
            song.set_featured(False)
            db.commit()
            
            return APIResponse.success("Song unfeatured successfully")
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to unfeature song: {str(e)}")


@songs_ns.route("/<uuid:song_id>/rate")
@songs_ns.param("song_id", "The song identifier")
class SongRating(Resource):
    @songs_ns.doc("rate_song")
    @require_auth
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
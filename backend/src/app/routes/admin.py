"""Admin management routes for GuitarTab Pro API."""

from typing import List, Optional
from uuid import UUID

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from ..database import get_db
from ..models.user import User
from ..models.song import Song
from ..services.user_service import UserService
from ..services.song_service import SongService
from ..utils.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..utils.responses import APIResponse, ErrorResponse
from ..utils.auth_decorators import require_admin, AuthorizationManager


# Create namespace
admin_ns = Namespace("admin", description="Administrator operations")

# Initialize services
user_service = UserService()
song_service = SongService()


@admin_ns.route("/users")
class AdminUserManagement(Resource):
    @admin_ns.doc("list_users")
    @require_admin
    def get(self):
        """List all users (admin only)."""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            search = request.args.get('search')
            role = request.args.get('role')
            is_active = request.args.get('is_active')
            
            # Convert string boolean to boolean
            if is_active is not None:
                is_active = is_active.lower() in ['true', '1', 'yes']
            
            db = get_db()
            current_user_id = UUID(get_jwt_identity())
            
            users, total = user_service.list_users(
                db=db,
                page=page,
                per_page=min(per_page, 100),
                search=search,
                role=role,
                is_active=is_active,
                current_user_id=current_user_id
            )
            
            user_data = []
            for user in users:
                user_info = user.to_dict(include_sensitive=True)
                user_data.append({
                    "id": user_info["id"],
                    "username": user_info["username"],
                    "email": user_info["email"],
                    "full_name": user_info["full_name"],
                    "role": user_info["role"],
                    "is_active": user_info["is_active"],
                    "created_at": user_info["created_at"],
                    "last_login_at": user_info["last_login_at"],
                })
            
            return APIResponse.success(
                f"Retrieved {len(user_data)} users",
                data={
                    "users": user_data,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page
                    }
                }
            )
            
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to list users: {str(e)}")


@admin_ns.route("/users/<uuid:user_id>/role")
class AdminRoleManagement(Resource):
    @admin_ns.doc("update_user_role")
    @require_admin
    def put(self, user_id: UUID):
        """Update user role (admin only)."""
        try:
            data = request.get_json()
            if not data or 'role' not in data:
                return ErrorResponse.bad_request("role field is required")
            
            new_role = data['role']
            valid_roles = ['user', 'moderator', 'admin']
            if new_role not in valid_roles:
                return ErrorResponse.validation_error({
                    "role": f"Invalid role. Valid roles: {valid_roles}"
                })
            
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            updated_user = user_service.update_user_role(db, user_id, new_role, current_admin_id)
            
            return APIResponse.success(
                f"User role updated to {new_role}",
                data={
                    "user_id": str(user_id),
                    "username": updated_user.username,
                    "new_role": updated_user.role
                }
            )
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to update user role: {str(e)}")


@admin_ns.route("/users/<uuid:user_id>/activate")
class AdminUserActivation(Resource):
    @admin_ns.doc("activate_user")
    @require_admin
    def post(self, user_id: UUID):
        """Activate user account (admin only)."""
        try:
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            activated_user = user_service.activate_user(db, user_id, current_admin_id)
            
            return APIResponse.success(
                f"User {activated_user.username} activated",
                data={"username": activated_user.username, "is_active": activated_user.is_active}
            )
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to activate user: {str(e)}")
    
    @admin_ns.doc("deactivate_user")
    @require_admin
    def delete(self, user_id: UUID):
        """Deactivate user account (admin only)."""
        try:
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            deactivated_user = user_service.deactivate_user(db, user_id, current_admin_id)
            
            return APIResponse.success(
                f"User {deactivated_user.username} deactivated",
                data={"username": deactivated_user.username, "is_active": deactivated_user.is_active}
            )
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to deactivate user: {str(e)}")


@admin_ns.route("/users/<uuid:user_id>/stats")
class AdminUserStats(Resource):
    @admin_ns.doc("get_user_stats")
    @require_admin
    def get(self, user_id: UUID):
        """Get comprehensive user statistics (admin only)."""
        try:
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            stats = user_service.get_user_stats(db, user_id, current_admin_id)
            
            return APIResponse.success("User statistics retrieved", data=stats)
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get user stats: {str(e)}")


@admin_ns.route("/users/<uuid:user_id>/promote")
class AdminUserPromotion(Resource):
    @admin_ns.doc("promote_to_moderator")
    @require_admin
    def post(self, user_id: UUID):
        """Promote user to moderator (admin only)."""
        try:
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            promoted_user = user_service.promote_to_moderator(db, user_id, current_admin_id)
            
            return APIResponse.success(
                f"User {promoted_user.username} promoted to moderator",
                data={"username": promoted_user.username, "role": promoted_user.role}
            )
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to promote user: {str(e)}")
    
    @admin_ns.doc("demote_from_moderator")
    @require_admin
    def delete(self, user_id: UUID):
        """Demote moderator to user (admin only)."""
        try:
            db = get_db()
            current_admin_id = UUID(get_jwt_identity())
            
            demoted_user = user_service.demote_from_moderator(db, user_id, current_admin_id)
            
            return APIResponse.success(
                f"User {demoted_user.username} demoted from moderator",
                data={"username": demoted_user.username, "role": demoted_user.role}
            )
            
        except NotFoundError as e:
            return ErrorResponse.from_exception(e)
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to demote user: {str(e)}")


@admin_ns.route("/system/stats")
class AdminSystemStats(Resource):
    @admin_ns.doc("get_system_stats")
    @require_admin
    def get(self):
        """Get system-wide statistics (admin only)."""
        try:
            db = get_db()
            
            # User statistics
            total_users = db.query(func.count(User.id)).scalar()
            active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
            admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
            moderator_users = db.query(func.count(User.id)).filter(User.is_moderator == True).scalar()
            
            # Song statistics
            total_songs = db.query(func.count(Song.id)).scalar()
            public_songs = db.query(func.count(Song.id)).filter(Song.is_public == True).scalar()
            flagged_songs = db.query(func.count(Song.id)).filter(Song.is_flagged == True).scalar()
            featured_songs = db.query(func.count(Song.id)).filter(Song.is_featured == True).scalar()
            
            # Content statistics
            songs_with_lyrics = db.query(func.count(Song.id)).filter(Song.lyrics.isnot(None)).scalar()
            songs_with_chords = db.query(func.count(Song.id)).filter(Song.chords.isnot(None)).scalar()
            songs_with_tabs = db.query(func.count(Song.id)).filter(Song.tab.isnot(None)).scalar()
            
            # Engagement statistics
            total_views = db.query(func.sum(Song.views)).scalar() or 0
            avg_rating = db.query(func.avg(Song.rating)).filter(Song.rating > 0).scalar() or 0
            
            stats = {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "admins": admin_users,
                    "moderators": moderator_users,
                },
                "songs": {
                    "total": total_songs,
                    "public": public_songs,
                    "flagged": flagged_songs,
                    "featured": featured_songs,
                },
                "content": {
                    "with_lyrics": songs_with_lyrics,
                    "with_chords": songs_with_chords,
                    "with_tabs": songs_with_tabs,
                },
                "engagement": {
                    "total_views": total_views,
                    "average_rating": round(avg_rating, 2),
                }
            }
            
            return APIResponse.success("System statistics retrieved", data=stats)
            
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get system stats: {str(e)}")


@admin_ns.route("/moderation")
class AdminModeration(Resource):
    @admin_ns.doc("get_moderation_queue")
    @require_admin
    def get(self):
        """Get songs pending moderation (admin only)."""
        try:
            db = get_db()
            
            flagged_songs = db.query(Song).filter(Song.is_flagged == True).all()
            
            song_data = []
            for song in flagged_songs:
                song_data.append({
                    "id": str(song.id),
                    "title": song.title,
                    "artist": song.artist,
                    "uploader": song.uploader.username,
                    "flagged_reason": song.flagged_reason,
                    "flagged_at": song.moderated_at.isoformat() if song.moderated_at else None,
                    "created_at": song.created_at.isoformat(),
                })
            
            return APIResponse.success(
                f"Found {len(song_data)} songs pending moderation",
                data=song_data
            )
            
        except PermissionDeniedError as e:
            return ErrorResponse.from_exception(e)
        except Exception as e:
            return ErrorResponse.service_error(f"Failed to get moderation queue: {str(e)}")

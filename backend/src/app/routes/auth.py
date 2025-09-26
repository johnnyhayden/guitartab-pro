"""Authentication routes for user registration, login, and password management."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow import Schema, ValidationError, fields

from app.auth import AuthService, PasswordManager, TokenManager
from app.database import get_db
from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


class RegistrationSchema(Schema):
    """Schema for user registration validation."""

    username = fields.Str(required=True, validate=lambda x: len(x) >= 3 and len(x) <= 50)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8)
    first_name = fields.Str(allow_none=True, validate=lambda x: x is None or len(x) <= 100)
    last_name = fields.Str(allow_none=True, validate=lambda x: x is None or len(x) <= 100)


class LoginSchema(Schema):
    """Schema for user login validation."""

    username_or_email = fields.Str(required=True)
    password = fields.Str(required=True)


class ChangePasswordSchema(Schema):
    """Schema for password change validation."""

    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        schema = RegistrationSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    success, message, user = AuthService.register_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
    )

    if success:
        tokens = TokenManager.create_tokens(user)
        return jsonify({"message": message, "user": user.to_dict(), "tokens": tokens}), 201
    else:
        return jsonify({"error": message}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return tokens."""
    try:
        schema = LoginSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    success, message, user = AuthService.authenticate_user(
        username_or_email=data["username_or_email"], password=data["password"]
    )

    if success:
        tokens = TokenManager.create_tokens(user)
        return jsonify({"message": message, "user": user.to_dict(), "tokens": tokens}), 200
    else:
        return jsonify({"error": message}), 401


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    current_user_id = get_jwt_identity()

    # Get user from database
    db = next(get_db())
    try:
        user = db.query(User).filter(User.user_id == current_user_id).first()
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401

        # Create new access token
        additional_claims = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
        }

        new_access_token = create_access_token(
            identity=user.user_id, additional_claims=additional_claims
        )

        return jsonify({"access_token": new_access_token, "token_type": "Bearer"}), 200

    finally:
        db.close()


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout user and revoke token."""
    jti = TokenManager.revoke_token()

    # In production, add jti to blacklist
    # For now, just return success
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        schema = ChangePasswordSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    current_user_id = get_jwt_identity()
    success, message = AuthService.change_password(
        user_id=current_user_id,
        old_password=data["old_password"],
        new_password=data["new_password"],
    )

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current user information."""
    user = TokenManager.get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/validate-password", methods=["POST"])
def validate_password():
    """Validate password strength."""
    password = request.json.get("password", "")
    is_valid, errors = PasswordManager.validate_password_strength(password)

    return jsonify({"is_valid": is_valid, "errors": errors}), 200

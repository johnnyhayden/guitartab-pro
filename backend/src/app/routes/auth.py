"""Authentication routes for GuitarTab Pro API."""

from flask import jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields
from marshmallow import Schema, ValidationError
from marshmallow import fields as ma_fields

from ..auth import AuthService, PasswordManager, TokenManager
from ..database import get_db
from ..models.user import User

auth_ns = Namespace("auth", description="Authentication operations")


# Flask-RESTX models
registration_model = auth_ns.model(
    "Registration",
    {
        "username": fields.String(
            required=True, description="Username", min_length=3, max_length=50
        ),
        "email": fields.String(required=True, description="Email address"),
        "password": fields.String(required=True, description="Password", min_length=8),
        "first_name": fields.String(description="First name", max_length=100),
        "last_name": fields.String(description="Last name", max_length=100),
    },
)

login_model = auth_ns.model(
    "Login",
    {
        "username_or_email": fields.String(required=True, description="Username or email"),
        "password": fields.String(required=True, description="Password"),
    },
)


# Marshmallow schemas for validation
class RegistrationSchema(Schema):
    """Schema for user registration validation."""

    username = ma_fields.Str(required=True, validate=lambda x: len(x) >= 3 and len(x) <= 50)
    email = ma_fields.Email(required=True)
    password = ma_fields.Str(required=True, validate=lambda x: len(x) >= 8)
    first_name = ma_fields.Str(allow_none=True, validate=lambda x: x is None or len(x) <= 100)
    last_name = ma_fields.Str(allow_none=True, validate=lambda x: x is None or len(x) <= 100)


class LoginSchema(Schema):
    """Schema for user login validation."""

    username_or_email = ma_fields.Str(required=True)
    password = ma_fields.Str(required=True)


@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(registration_model)
    @auth_ns.doc("register_user")
    def post(self):
        """Register a new user."""
        try:
            data = RegistrationSchema().load(request.json)
        except ValidationError as err:
            return {"message": "Validation Error", "errors": err.messages}, 400

        success, message, user = AuthService.register_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
        )

        if success:
            return {"message": message, "user_id": str(user.id)}, 201
        return {"message": message}, 400


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.doc("login_user")
    def post(self):
        """Log in an existing user."""
        try:
            data = LoginSchema().load(request.json)
        except ValidationError as err:
            return {"message": "Validation Error", "errors": err.messages}, 400

        success, message, user = AuthService.authenticate_user(
            username_or_email=data["username_or_email"], password=data["password"]
        )

        if success:
            access_token, refresh_token = TokenManager.create_tokens(user.id)
            response = {"message": message, "user_id": str(user.id)}
            # Note: In a real app, you'd set cookies here
            return response, 200
        return {"message": message}, 401


@auth_ns.route("/refresh")
class Refresh(Resource):
    @jwt_required(refresh=True)
    @auth_ns.doc("refresh_token")
    def post(self):
        """Refresh access token using refresh token."""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        return {"message": "Token refreshed", "access_token": access_token}, 200


@auth_ns.route("/logout")
class Logout(Resource):
    @jwt_required()
    @auth_ns.doc("logout_user")
    def post(self):
        """Log out user by revoking tokens."""
        jti = get_jwt()["jti"]
        TokenManager.revoke_token(jti)  # Placeholder for actual revocation
        return {"message": "Successfully logged out"}, 200

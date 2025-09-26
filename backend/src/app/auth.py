"""Authentication configuration and utilities."""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


class AuthConfig:
    """Authentication configuration."""

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    JWT_COOKIE_CSRF_PROTECT = True

    # Password Configuration
    BCRYPT_ROUNDS = 12
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128

    # Rate Limiting
    LOGIN_ATTEMPTS_LIMIT = 5
    LOGIN_ATTEMPTS_WINDOW = 300  # 5 minutes

    # Email Configuration
    EMAIL_VERIFICATION_REQUIRED = True
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(hours=1)


class PasswordManager:
    """Password hashing and validation utilities."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=AuthConfig.BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """Validate password strength and return (is_valid, errors)."""
        errors = []

        if len(password) < AuthConfig.MIN_PASSWORD_LENGTH:
            errors.append(
                f"Password must be at least {AuthConfig.MIN_PASSWORD_LENGTH} characters long"
            )

        if len(password) > AuthConfig.MAX_PASSWORD_LENGTH:
            errors.append(
                f"Password must be no more than {AuthConfig.MAX_PASSWORD_LENGTH} characters long"
            )

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors


class TokenManager:
    """JWT token management utilities."""

    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for a user."""
        additional_claims = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
        }

        access_token = create_access_token(
            identity=user.user_id,
            additional_claims=additional_claims,
            expires_delta=AuthConfig.JWT_ACCESS_TOKEN_EXPIRES,
        )

        refresh_token = create_refresh_token(
            identity=user.user_id,
            additional_claims=additional_claims,
            expires_delta=AuthConfig.JWT_REFRESH_TOKEN_EXPIRES,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(AuthConfig.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
        }

    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get the current authenticated user."""
        user_id = get_jwt_identity()
        if not user_id:
            return None

        db = next(get_db())
        try:
            return db.query(User).filter(User.user_id == user_id).first()
        finally:
            db.close()

    @staticmethod
    def revoke_token():
        """Revoke the current token (add to blacklist)."""
        jti = get_jwt()["jti"]
        # In a production app, you would add this to a Redis blacklist
        # For now, we'll just return the jti for manual handling
        return jti


class AuthService:
    """Authentication service for user operations."""

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> tuple[bool, str, Optional[User]]:
        """Register a new user."""
        db = next(get_db())
        try:
            # Check if user already exists
            if db.query(User).filter(User.username == username).first():
                return False, "Username already exists", None

            if db.query(User).filter(User.email == email).first():
                return False, "Email already exists", None

            # Validate password strength
            is_valid, errors = PasswordManager.validate_password_strength(password)
            if not is_valid:
                return False, "; ".join(errors), None

            # Create new user
            user = User(
                user_id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=PasswordManager.hash_password(password),
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            return True, "User registered successfully", user

        except Exception as e:
            db.rollback()
            return False, f"Registration failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def authenticate_user(
        username_or_email: str, password: str
    ) -> tuple[bool, str, Optional[User]]:
        """Authenticate a user with username/email and password."""
        db = next(get_db())
        try:
            # Find user by username or email
            user = (
                db.query(User)
                .filter((User.username == username_or_email) | (User.email == username_or_email))
                .first()
            )

            if not user:
                return False, "Invalid credentials", None

            if not user.is_active:
                return False, "Account is deactivated", None

            if not PasswordManager.verify_password(password, user.password_hash):
                return False, "Invalid credentials", None

            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()

            return True, "Authentication successful", user

        except Exception as e:
            return False, f"Authentication failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password."""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False, "User not found"

            # Verify old password
            if not PasswordManager.verify_password(old_password, user.password_hash):
                return False, "Current password is incorrect"

            # Validate new password strength
            is_valid, errors = PasswordManager.validate_password_strength(new_password)
            if not is_valid:
                return False, "; ".join(errors)

            # Update password
            user.password_hash = PasswordManager.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()

            return True, "Password changed successfully"

        except Exception as e:
            db.rollback()
            return False, f"Password change failed: {str(e)}"
        finally:
            db.close()

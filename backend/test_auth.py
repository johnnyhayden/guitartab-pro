#!/usr/bin/env python3
"""Simple test script for authentication system."""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from app.app import create_app
from app.auth import AuthService, PasswordManager


def test_password_hashing():
    """Test password hashing and verification."""
    print("Testing password hashing...")

    password = "TestPassword123!"
    hashed = PasswordManager.hash_password(password)

    print(f"Original password: {password}")
    print(f"Hashed password: {hashed}")
    print(f"Verification: {PasswordManager.verify_password(password, hashed)}")
    print(f"Wrong password verification: {PasswordManager.verify_password('wrong', hashed)}")
    print()


def test_password_validation():
    """Test password strength validation."""
    print("Testing password validation...")

    test_passwords = [
        "weak",
        "password",
        "Password123",
        "Password123!",
        "VeryStrongPassword123!@#",
    ]

    for password in test_passwords:
        is_valid, errors = PasswordManager.validate_password_strength(password)
        print(f"Password: {password}")
        print(f"Valid: {is_valid}")
        print(f"Errors: {errors}")
        print()


def test_app_creation():
    """Test Flask app creation."""
    print("Testing Flask app creation...")

    try:
        app = create_app()
        print("✅ Flask app created successfully")
        print(f"App name: {app.name}")
        print(f"Debug mode: {app.debug}")
        print(f"Registered blueprints: {list(app.blueprints.keys())}")
        print()
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        print()


if __name__ == "__main__":
    print("🧪 Testing GuitarTab Pro Authentication System")
    print("=" * 50)

    test_password_hashing()
    test_password_validation()
    test_app_creation()

    print("✅ All tests completed!")

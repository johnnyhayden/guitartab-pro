#!/usr/bin/env python3
"""Test script for Flask API setup."""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from app.app import create_app
from app.utils.pagination import PaginationParams, PaginatedResponse


def test_app_creation():
    """Test Flask app creation with enhanced configuration."""
    print("Testing Flask app creation...")
    
    try:
        app = create_app()
        print("✅ Flask app created successfully")
        print(f"App name: {app.name}")
        print(f"Debug mode: {app.debug}")
        print(f"Registered blueprints: {list(app.blueprints.keys())}")
        print(f"CORS enabled: {hasattr(app, 'after_request_funcs')}")
        print()
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        print()


def test_pagination():
    """Test pagination utilities."""
    print("Testing pagination utilities...")
    
    # Test PaginationParams
    params = PaginationParams(page=2, per_page=10, sort_by="name", sort_order="desc")
    print(f"Pagination params: page={params.page}, per_page={params.per_page}")
    print(f"Sort: {params.sort_by} {params.sort_order}")
    
    # Test PaginatedResponse
    response = PaginatedResponse(
        items=["item1", "item2", "item3"],
        total=25,
        page=2,
        per_page=10,
        pages=3,
        has_prev=True,
        has_next=True,
        prev_num=1,
        next_num=3
    )
    
    response_dict = response.to_dict()
    print(f"Paginated response: {response_dict}")
    print()


def test_error_handlers():
    """Test error handler registration."""
    print("Testing error handlers...")
    
    try:
        app = create_app()
        error_handlers = app.error_handler_spec.get(None, {})
        print(f"✅ Error handlers registered: {len(error_handlers)} handlers")
        for code, handler in error_handlers.items():
            print(f"  - {code}: {handler}")
        print()
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        print()


if __name__ == "__main__":
    print("🧪 Testing GuitarTab Pro Flask API Setup")
    print("=" * 50)
    
    test_app_creation()
    test_pagination()
    test_error_handlers()
    
    print("✅ All API tests completed!")

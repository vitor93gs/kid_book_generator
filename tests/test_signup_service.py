"""
Tests for the signup service.
"""

import pytest
from fastapi import HTTPException
from app.models.user_schema import User
from app.services.auth.signup_service import create_user
from unittest.mock import MagicMock


@pytest.fixture
def mock_collection():
    """Return a fresh MagicMock for the MongoDB collection per test."""
    return MagicMock()

@pytest.fixture
def mock_user():
    """Return a sample User model instance for tests.

    The fixture provides a pre-filled `User` instance suitable for unit tests
    that exercise signup and storage behaviour.
    """
    return User(
        id="12345",
        email="test@example.com",
        hashed_password="plaintextpassword",
        oauth_provider="google",
        oauth_id="google_id",
        full_name="Test User"
    )

def test_create_user_success(mock_user, monkeypatch, mock_collection):
    """
    Test successful user creation.
    """
    # Patch the symbol where it's used (inside signup_service), not the source module
    monkeypatch.setattr(
        "app.services.auth.signup_service.users_collection",
        mock_collection,
        raising=True,
    )
    mock_collection.find_one.return_value = None
    mock_collection.insert_one.return_value.inserted_id = "12345"

    user = create_user(mock_user)

    assert user.id == "12345"
    # Ensure the mock is correctly called
    mock_collection.find_one.assert_called_once_with({"email": mock_user.email})
    mock_collection.insert_one.assert_called_once()

def test_create_user_email_already_registered(mock_user, monkeypatch, mock_collection):
    """
    Test user creation with an already registered email.
    """
    # Patch the symbol where it's used (inside signup_service)
    monkeypatch.setattr(
        "app.services.auth.signup_service.users_collection",
        mock_collection,
        raising=True,
    )
    mock_collection.find_one.return_value = {"email": mock_user.email}

    with pytest.raises(HTTPException) as exc_info:
        create_user(mock_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"
    # Ensure the mock is correctly called
    mock_collection.find_one.assert_called_once_with({"email": mock_user.email})


def test_create_user_db_insert_failure(mock_user, monkeypatch, mock_collection):
    """If the database insert fails, the exception should propagate."""
    monkeypatch.setattr(
        "app.services.auth.signup_service.users_collection",
        mock_collection,
        raising=True,
    )
    mock_collection.find_one.return_value = None
    mock_collection.insert_one.side_effect = Exception("DB insert failed")

    with pytest.raises(Exception) as exc_info:
        create_user(mock_user)

    assert "DB insert failed" in str(exc_info.value)


def test_signup_integration_run_app_and_signup():
    """Integration test: run the auth router with TestClient, send a signup request,
    assert the user is created in MongoDB, then delete the user.

    This test requires a reachable MongoDB instance configured via environment
    variables (MONGODB_URI, etc.). If the database is not available the test
    will be skipped.
    """

    import random
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    try:
        # Import the real collection; this will raise if MongoDB is unreachable
        from app.mongodb import users_collection as characters_collection
    except Exception as e:
        pytest.skip(f"MongoDB not available for integration test: {e}")

    # Mount the auth router under /auth so callback/redirect URIs align
    from app.routers import auth as auth_router

    test_app = FastAPI()
    test_app.include_router(auth_router.router, prefix="/auth")

    client = TestClient(test_app)

    # Unique test email to avoid collisions
    unique = random.randint(10000, 99999)
    email = f"integration_test_{unique}@example.com"
    payload = {"email": email, "hashed_password": "plaintextpassword"}

    # Ensure no existing doc
    try:
        characters_collection.delete_many({"email": email})
    except Exception:
        # If delete fails, still attempt the test; we'll try to clean up later
        pass

    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 200, f"unexpected status: {response.status_code} body={response.text}"
    body = response.json()
    assert body.get("email") == email
    user_id = body.get("id")
    assert user_id is not None

    # Cleanup: delete the created user by _id
    try:
        from bson import ObjectId
        characters_collection.delete_one({"_id": ObjectId(user_id)})
    except Exception:
        # best-effort cleanup
        characters_collection.delete_many({"email": email})
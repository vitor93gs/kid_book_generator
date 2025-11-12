"""
Tests for the OAuth service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from app.services.auth.oauth_service import google_authorize_redirect, google_authorize_callback

# Mock the OAuth client
mock_oauth = MagicMock()
mock_oauth.google.authorize_redirect = AsyncMock()
mock_oauth.google.parse_id_token = AsyncMock()


@pytest.fixture
def mock_collection():
    """Return a fresh MagicMock for the MongoDB collection per test.

    This fixture avoids shared call history across tests by providing a fresh
    MagicMock instance for each test that needs to assert database interactions.
    """
    return MagicMock()

@pytest.mark.asyncio
async def test_google_authorize_redirect(monkeypatch):
    """
    Test the Google OAuth authorization redirect.
    """
    redirect_uri = "http://localhost:8000/auth/oauth/google/callback"
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}

    # Patch the oauth client where it's used (inside oauth_service)
    monkeypatch.setattr(
        "app.services.auth.oauth_service.oauth",
        mock_oauth,
        raising=True,
    )
    mock_oauth.google.authorize_redirect.return_value = "redirect_response"
    mock_oauth.google.load_server_metadata = AsyncMock(return_value={"jwks_uri": "mock_uri"})
    mock_oauth.google.fetch_jwk_set = AsyncMock(return_value={"keys": []})

    response = await google_authorize_redirect(mock_request, redirect_uri)
    # Ensure the mock is correctly called
    mock_oauth.google.authorize_redirect.assert_called_once_with(mock_request, redirect_uri)
    assert response == "redirect_response"

@pytest.mark.asyncio
async def test_google_authorize_callback_new_user(monkeypatch, mock_collection):
    """
    Test the Google OAuth callback for a new user.
    """
    token = {"access_token": "test_token"}
    user_info = {
        "email": "newuser@example.com",
        "sub": "google_id",
        "name": "New User",
        "picture": "http://example.com/avatar.png"
    }

    # Patch oauth and the collection where they're referenced (inside oauth_service)
    monkeypatch.setattr(
        "app.services.auth.oauth_service.oauth",
        mock_oauth,
        raising=True,
    )
    monkeypatch.setattr(
        "app.services.auth.oauth_service.users_collection",
        mock_collection,
        raising=True,
    )
    mock_oauth.google.parse_id_token.return_value = user_info
    mock_oauth.google.load_server_metadata = AsyncMock(return_value={"jwks_uri": "mock_uri"})
    mock_oauth.google.fetch_jwk_set = AsyncMock(return_value={"keys": []})
    mock_collection.find_one.return_value = None
    mock_collection.insert_one.return_value.inserted_id = "12345"

    user = await google_authorize_callback(token)

    assert user["id"] == "12345"
    assert user["email"] == user_info["email"]
    mock_collection.find_one.assert_called_once_with({"email": user_info["email"]})
    mock_collection.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_google_authorize_callback_existing_user(monkeypatch, mock_collection):
    """
    Test the Google OAuth callback for an existing user.
    """
    token = {"access_token": "test_token"}
    user_info = {
        "email": "existinguser@example.com",
        "sub": "google_id",
        "name": "Existing User",
        "picture": "http://example.com/avatar.png"
    }

    existing_user = {
        "email": user_info["email"],
        "oauth_provider": "google",
        "oauth_id": user_info["sub"],
        "full_name": user_info["name"],
        "avatar_url": user_info["picture"]
    }

    monkeypatch.setattr(
        "app.services.auth.oauth_service.oauth",
        mock_oauth,
        raising=True,
    )
    monkeypatch.setattr(
        "app.services.auth.oauth_service.users_collection",
        mock_collection,
        raising=True,
    )
    mock_oauth.google.parse_id_token.return_value = user_info
    mock_oauth.google.load_server_metadata = AsyncMock(return_value={"jwks_uri": "mock_uri"})
    mock_oauth.google.fetch_jwk_set = AsyncMock(return_value={"keys": []})
    mock_collection.find_one.return_value = existing_user

    user = await google_authorize_callback(token)

    assert user == existing_user
    mock_collection.find_one.assert_called_once_with({"email": user_info["email"]})
    mock_collection.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_google_authorize_redirect_error(monkeypatch):
    """If the underlying oauth authorize_redirect raises, it should propagate."""
    redirect_uri = "http://localhost:8000/auth/oauth/google/callback"
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}

    monkeypatch.setattr(
        "app.services.auth.oauth_service.oauth",
        mock_oauth,
        raising=True,
    )
    mock_oauth.google.authorize_redirect.side_effect = Exception("Auth error")

    with pytest.raises(Exception) as exc_info:
        await google_authorize_redirect(mock_request, redirect_uri)

    assert "Auth error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_google_authorize_callback_parse_error(monkeypatch):
    """If parsing the id token fails, the exception should propagate."""
    token = {"access_token": "bad_token"}

    monkeypatch.setattr(
        "app.services.auth.oauth_service.oauth",
        mock_oauth,
        raising=True,
    )
    # Make parse_id_token raise
    mock_oauth.google.parse_id_token.side_effect = Exception("Invalid token")
    mock_oauth.google.load_server_metadata = AsyncMock(return_value={"jwks_uri": "mock_uri"})
    mock_oauth.google.fetch_jwk_set = AsyncMock(return_value={"keys": []})

    with pytest.raises(Exception) as exc_info:
        await google_authorize_callback(token)

    assert "Invalid token" in str(exc_info.value)
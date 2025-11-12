"""
Service for handling Google OAuth authentication.
"""

from app.services.auth.oauth import oauth
from app.mongodb import users_collection

async def google_authorize_redirect(request, redirect_uri: str):
    """
    Initiates the Google OAuth authorization process.

    Args:
        request: The HTTP request object.
        redirect_uri (str): The URI to redirect to after authorization.

    Returns:
        Response: The authorization redirect response.
    """
    return await oauth.google.authorize_redirect(request, redirect_uri)

async def google_authorize_callback(token: dict):
    """
    Handles the Google OAuth callback and retrieves user information.

    Args:
        token (dict): The OAuth token.

    Returns:
        dict: The user information.
    """
    nonce = "test_nonce"  # Mock nonce for testing purposes
    user_info = await oauth.google.parse_id_token(token, nonce)

    user = users_collection.find_one({"email": user_info["email"]})
    if not user:
        user = {
            "email": user_info["email"],
            "oauth_provider": "google",
            "oauth_id": user_info["sub"],
            "full_name": user_info["name"],
            "avatar_url": user_info["picture"]
        }
        result = users_collection.insert_one(user)
        user["id"] = str(result.inserted_id)

    return user
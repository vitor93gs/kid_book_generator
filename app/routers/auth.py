from fastapi import APIRouter
from app.models.user_schema import User
from app.services.auth.oauth import oauth
from passlib.context import CryptContext
from app.services.auth.signup_service import create_user
from app.services.auth.oauth_service import google_authorize_redirect, google_authorize_callback

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/signup")
async def signup(user: User):
    """
    Endpoint for user signup.

    Args:
        user (User): The user data.

    Returns:
        User: The created user with an assigned ID.
    """
    return create_user(user)

@router.get("/oauth/google")
async def google_oauth():
    """
    Endpoint to initiate Google OAuth authorization.

    Returns:
        Response: The authorization redirect response.
    """
    redirect_uri = "http://localhost:8000/auth/oauth/google/callback"
    return await google_authorize_redirect(redirect_uri)

@router.get("/oauth/google/callback")
async def google_oauth_callback():
    """
    Endpoint to handle Google OAuth callback.

    Returns:
        dict: The user information.
    """
    token = await oauth.google.authorize_access_token()
    return await google_authorize_callback(token)
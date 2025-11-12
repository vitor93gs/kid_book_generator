"""
Service for handling user signup.
"""

from fastapi import HTTPException
from passlib.context import CryptContext
from app.models.user_schema import User
from app.mongodb import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

def create_user(user: User) -> User:
    """
    Creates a new user in the database.

    Args:
        user (User): The user data.

    Raises:
        HTTPException: If the email is already registered.

    Returns:
        User: The created user with an assigned ID.
    """
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.hashed_password:
        user.hashed_password = hash_password(user.hashed_password)

    user_dict = user.model_dump()
    user_dict.pop("id", None)
    result = users_collection.insert_one(user_dict)
    user.id = str(result.inserted_id)
    return user
"""
MongoDB connection utility for the kid_book_generator project.
"""

from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_USER = os.getenv("MONGODB_USER", "default_user")
MONGODB_PASS = os.getenv("MONGODB_PASS", "default_pass")
MONGODB_DB = os.getenv("MONGODB_DB", "kid_book_db")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set in the environment variables.")

try:
    client = MongoClient(
        MONGODB_URI,
        username=MONGODB_USER,
        password=MONGODB_PASS,
        server_api=ServerApi("1"),
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )
    # Attempt to ping the server to check connection
    client.admin.command('ping')
    db = client[MONGODB_DB]
    characters_collection = db["characters"]
except errors.ServerSelectionTimeoutError as e:
    raise RuntimeError(f"Could not connect to MongoDB: {e}")
except Exception as e:
    raise RuntimeError(f"MongoDB connection error: {e}")

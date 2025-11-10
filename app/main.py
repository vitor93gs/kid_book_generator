from fastapi import FastAPI
from app.routers.character import router as character_router
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

app.include_router(character_router)
# Example usage of an environment variable
api_key = os.getenv("GEMINI_KEY")
if not api_key:
    raise ValueError("GEMINI_KEY is not set in the environment variables.")
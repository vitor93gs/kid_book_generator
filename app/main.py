from fastapi import FastAPI
from app.routers.character import router as character_router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

app.include_router(character_router)
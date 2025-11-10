

from fastapi import APIRouter, UploadFile, HTTPException, File
from app.services.character.character_service import get_character_description
from app.services.character.character_crud import create_character
from app.models.character_schema import CharacterCreate

router = APIRouter()

@router.post("/character")
async def character_route(file: UploadFile = File(...)):
    """
    Analyzes an image of a person and saves the structured JSON response to MongoDB.

    Args:
        file (UploadFile): The image file to analyze.

    Returns:
        dict: The inserted character document (with _id).

    Raises:
        HTTPException: If there is an error processing the image or communicating with the Gemini API.
    """
    try:
        image_content = await file.read()
        response = get_character_description(image_content)
        character_in = CharacterCreate(**response)
        db_character = create_character(character_in)
        return db_character
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
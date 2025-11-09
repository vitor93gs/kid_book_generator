from fastapi import APIRouter, UploadFile, HTTPException
from app.services.character.character_service import get_character_description

router = APIRouter()

@router.post("/character")
async def character_route(file: UploadFile):
    """
    Analyzes an image of a person and returns a structured JSON response.

    Args:
        file (UploadFile): The image file to analyze.

    Returns:
        dict: A JSON response with the analysis of the person in the image.
    
    Raises:
        HTTPException: If there is an error processing the image or communicating with the Gemini API.
    """
    try:
        # Read the uploaded image file
        image_content = await file.read()

        # Call the Gemini prompt service
        response = get_character_description(image_content)

        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
from app.services.gemini.client import generate_text_from_image
from fastapi import HTTPException
import json

def get_character_description(image_file: bytes) -> dict:
    """
    Gets a character description from an image using the Gemini API.

    Args:
        image_file (bytes): The image file to analyze.

    Returns:
        dict: The JSON response from Gemini.
    """
    with open("app/system_messages/character_prompt.txt", "r") as f:
        prompt = f.read()
    
    try:
        response_text = generate_text_from_image(prompt, image_file)
        # The response from Gemini is a string, so we need to parse it as JSON
        # The response may contain markdown, so we need to strip it
        response_text = response_text.strip().replace("```json", "").replace("```", "")
        return json.loads(response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response from Gemini: {str(e)}")
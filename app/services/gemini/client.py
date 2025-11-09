import google.generativeai as genai
import os
from fastapi import HTTPException
from PIL import Image
import io

def configure_gemini():
    """
    Configures the Gemini API with the API key from environment variables.
    """
    api_key = os.getenv("GEMINI_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured.")
    genai.configure(api_key=api_key)

def generate_text_from_image(prompt: str, image: bytes) -> str:
    """
    Generates text from a prompt and an image using the Gemini API.

    Args:
        prompt (str): The text prompt to send to the model.
        image (bytes): The image to send to the model.

    Returns:
        str: The generated text from the model.
    """

    configure_gemini()
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    img = Image.open(io.BytesIO(image))
    response = model.generate_content([prompt, img])
    return response.text

def list_models():
    """
    Lists the available Gemini models.

    Returns:
        list: A list of available models.
    """
    configure_gemini()
    models = genai.list_models()
    return [m.name for m in models]

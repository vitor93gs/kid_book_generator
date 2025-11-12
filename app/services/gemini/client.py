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

def generate_text_from_image(prompt: str, image: bytes, system_message: str | None = None) -> str:
    """
    Generates text from a prompt and an image using the Gemini API.

    Args:
        prompt (str): The text prompt to send to the model.
        image (bytes): The image to send to the model.

    Returns:
        str: The generated text from the model.
    """

    configure_gemini()
    img = Image.open(io.BytesIO(image))

    # Prefer using a chat-style API if available so we can send a real system
    # message. Fall back to the older generate_content approach when not.
    try:
        # Try to use a chat model if the library provides it.
        if hasattr(genai, 'ChatModel'):
            chat = genai.ChatModel('models/gemini-2.5-chat')
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            # Some SDK versions accept images in a separate parameter; attempt a
            # generic call and let the SDK raise if unsupported.
            resp = chat.generate(messages=messages, image=img)
            return getattr(resp, 'text', str(resp))
    except Exception:
        # ignore and fall back
        pass

    # Fallback: include the system message as a preface to the prompt. This
    # isn't a true system role but keeps backward compatibility.
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    combined = prompt
    if system_message:
        combined = f"SYSTEM:\n{system_message}\n---\n{prompt}"
    response = model.generate_content([combined, img])
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

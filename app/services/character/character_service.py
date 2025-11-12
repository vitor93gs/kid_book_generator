from app.services.gemini.client import generate_text_from_image
from fastapi import HTTPException
import json
from app.services.toon.toon_service import json_to_toon, toon_to_json
import re
import os


def get_character_description(image_file: bytes) -> dict:
    """
    Gets a character description from an image using the Gemini API.

    Args:
        image_file (bytes): The image file to analyze.

    Returns:
        dict: The JSON response from Gemini.
    """
    # Load the system prompt template and the canonical JSON schema. We'll
    # include the schema converted to TOON in the system message to save
    # tokens on both input and output.
    prompt_template = ""
    try:
        with open("app/system_messages/character_prompt.txt", "r") as f:
            prompt_template = f.read()
    except Exception:
        prompt_template = "You are an advanced AI model tasked with analyzing images of individuals. Respond in TOON format."

    # Replace any {{TOON:<filename>}} placeholders in the template by loading
    # the corresponding JSON file from app/json_schemas and converting it to
    # TOON. This keeps the system message template small and allows schema
    # edits in one place.
    def _replace_toon_placeholders(template: str) -> str:
        """Replace any {{TOON:<filename>}} placeholders with raw TOON strings.

        The function loads the referenced JSON file from ``app/json_schemas``
        and converts it to TOON using the canonical TOON service. If a
        schema file cannot be loaded it emits an empty string for that
        placeholder so the caller can still proceed.

        Args:
            template: The prompt template containing {{TOON:...}} markers.

        Returns:
            The template with placeholders replaced by TOON strings.
        """
        def _loader(match):
            fname = match.group(1).strip()
            schema_path = os.path.join("app", "json_schemas", fname)
            try:
                with open(schema_path, "r") as sf:
                    obj = json.load(sf)
                return json_to_toon(obj)
            except Exception:
                # If the schema file isn't available, replace with an empty
                # placeholder but keep going — the caller may still proceed.
                return ""

        return re.sub(r"\{\{TOON:([^}]+)\}\}", _loader, template)

    processed_template = _replace_toon_placeholders(prompt_template)

    # Split the processed template into header (system message) and prompt
    # (the user prompt) by looking for 'PROMPT:'. If not present, fall back
    # to defaults.
    if "PROMPT:" in processed_template:
        header, after = processed_template.split("PROMPT:", 1)
        system_message = header.strip()
        prompt_body = after.strip()
    else:
        system_message = processed_template.strip()
        prompt_body = "Analyze the provided image and extract the details about the person, responding ONLY in TOON format."

    # Ask the model to reply in TOON and send the schema as a system message
    prompt = prompt_body + "\n\nRespond ONLY in TOON format (compact key=value pairs, use `|` or newlines to separate)."

    try:
        response_text = generate_text_from_image(prompt, image_file, system_message=system_message)
        # The model may return fenced code blocks or either JSON or TOON.
        response_text = response_text.strip()

        # Try JSON first
        try:
            # strip possible fences
            cleaned = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception:
            # Try to extract an embedded JSON block from the response
            try:
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = response_text[start:end+1]
                    return json.loads(candidate)
            except Exception:
                pass

            # Attempt to parse TOON; if it doesn't produce expected structured keys,
            # raise an error to make the failure explicit.
            try:
                parsed = toon_to_json(response_text)
                # basic validation: expect at least one of the top-level character keys
                expected_keys = {
                    "meta",
                    "general",
                    "head",
                    "hair",
                    "skin",
                    "face",
                    "measurements_and_proportions",
                    "pose_and_landmarks",
                    "clothing_and_accessories",
                    "annotations",
                }
                if not expected_keys.intersection(parsed.keys()):
                    raise ValueError("Parsed TOON does not contain expected character keys")
                return parsed
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Error parsing model response: {str(e2)}; raw={response_text}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response from Gemini: {str(e)}")
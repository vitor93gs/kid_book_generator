from fastapi.testclient import TestClient
from app.main import app
from jsonschema import validate
import json

# Load the character schema
with open("app/json_schemas/character.json", "r") as schema_file:
    character_schema = json.load(schema_file)

client = TestClient(app)

def test_character_route():
    """End-to-end test for the `/character` route using a real image.

    The test sends an actual image file to the endpoint and validates that
    the response conforms to the `character.json` schema.
    """
    # Use the actual image file for testing
    with open("tests/assets/test_person.png", "rb") as image_file:
        files = {"file": ("test_person.png", image_file, "image/png")}

        response = client.post("/character", files=files)

        if response.status_code != 200:
            print(f"Error response: {response.json()}")

        assert response.status_code == 200, "Response status code is not 200"
        
        # Validate the response JSON against the schema
        response_json = response.json()
        validate(instance=response_json, schema=character_schema)
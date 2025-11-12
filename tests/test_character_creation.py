from dotenv import load_dotenv
load_dotenv()


from fastapi.testclient import TestClient
from app.main import app
from app.mongodb import characters_collection
from bson import ObjectId
from dotenv import load_dotenv
import pytest

# Load environment variables
load_dotenv()

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def cleanup_created_characters():
    """Fixture to collect and clean up characters created during the test.

    Yields a mutable list which tests should append created character IDs to.
    After the test completes the fixture will remove those documents from the
    `characters` collection.
    """
    created_character_ids = []
    yield created_character_ids
    for character_id in created_character_ids:
        characters_collection.delete_one({"_id": ObjectId(character_id)})

def test_character_creation_route(cleanup_created_characters):
    """
    Test that a character can be created and is saved in MongoDB, then clean up only that character.
    """
    test_image_path = "tests/assets/test_person.png"
    with open(test_image_path, "rb") as image_file:
        files = {"file": ("test_person.png", image_file, "image/png")}
        response = client.post("/character", files=files)
        assert response.status_code == 200, f"Unexpected status: {response.status_code}, {response.text}"
        data = response.json()
        # Check that an _id is present in the response
        assert "_id" in data
        cleanup_created_characters.append(data["_id"])

    # Check that the character is actually in the database
    db_obj = characters_collection.find_one({"_id": ObjectId(data["_id"])})
    assert db_obj is not None
    assert "meta" in data

    # Clean up: remove only the created character
    delete_result = characters_collection.delete_one({"_id": ObjectId(data["_id"])})
    assert delete_result.deleted_count == 1, "Character was not deleted from the database"

    # Verify the character is no longer in the database
    db_obj_after_deletion = characters_collection.find_one({"_id": ObjectId(data["_id"])})
    assert db_obj_after_deletion is None, "Character still exists in the database after deletion"

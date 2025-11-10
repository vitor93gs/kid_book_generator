

from fastapi import HTTPException
from app.models.character_schema import CharacterCreate
from app.mongodb import characters_collection


def create_character(character_data: CharacterCreate) -> dict:
    """
    Insert a new character document into MongoDB.

    Args:
        character_data (CharacterCreate): Data for the new character.

    Returns:
        dict: The inserted character document (with _id).

    Raises:
        HTTPException: If the database operation fails.
    """
    from pymongo.errors import PyMongoError
    try:
        character_dict = character_data.model_dump(exclude_unset=True)
        result = characters_collection.insert_one(character_dict)
        character_dict["_id"] = str(result.inserted_id)
        return character_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"MongoDB operation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected MongoDB error: {str(e)}")

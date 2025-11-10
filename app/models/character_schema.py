
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class CharacterCreate(BaseModel):
    """
    Pydantic schema for creating a character, matching the JSON schema.
    """
    meta: Optional[Dict[str, Any]]
    general: Optional[Dict[str, Any]]
    head: Optional[Dict[str, Any]]
    hair: Optional[Dict[str, Any]]
    skin: Optional[Dict[str, Any]]
    face: Optional[Dict[str, Any]]
    measurements_and_proportions: Optional[Dict[str, Any]]
    pose_and_landmarks: Optional[Dict[str, Any]]
    clothing_and_accessories: Optional[Dict[str, Any]]
    annotations: Optional[List[Dict[str, Any]]]

class CharacterRead(CharacterCreate):
    """
    Pydantic schema for reading a character, including the DB id.
    """
    id: int

    class Config:
        orm_mode = True

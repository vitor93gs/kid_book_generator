from pydantic import BaseModel

class User(BaseModel):
    id: str | None = None
    email: str
    hashed_password: str | None = None
    oauth_provider: str | None = None
    oauth_id: str | None = None
    full_name: str | None = None
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CollectionCreate(BaseModel):
    name: str

class CollectionOut(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class DatasetCreate(BaseModel):
    collection_id: UUID
    name: str

class DatasetOut(BaseModel):
    id: UUID
    collection_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

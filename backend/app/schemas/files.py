from pydantic import BaseModel
from uuid import UUID

class FileOut(BaseModel):
    id: UUID
    submission_id: UUID
    path: str
    storage_key: str

    class Config:
        from_attributes = True

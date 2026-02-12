from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class CollectionCreate(BaseModel):
    name: str

class CollectionOut(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# Dataset Schemas
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


# Run Schemas
class RunCreate(BaseModel):
    dataset_id: UUID
    config_json: Dict[str, Any]


class RunOut(BaseModel):
    id: UUID
    dataset_id: UUID
    status: str
    stage: str
    progress_pct: int
    config_json: Dict[str, Any]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True

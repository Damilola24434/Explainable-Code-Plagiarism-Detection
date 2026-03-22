from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List


class RunCreate(BaseModel):
    dataset_id: UUID
    config_json: Dict[str, Any] = {}


class RunOut(BaseModel):
    id: UUID
    dataset_id: UUID
    status: str          # QUEUED | RUNNING | DONE | FAILED
    stage: str           # INGEST | TOKENS | AST | REPORT
    progress_pct: int
    config_json: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SimilarityResultOut(BaseModel):
    id: UUID
    file_a: str          # path of file A
    file_b: str          # path of file B
    file_a_id: UUID
    file_b_id: UUID
    similarity: float    # 0.0 – 1.0
    risk: str            # HIGH | MEDIUM | LOW

    class Config:
        from_attributes = True

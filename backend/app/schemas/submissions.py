from pydantic import BaseModel
from uuid import UUID

class SubmissionOut(BaseModel):
    id: UUID
    dataset_id: UUID
    student_label: str

    class Config:
        from_attributes = True

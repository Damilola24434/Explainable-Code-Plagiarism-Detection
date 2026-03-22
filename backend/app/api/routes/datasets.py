from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.models.models import Dataset, Submission, File
from app.schemas.datasets import DatasetCreate, DatasetOut
from app.schemas.files import FileOut

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def get_dataset_or_404(db: Session, dataset_id: UUID) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def query_dataset_files(db: Session, dataset_id: UUID) -> list[File]:
    return (
        db.query(File)
        .join(Submission, Submission.id == File.submission_id)
        .filter(Submission.dataset_id == dataset_id)
        .all()
    )

@router.post("/", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = Dataset(**payload.dict())
    db.add(dataset); db.commit(); db.refresh(dataset)
    return dataset

@router.get("/", response_model=list[DatasetOut])
def list_datasets(collection_id: UUID | None = None, db: Session = Depends(get_db)):
    query = db.query(Dataset)
    if collection_id:
        query = query.filter(Dataset.collection_id == collection_id)
    return query.all()

@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    return get_dataset_or_404(db, dataset_id)

@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(dataset_id: UUID, payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id)
    dataset.name = payload.name
    db.commit(); db.refresh(dataset)
    return dataset

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id)
    db.delete(dataset); db.commit()

@router.get("/{dataset_id}/files", response_model=list[FileOut])
def list_dataset_files(dataset_id: UUID, db: Session = Depends(get_db)):
    try:
        get_dataset_or_404(db, dataset_id)
        return query_dataset_files(db, dataset_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.db import get_db
from app.models.models import Collection, Dataset
from app.schemas.datasets import DatasetCreate, DatasetOut

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# TEMP owner_id until auth is built
TEMP_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
  
    # Verify collection exists and belongs to current user
    collection = db.query(Collection).filter(
        Collection.id == payload.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    dataset = Dataset(collection_id=payload.collection_id, name=payload.name)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/", response_model=list[DatasetOut])
def list_datasets(collection_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
   
    query = db.query(Dataset)
    
    if collection_id:
        # Verify collection exists and belongs to current user
        collection = db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.owner_id == TEMP_OWNER_ID
        ).first()
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection not found or access denied"
            )
        
        query = query.filter(Dataset.collection_id == collection_id)
    
    return query.all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
  
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Verify user owns the collection
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    return dataset


@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(
    dataset_id: uuid.UUID,
    payload: DatasetCreate,
    db: Session = Depends(get_db)
):
  
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Verify user owns the collection
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    dataset.name = payload.name
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
  
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Verify user owns the collection
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    db.delete(dataset)
    db.commit()

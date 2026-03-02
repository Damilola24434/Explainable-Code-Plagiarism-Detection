from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI tools for routing and error handling
from sqlalchemy.orm import Session  # Used to interact with the database session
import uuid  # For working with UUID identifiers

from app.core.db import get_db  # Database dependency that provides a session
from app.models.models import Collection, Dataset  # Database models
from app.schemas.datasets import DatasetCreate, DatasetOut  # Request and response schemas


# Creating a router for dataset-related endpoints
# All routes here will start with /api/datasets
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


# Temporary owner ID until authentication is implemented
# This simulates a logged-in user for now
TEMP_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
  
    # First, confirm the collection exists and belongs to the current user
    # This prevents creating datasets under collections the user does not own
    collection = db.query(Collection).filter(
        Collection.id == payload.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If the collection does not exist, return 404
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Create a new dataset linked to the provided collection
    dataset = Dataset(collection_id=payload.collection_id, name=payload.name)

    # Add it to the database session
    db.add(dataset)

    # Commit to save it permanently
    db.commit()

    # Refresh to get updated values like the generated ID
    db.refresh(dataset)

    # Return the newly created dataset
    return dataset


@router.get("/", response_model=list[DatasetOut])
def list_datasets(collection_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
   
    # Start building a base query for datasets
    query = db.query(Dataset)
    
    # If a collection_id is provided, filter datasets by that collection
    if collection_id:
        # Make sure the collection exists and belongs to the user
        collection = db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.owner_id == TEMP_OWNER_ID
        ).first()
        
        # If collection not found or not owned by user, deny access
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection not found or access denied"
            )
        
        # Apply filter to only return datasets under this collection
        query = query.filter(Dataset.collection_id == collection_id)
    
    # Execute the query and return all results
    return query.all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
  
    # Retrieve dataset by ID
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    # If it does not exist, return 404
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Verify that the dataset belongs to a collection owned by the user
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If ownership check fails, return error
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # If everything is valid, return the dataset
    return dataset


@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(
    dataset_id: uuid.UUID,
    payload: DatasetCreate,
    db: Session = Depends(get_db)
):
  
    # Look for the dataset first
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    # If it does not exist, return 404
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Confirm the user owns the parent collection
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If ownership fails, deny access
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Update dataset name with new value
    dataset.name = payload.name

    # Save changes
    db.commit()

    # Refresh to get updated values
    db.refresh(dataset)

    # Return updated dataset
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
  
    # Find the dataset to delete
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    # If not found, return 404
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Confirm the dataset belongs to a collection owned by the user
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If ownership check fails, deny deletion
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Delete dataset from database
    db.delete(dataset)

    # Commit deletion permanently
    db.commit()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.db import get_db
from app.models.models import Collection, Dataset, Run
from app.schemas.runs import RunCreate, RunOut

router = APIRouter(prefix="/api/runs", tags=["runs"])

# TEMP owner_id until auth is built
TEMP_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    """
    Create a new run for a dataset with status=QUEUED.
    
    Args:
        payload: RunCreate schema with dataset_id and config_json
        db: Database session dependency
        
    Returns:
        RunOut: Created run object
        
    Raises:
        HTTPException: 404 if dataset not found or user doesn't own the collection
    """
    # Verify dataset exists and user owns the collection
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    
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
    
    # Create run with status=QUEUED
    run = Run(
        dataset_id=payload.dataset_id,
        status="QUEUED",
        stage="INGEST",
        progress_pct=0,
        config_json=payload.config_json
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific run by ID with its status and progress.
    
    Args:
        run_id: UUID of the run
        db: Database session dependency
        
    Returns:
        RunOut: Run object with current status and progress
        
    Raises:
        HTTPException: 404 if run not found or user doesn't own the dataset's collection
    """
    run = db.query(Run).filter(Run.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    # Verify user owns the dataset's collection
    dataset = db.query(Dataset).filter(Dataset.id == run.dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied"
        )
    
    return run

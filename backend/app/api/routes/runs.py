from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI routing and error handling tools
from sqlalchemy.orm import Session  # Database session for queries
import uuid  # For handling UUID identifiers

from app.core.db import get_db  # Dependency that provides DB session
from app.models.models import Collection, Dataset, Run  # Database models
from app.schemas.runs import RunCreate, RunOut  # Request and response schemas

# Router for run-related endpoints
# All routes here start with /api/runs
router = APIRouter(prefix="/api/runs", tags=["runs"])

# Temporary owner ID until authentication system is implemented
# This simulates a logged-in user for now
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

    # First check if the dataset exists in the database
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    
    # If dataset does not exist, return 404
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Now verify that the dataset belongs to a collection owned by this user
    # This prevents someone from creating runs on datasets they do not own
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If ownership check fails, deny access
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Create a new run with default processing state
    # Initially status is QUEUED and stage starts at INGEST
    run = Run(
        dataset_id=payload.dataset_id,
        status="QUEUED",
        stage="INGEST",
        progress_pct=0,
        config_json=payload.config_json
    )

    # Add run to session
    db.add(run)

    # Commit to save permanently
    db.commit()

    # Refresh to load generated values like ID and timestamps
    db.refresh(run)

    # Return the created run
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

    # Look for the run in the database
    run = db.query(Run).filter(Run.id == run_id).first()
    
    # If run does not exist, return 404
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    # Retrieve the dataset associated with this run
    dataset = db.query(Dataset).filter(Dataset.id == run.dataset_id).first()
    
    # If dataset somehow does not exist, treat as not found
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    # Verify the collection linked to this dataset belongs to the user
    # This ensures users cannot view runs from other users
    collection = db.query(Collection).filter(
        Collection.id == dataset.collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If ownership check fails, deny access
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied"
        )
    
    # If everything is valid, return the run
    return run

from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI tools for routing and handling errors
from sqlalchemy.orm import Session  # Used to interact with the database session
import uuid  # For handling unique IDs (UUIDs)

from app.core.db import get_db  # This gives us the database connection
from app.models.models import Collection  # The database model for collections
from app.schemas.collections import CollectionCreate, CollectionOut  # Schemas for input validation and output


# Creating a router specifically for collections
# All endpoints here will start with /api/collections
router = APIRouter(prefix="/api/collections", tags=["collections"])


# Temporary owner ID since authentication is not implemented yet
# This is just to simulate a logged-in user for now
TEMP_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
   
    # Creating a new collection object using the name sent from the request
    # Assigning it to the temporary owner
    collection = Collection(owner_id=TEMP_OWNER_ID, name=payload.name)

    # Adding the new collection to the database session
    db.add(collection)

    # Committing the transaction so it saves to the database
    db.commit()

    # Refreshing to get updated values like the generated ID
    db.refresh(collection)

    # Returning the created collection as response
    return collection


@router.get("/", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
   
    # Querying the database to get all collections that belong to this owner
    collections = db.query(Collection).filter(
        Collection.owner_id == TEMP_OWNER_ID
    ).all()

    # Returning the list of collections
    return collections


@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
   
    # Searching for a collection with this ID that belongs to the owner
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If the collection does not exist, raise 404 error
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # If found, return the collection
    return collection


@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionCreate,
    db: Session = Depends(get_db)
):
   
    # Checking if the collection exists and belongs to this owner
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If not found, return 404
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Updating the name of the collection with the new value
    collection.name = payload.name

    # Saving the changes
    db.commit()

    # Refreshing to get the updated version
    db.refresh(collection)

    # Returning the updated collection
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
   
    # Looking for the collection before attempting to delete
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    # If it does not exist, raise 404
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Deleting the collection from the database
    db.delete(collection)

    # Committing the deletion permanently
    db.commit()

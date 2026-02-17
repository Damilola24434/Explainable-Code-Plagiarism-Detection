from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.db import get_db
from app.models.models import Collection
from app.schemas.collections import CollectionCreate, CollectionOut

router = APIRouter(prefix="/api/collections", tags=["collections"])

# TEMP owner_id until auth is built
TEMP_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
   
    collection = Collection(owner_id=TEMP_OWNER_ID, name=payload.name)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


@router.get("/", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
   
    collections = db.query(Collection).filter(
        Collection.owner_id == TEMP_OWNER_ID
    ).all()
    return collections


@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
   
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    return collection


@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionCreate,
    db: Session = Depends(get_db)
):
   
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    collection.name = payload.name
    db.commit()
    db.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
   
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.owner_id == TEMP_OWNER_ID
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    db.delete(collection)
    db.commit()

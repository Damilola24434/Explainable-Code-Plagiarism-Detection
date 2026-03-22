# About Collection.py file:
#It is the file for the backend it essentially handles collection feactures in this project/
#It create API endpoints for creating a colection,listing collections, get one signle colection
# deleting a collction, uploading a zip file to colection.
# It takes a uploaded zip files , opens the uploaded zip files and saves students files into the shred neon cloud database,
# It saves it as datasets,submsision, and files)
#This file is the entry pointy for  the data. before plagiarsim analysis can run, code files must be uploaded and stored and that why this code file matters.
# this file is what connects user uploads from frontend to stored database
#version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./test.db
      - USE_REDIS=1
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  celery:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./test.db
      - USE_REDIS=1
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend    version: '3.8'
    services:
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
    
      backend:
        build: ./backend
        ports:
          - "8000:8000"
        environment:
          - DATABASE_URL=sqlite:///./test.db
          - USE_REDIS=1
          - REDIS_URL=redis://redis:6379/0
        depends_on:
          - redis
    
      celery:
        build: ./backend
        command: celery -A app.celery worker --loglevel=info
        environment:
          - DATABASE_URL=sqlite:///./test.db
          - USE_REDIS=1
          - REDIS_URL=redis://redis:6379/0
        depends_on:
          - redis
    
      frontend:
        build: ./frontend
        ports:
          - "5173:5173"
        depends_on:
          - backend


# let me group realted endpoints together this is very important for the code to be fast 
# the depend is a way to say before running a functio run thee other one first
# this file is what connects user uploads from frontend to stored database

# let me group realted endpoints together this is very important for the code to be fast 
# the depend is a way to say before running a functio run thee other one first
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
#this is the database connection object.. it is passed to every function that will need it
from sqlalchemy.orm import Session
# uuid is for generating and handling unique ids, 

import uuid
#zipfile and io are for handling the uploaded zip files,
import zipfile
import io
 #time to get the current timestamp
import time

#this s a function that opens the datanbase connetion
from app.core.db import get_db
#these are like tables classes. each one of this classes maps to a table in postgreSQL
from app.models.models import Collection, Dataset, Submission, File as FileModel
#he schemas are used to shape the data gpoin in and out of APi
from app.schemas.collections import CollectionCreate, CollectionOut
# create the routes.
router = APIRouter(prefix="/api/collections", tags=["collections"])

# placeholder owner until real auth is added if we decided to do login and sign up
PLACEHOLDER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")

# this fuction is resuable mini funtion. it ask the database to find collection with this id, if nothing i foune 404 error

def get_or_404(db: Session, collection_id: uuid.UUID) -> Collection:
    """Fetch a collection or raise 404."""
    obj = db.query(Collection).filter(Collection.id == collection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Collection not found")
    return obj

# this is a helper function it reads all the file paths in a ZIP and groups tem by the first folder name. the result is a dictionalry which helps with run time.time complexity when we want to save the files in the database. it is based on the assumption that each student upload a folder with their name and all their files are in that folder. if there is no folder it will be grouped under "root"
def group_zip_files(names: list[str]) -> dict[str, list[str]]:
    """Group zip entry paths by top-level folder (one folder = one student)."""
    groups: dict[str, list[str]] = {}
    for path in names:
        if path.endswith('/'):
            continue
        student = path.split('/')[0] if '/' in path else "root"
        groups.setdefault(student, []).append(path)
    return groups

# this is also a helper funtion it talkes the grouped fles and saves them ti the databse note not the zip files but the files in the zip files
def save_zip_to_db(db: Session, dataset_id: uuid.UUID, z: zipfile.ZipFile) -> None:
    """Create Submission + File rows from an open ZIP."""
    for student, paths in group_zip_files(z.namelist()).items():
        sub = Submission(dataset_id=dataset_id, student_label=student if student != "root" else "default")
        db.add(sub)
        db.commit()
        db.refresh(sub)
        for fpath in paths:
            data = z.read(fpath)
            rel = fpath if student == "root" else '/'.join(fpath.split('/')[1:])
            db.add(FileModel(
                submission_id=sub.id, path=rel, language="",
                size_bytes=len(data), content_hash="",
                storage_key=fpath, content=data,
            ))
        db.commit()


# --- endpoints ---
#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.post("/", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    c = Collection(name=payload.name, owner_id=PLACEHOLDER_OWNER)
    db.add(c); db.commit(); db.refresh(c)
    return c
    
#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.get("/", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
    return db.query(Collection).all()

#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_or_404(db, collection_id)

#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(collection_id: uuid.UUID, payload: CollectionCreate, db: Session = Depends(get_db)):
    c = get_or_404(db, collection_id)
    c.name = payload.name
    db.commit(); db.refresh(c)
    return c
#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    c = get_or_404(db, collection_id)
    db.delete(c); db.commit()

#The collections endpoint in your API handles all standard CRUD operations 
#for collections. You can create a new collection, list 
#all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five 
#routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file, 
#creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, this are the api routes
@router.post("/{collection_id}/upload")
async def upload_collection_zip(
    collection_id: uuid.UUID,
    upload: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
):
    get_or_404(db, collection_id)
    contents = await upload.read()

    try:
        z = zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")

    dataset = Dataset(collection_id=collection_id, name=f"{upload.filename}_{int(time.time())}")
    db.add(dataset); db.commit(); db.refresh(dataset)

    save_zip_to_db(db, dataset.id, z)
    return {"detail": "upload complete"}

# About Collection.py file:
# It is the file for the backend it essentially handles collection features in this project
# It create API endpoints for creating a collection, listing collections, get one single collection
# deleting a collection, uploading a zip file to collection.
# It takes a uploaded zip files , opens the uploaded zip files and saves students files into the shared neon cloud database,
# It saves it as datasets, submission, and files
# This file is the entry point for the data. before plagiarism analysis can run, code files must be uploaded and stored and that why this code file matters.
# this file is what connects user uploads from frontend to stored database

# let me group related endpoints together this is very important for the code to be fast
# the depend is a way to say before running a function run the other one first
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
# this is the database connection object.. it is passed to every function that will need it
from sqlalchemy.orm import Session
# uuid is for generating and handling unique ids,

import uuid
# zipfile and io are for handling the uploaded zip files,
import zipfile
import io
# time to get the current timestamp
import time

# this is a function that opens the database connection
from app.core.db import get_db
# these are like tables classes. each one of this classes maps to a table in postgreSQL
from app.models.models import Collection, Dataset, Submission, File as FileModel
# the schemas are used to shape the data going in and out of API
from app.schemas.collections import CollectionCreate, CollectionOut

# create the routes.
router = APIRouter(prefix="/api/collections", tags=["collections"])

# placeholder owner until real auth is added if we decided to do login and sign up
PLACEHOLDER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")

# this function is reusable mini function. it ask the database to find collection with this id, if nothing is found 404 error

def get_or_404(db: Session, collection_id: uuid.UUID) -> Collection:
    """Fetch a collection or raise 404."""
    obj = db.query(Collection).filter(Collection.id == collection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Collection not found")
    return obj

# this is a helper function it reads all the file paths in a ZIP and groups them by the first folder name. the result is a dictionary which helps with runtime.time complexity when we want to save the files in the database. it is based on the assumption that each student upload a folder with their name and all their files are in that folder. if there is no folder it will be grouped under "root"
def group_zip_files(names: list[str]) -> dict[str, list[str]]:
    """Group zip entry paths by top-level folder (one folder = one student)."""
    groups: dict[str, list[str]] = {}
    for path in names:
        if path.endswith('/'):
            continue
        student = path.split('/')[0] if '/' in path else "root"
        groups.setdefault(student, []).append(path)
    return groups

# this is also a helper function it takes the grouped files and saves them to the database note not the zip files but the files in the zip files
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
# The collections endpoint in your API handles all standard CRUD operations
# for collections. You can create a new collection, list
# all collections, get a collection by its ID, update a
# collection name, delete a collection, and upload a ZIP file to a specific collection. The first five
# routes cover typical database actions, while the upload route is unique. It reads and validates a ZIP file,
# creates a dataset within the collection, and saves each student submission and file to the database so your plagiarism pipeline can process the stored code.
# this is basically the api endpoint for the collection, these are the api routes

@router.post("/", response_model=CollectionOut, status_code=201)
def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    """Create a new collection."""
    new = Collection(name=collection.name, owner_id=PLACEHOLDER_OWNER)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.get("/", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
    """List all collections."""
    return db.query(Collection).all()

@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a collection by ID."""
    return get_or_404(db, collection_id)

@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(collection_id: uuid.UUID, collection: CollectionCreate, db: Session = Depends(get_db)):
    """Update a collection."""
    obj = get_or_404(db, collection_id)
    obj.name = collection.name
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{collection_id}")
def delete_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a collection."""
    obj = get_or_404(db, collection_id)
    db.delete(obj)
    db.commit()
    return {"message": "Collection deleted"}

@router.post("/{collection_id}/upload")
def upload_zip(collection_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a ZIP file to a collection."""
    col = get_or_404(db, collection_id)
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")
    dataset = Dataset(collection_id=collection_id, uploaded_at=time.time())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    try:
        z = zipfile.ZipFile(io.BytesIO(file.file.read()))
        save_zip_to_db(db, dataset.id, z)
        return {"message": "ZIP uploaded successfully", "dataset_id": dataset.id}
    except Exception as e:
        db.delete(dataset)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

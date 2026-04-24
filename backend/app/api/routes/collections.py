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
import hashlib
# time to get the current timestamp
import time
import os
from collections import Counter

# this is a function that opens the database connection
from app.core.db import get_db
# these are like tables classes. each one of this classes maps to a table in postgreSQL
from app.models.models import Collection, Dataset, Submission, File as FileModel
from app.pipeline.ast.run_stage import infer_language_from_path
from app.pipeline.upload.zip_utils import group_zip_files, zip_entry_skip_reason
# the schemas are used to shape the data going in and out of API
from app.schemas.collections import CollectionCreate, CollectionOut

# create the routes.
router = APIRouter(prefix="/api/collections", tags=["collections"])

# placeholder owner until real auth is added if we decided to do login and sign up
PLACEHOLDER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
MAX_ZIP_BYTES = int(os.getenv("MAX_UPLOAD_ZIP_BYTES", str(25 * 1024 * 1024)))
MAX_SOURCE_FILES = int(os.getenv("MAX_UPLOAD_SOURCE_FILES", "250"))
MAX_SOURCE_FILE_BYTES = int(os.getenv("MAX_UPLOAD_SOURCE_FILE_BYTES", str(1 * 1024 * 1024)))

# this function is reusable mini function. it ask the database to find collection with this id, if nothing is found 404 error

def get_or_404(db: Session, collection_id: uuid.UUID) -> Collection:
    """Fetch a collection or raise 404."""
    obj = db.query(Collection).filter(Collection.id == collection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Collection not found")
    return obj
def collect_zip_skip_summary(z: zipfile.ZipFile) -> list[dict[str, str]]:
    skipped: list[dict[str, str]] = []
    for path in z.namelist():
        reason = zip_entry_skip_reason(path)
        if reason and reason != "directory":
            skipped.append({"path": path, "reason": reason})
    return skipped


def build_upload_warnings(
    *,
    stored_count: int,
    skipped_count: int,
    language_counts: Counter,
) -> list[str]:
    warnings: list[str] = []
    comparable_languages = [lang for lang, count in language_counts.items() if count >= 2]
    if stored_count == 1:
        warnings.append("Only one supported source file was uploaded, so analysis cannot compare file pairs yet.")
    elif stored_count > 1 and not comparable_languages:
        warnings.append("Files were uploaded, but no language group has at least two files for same-language comparison.")
    if skipped_count > 0:
        warnings.append(f"{skipped_count} unsupported or system metadata file(s) were skipped.")
    return warnings


# this is also a helper function it takes the grouped files and saves them to the database note not the zip files but the files in the zip files
def save_zip_to_db(db: Session, dataset_id: uuid.UUID, z: zipfile.ZipFile) -> dict:
    """Create Submission + File rows from an open ZIP."""
    skipped = collect_zip_skip_summary(z)
    groups = group_zip_files(z.namelist())
    source_paths = [path for paths in groups.values() for path in paths]
    if not source_paths:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No supported source files found. Upload Python, Java, C, C++, or JavaScript files.",
                "stored_files": 0,
                "skipped_files": len(skipped),
                "skipped": skipped[:50],
            },
        )
    if len(source_paths) > MAX_SOURCE_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many supported source files. Limit is {MAX_SOURCE_FILES}.",
        )

    stored_count = 0
    language_counts: Counter = Counter()
    for student, paths in group_zip_files(z.namelist()).items():
        sub = Submission(dataset_id=dataset_id, student_label=student if student != "root" else "default")
        db.add(sub)
        db.commit()
        db.refresh(sub)
        for fpath in paths:
            data = z.read(fpath)
            if len(data) > MAX_SOURCE_FILE_BYTES:
                skipped.append({"path": fpath, "reason": f"file too large; limit is {MAX_SOURCE_FILE_BYTES} bytes"})
                continue
            rel = fpath if student == "root" else '/'.join(fpath.split('/')[1:])
            language = infer_language_from_path(rel) or ""
            db.add(FileModel(
                submission_id=sub.id, path=rel, language=language,
                size_bytes=len(data), content_hash=hashlib.sha256(data).hexdigest(),
                storage_key=fpath, content=data,
            ))
            stored_count += 1
            if language:
                language_counts[language] += 1
        db.commit()

    if stored_count == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No supported source files were stored after upload validation.",
                "stored_files": 0,
                "skipped_files": len(skipped),
                "skipped": skipped[:50],
            },
        )

    return {
        "stored_files": stored_count,
        "skipped_files": len(skipped),
        "skipped": skipped[:50],
        "language_counts": dict(language_counts),
        "warnings": build_upload_warnings(
            stored_count=stored_count,
            skipped_count=len(skipped),
            language_counts=language_counts,
        ),
    }


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
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")
    base_name = os.path.splitext(file.filename)[0] or "dataset"
    dataset_name = f"{base_name}-{int(time.time())}"
    dataset = Dataset(collection_id=collection_id, name=dataset_name)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    try:
        zip_bytes = file.file.read()
        if len(zip_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded ZIP file is empty.")
        if len(zip_bytes) > MAX_ZIP_BYTES:
            raise HTTPException(status_code=400, detail=f"ZIP file is too large. Limit is {MAX_ZIP_BYTES} bytes.")
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
        summary = save_zip_to_db(db, dataset.id, z)
        return {"message": "ZIP uploaded successfully", "dataset_id": dataset.id, **summary}
    except zipfile.BadZipFile:
        db.delete(dataset)
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file.")
    except HTTPException:
        db.delete(dataset)
        db.commit()
        raise
    except Exception as e:
        db.delete(dataset)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

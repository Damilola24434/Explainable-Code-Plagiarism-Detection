from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
import uuid
import zipfile
import io
import time

from app.core.db import get_db
from app.models.models import Collection, Dataset, Submission, File as FileModel
from app.schemas.collections import CollectionCreate, CollectionOut

router = APIRouter(prefix="/api/collections", tags=["collections"])

# placeholder owner until real auth is added
PLACEHOLDER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_or_404(db: Session, collection_id: uuid.UUID) -> Collection:
    """Fetch a collection or raise 404."""
    obj = db.query(Collection).filter(Collection.id == collection_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Collection not found")
    return obj


def group_zip_files(names: list[str]) -> dict[str, list[str]]:
    """Group zip entry paths by top-level folder (one folder = one student)."""
    groups: dict[str, list[str]] = {}
    for path in names:
        if path.endswith('/'):
            continue
        student = path.split('/')[0] if '/' in path else "root"
        groups.setdefault(student, []).append(path)
    return groups


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

@router.post("/", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    c = Collection(name=payload.name, owner_id=PLACEHOLDER_OWNER)
    db.add(c); db.commit(); db.refresh(c)
    return c

@router.get("/", response_model=list[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
    return db.query(Collection).all()

@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_or_404(db, collection_id)

@router.put("/{collection_id}", response_model=CollectionOut)
def update_collection(collection_id: uuid.UUID, payload: CollectionCreate, db: Session = Depends(get_db)):
    c = get_or_404(db, collection_id)
    c.name = payload.name
    db.commit(); db.refresh(c)
    return c

@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: uuid.UUID, db: Session = Depends(get_db)):
    c = get_or_404(db, collection_id)
    db.delete(c); db.commit()

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

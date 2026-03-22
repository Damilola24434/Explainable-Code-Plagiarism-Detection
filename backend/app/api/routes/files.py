# About files.py file:
# This file handles getting one stored code file by it id. this is after all the files have been uploaded to dataset
#if it exists , it returns the raw file content. if it does not exist it return 44 error
#This file ensure that each code file submostted is sucessfully stored and can be retrieved for analysis or viewing.
#This gile helps frontend or analysis views can open actia code content after upload. do in the frotend you can see and get access to what was stored. you can see the content of each files.
# Colection and datasers organise data, but this fie gives access to the real code text when needed.



# let me group realted endpoints together this is very important for the code to be fast 
# the depend is a way to say before running a functio run thee other one first
from fastapi import APIRouter, Depends, HTTPException
#this is the database connection object.. it is passed to every function that will need it
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import io

from app.core.db import get_db
from app.models.models import File as FileModel

router = APIRouter(prefix="/api/files", tags=["files"])


def get_file_or_404(db: Session, file_id: UUID) -> FileModel:
    file_row = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    if file_row.content is None:
        raise HTTPException(status_code=404, detail="File content not found")
    return file_row

@router.get("/{file_id}")
def get_file(file_id: UUID, db: Session = Depends(get_db)):
    """Return the raw contents of a stored file from database."""
    f = get_file_or_404(db, file_id)
    return StreamingResponse(
        io.BytesIO(f.content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={f.path}"}
    )

# About datasets.py file:
#This file manages dataset Apis. it allows the app to create dataset, list the dataset that was gotten from the uploaded zip file
# get one dataser, delete a dataser, list all files in a dataset. 
# the main Idea of this file is to manage for instace a folder that has lots f dataset.. if a 
# if a colection can have many datasets.A dataset cotains submissions/files used for plagrism checking
# This code file is the middle layer between collections and actual code files.
#this code fie is important becuaseafet for instace a ZIP upload creates datasets , this files helps the frontend viw and manage those dtasers and files before anlysis runs.


# let me group realted endpoints together this is very important for the code to be fast 
# the depend is a way to say before running a functio run thee other one first
from fastapi import APIRouter, Depends, HTTPException, status
#this is the database connection object.. it is passed to every function that will need it
from sqlalchemy.orm import Session
# uuid is for generating and handling unique ids, 
from uuid import UUID
#imports the databse sessions provider that is used with depends so each api request will get a DB seiion and it will be closed
from app.core.db import get_db
# this imports SQLAlchemy modes for the datasets,submissios,individual files
from app.models.models import Dataset, Submission, File
# this imports the pydantic schemas for the datasets and files, these are used to shape the data going in and out of the API
from app.schemas.datasets import DatasetCreate, DatasetOut
# this imports the pydantic schema for the file output, this is used to shape the data going out of the API when we list the files in a dataset
from app.schemas.files import FileOut
# this is the setup ad router for he dataset file
router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# this is a helper function the means all rouyes in thi file will start with api/dataser
def get_dataset_or_404(db: Session, dataset_id: UUID) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

# also a helper fuction that gets all the files that will belong to a dataset. it will join file with submission and 
#filters by submisionid. ths files are inked to submissions and submission are linked to dataset
def query_dataset_files(db: Session, dataset_id: UUID) -> list[File]:
    return (
        db.query(File)
        .join(Submission, Submission.id == File.submission_id)
        .filter(Submission.dataset_id == dataset_id)
        .all()
    )

#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id
@router.post("/", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = Dataset(**payload.dict())
    db.add(dataset); db.commit(); db.refresh(dataset)
    return dataset
#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id
@router.get("/", response_model=list[DatasetOut])
def list_datasets(collection_id: UUID | None = None, db: Session = Depends(get_db)):
    query = db.query(Dataset)
    if collection_id:
        query = query.filter(Dataset.collection_id == collection_id)
    return query.all()
#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id, this helps in the overall time complexity of the app because we are not making multiple queries to get the files for a dataset, we are doing it in one query with a join and filter
@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    return get_dataset_or_404(db, dataset_id)
#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id, this helps in the overall time complexity of the app because we are not making multiple queries to get the files for a dataset, we are doing it in one query with a join and filter
@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(dataset_id: UUID, payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id)
    dataset.name = payload.name
    db.commit(); db.refresh(dataset)
    return dataset
#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id,this help in the overall time complexity of the app because we are not making multiple queries to get the files for a dataset, we are doing it in one query with a join and filter
@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id)
    db.delete(dataset); db.commit()
#endponst, taks reuest body, relaod the row so returned data includes database generated values for example id, this helps in the overall time complexity of the app because we are not making multiple queries to get the files for a dataset, we are doing it in one query with a join and filter
@router.get("/{dataset_id}/files", response_model=list[FileOut])
def list_dataset_files(dataset_id: UUID, db: Session = Depends(get_db)):
    try:
        get_dataset_or_404(db, dataset_id)
        return query_dataset_files(db, dataset_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")

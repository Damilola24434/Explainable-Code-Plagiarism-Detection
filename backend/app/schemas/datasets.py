# about datasets.py file:

#  this file helps on defining the data shapes for dataset requests and responses
# It tells the backend :
#  what data is allowe when creatinf/ updating a dataset, what data should be returned to the frontend just ensure the data entered is right kind of data to preent user from entering wrong data
#  so models.py defins how data is stored in the database, the datasets.py fils defines how datasets data is sent thorugh api
# it helps keep the API data clean and correct.
# it makes dure frontend and backend actually agree on what dataset data should look like

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class DatasetCreate(BaseModel):
    collection_id: UUID
    name: str

class DatasetOut(BaseModel):
    id: UUID
    collection_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

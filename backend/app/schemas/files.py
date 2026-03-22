# about collections.py file:
#  this file helps on defining the data shapes for files requests and responses
# It tells the backend :
#  what data is allowe when creatinf/ updating a files, what data should be returned to the frontend just ensure the data entered is right kind of data to preent user from entering wrong data
#  so models.py defins how data is stored in the database, the files.py fils defines how files data is sent thorugh api
# it helps keep the API data clean and correct.
# it makes dure frontend and backend actually agree on what files data should look like

from pydantic import BaseModel
from uuid import UUID

class FileOut(BaseModel):
    id: UUID
    submission_id: UUID
    path: str
    storage_key: str

    class Config:
        from_attributes = True

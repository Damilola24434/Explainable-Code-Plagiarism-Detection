# about submissions.py file:
#  this file helps on defining the data shapes for submission requests and responses
# It tells the backend :
#  what data is allowe when creatinf/ updating a submission, what data should be returned to the frontend just ensure the data entered is right kind of data to preent user from entering wrong data
#  so models.py defins how data is stored in the database, the submissions.py fils defines how submission data is sent thorugh api
# it helps keep the API data clean and correct.
# it makes dure frontend and backend actually agree on what submission data should look like

from pydantic import BaseModel
from uuid import UUID

class SubmissionOut(BaseModel):
    id: UUID
    dataset_id: UUID
    student_label: str

    class Config:
        from_attributes = True

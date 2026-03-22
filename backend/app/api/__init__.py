# This file is the glue of all file in the route folder.
# It basically imports all the files in the route folder to make it one combined router to that
# app/main.py can access
from app.api.routes import router
# This is what combines all the api in the routes folder
__all__ = ["router"]

# This file is the glue of all file in the route folder.
# It basically imports all the files in the route folder to make it one combined router to that
# app/main.py can access
from fastapi import APIRouter
#It calls the api route for collection to import it to the central routes file
from app.api.routes.collections import router as collections_router
#It calls the api route for datasets to import it to the central routes file
from app.api.routes.datasets import router as datasets_router
#It calls the api route for runs to import it to the central routes file
from app.api.routes.runs import router as runs_router
#It calls the api route for files to import it to the central routes file
from app.api.routes.files import router as files_router

router = APIRouter()

router.include_router(collections_router)
router.include_router(datasets_router)
router.include_router(runs_router)
router.include_router(files_router)
#calls all the routes folder to be included in the main router that is imported in main.py
__all__ = ["router"]

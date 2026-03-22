# about main.py file:
# this is the backend app entry point.
# It creates creates the Fastapi application.
# It registers all files routes to example collections, datasets, files, runs
# it includes basci app setup like CORS and heath endpoints
# This file stars the backend api
# without this code file routes files will exists but the app would not expoase them to the frontend


from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.db import get_db
from app.api import router as api_router

app = FastAPI(
    title="Explainable Code Plagiarism Detection",
    description="Backend API for code plagiarism detection",
    version="1.0.0"
)

# Allow frontend to reach backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/db-test")
def db_test(db: Session = Depends(get_db)):
    """Test database connection"""
    result = db.execute(text("SELECT 1"))
    return {"db": result.scalar()}


# Include all API routers
app.include_router(api_router)

# This fie is the backend launcher that wires all API routes togther
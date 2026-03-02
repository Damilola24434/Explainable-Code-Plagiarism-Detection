from fastapi import FastAPI, Depends  # FastAPI app and dependency system
from sqlalchemy.orm import Session  # Database session type
from sqlalchemy import text  # Used to execute raw SQL queries

from app.core.db import get_db  # Database session dependency
from app.api import router as api_router  # Main API router that contains all endpoints


# Create the FastAPI application instance
# This is the main entry point of the backend
app = FastAPI(
    title="Explainable Code Plagiarism Detection",
    description="Backend API for code plagiarism detection",
    version="1.0.0"
)


# Simple health check endpoint
# Used to confirm the server is running properly
@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


# Endpoint to test database connectivity
# Useful for confirming the database connection is working
@app.get("/api/db-test")
def db_test(db: Session = Depends(get_db)):
    """Test database connection"""

    # Execute a simple SQL query to verify DB connection
    # SELECT 1 is commonly used for quick connection checks
    result = db.execute(text("SELECT 1"))

    # Return the result to confirm database responded correctly
    return {"db": result.scalar()}


# Include all API routers from the app.api module
# This keeps the main file clean and organizes endpoints modularly
app.include_router(api_router)

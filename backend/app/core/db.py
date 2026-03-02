import os  # Used to access environment variables
from dotenv import load_dotenv  # Loads variables from .env file
from sqlalchemy import create_engine  # Creates the database engine/connection
from sqlalchemy.orm import sessionmaker, declarative_base  # For DB sessions and model base class


# Load environment variables from the .env file
# This allows us to access DATABASE_URL securely
load_dotenv()


# Get the database connection string from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, stop the application immediately
# This prevents the app from running without a database connection
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Check your .env file.")


# Create the SQLAlchemy engine using the connection string
# pool_pre_ping=True helps prevent stale database connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# Create a configured session class for interacting with the database
# autocommit=False ensures we manually commit changes
# autoflush=False prevents automatic writes before we explicitly commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class that all database models will inherit from
# This is required for SQLAlchemy ORM models
Base = declarative_base()


# Dependency function used by FastAPI routes
# Provides a database session per request
def get_db():
    db = SessionLocal()  # Create a new database session
    try:
        # Yield the session so routes can use it
        yield db
    finally:
        # Always close the session after request finishes
        # This prevents connection leaks
        db.close()

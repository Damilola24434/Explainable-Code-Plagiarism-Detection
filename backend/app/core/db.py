# About db.py file:
# This fileset up the daabase connection for the whole f the backend for this partcular program
# It create databse engine and sessions.It gives other files a way to talk to the databse
# It also loads the database url, so tha app can connect to Neoo or SQlite
# ALmost all backend files relies/ depens on this file.
# without this file collections, datasets, files, runs apis will not work because they all need to connect to the database to store and retrieve data.


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
# this reads the shared /neon database url from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"  # fallback for testing

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

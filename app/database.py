from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # Reads your .env file

DATABASE_URL = os.getenv("DATABASE_URL")

# The engine is the actual connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal is used to talk to the DB (one per request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all your models will inherit from
Base = declarative_base()

# This function gives each request its own DB session
# FastAPI will call this automatically via Depends()
def get_db():
    db = SessionLocal()
    try:
        yield db       # hands db to your route function
    finally:
        db.close()     # always closes, even if an error occurs
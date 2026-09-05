"""
Sets up the SQLAlchemy engine + session that every request will use
to talk to Postgres. get_db() is a FastAPI "dependency" - every
endpoint that needs the database will ask for it, and FastAPI will
automatically call this function, hand the session to the endpoint,
then close it afterwards.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

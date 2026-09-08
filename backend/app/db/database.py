from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from collections.abc import Generator

DATABASE_URL = (
    "postgresql+psycopg://"
    "smart_pantry:"
    "smart_pantry_password"
    "@localhost:5433/"
    "smart_pantry"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
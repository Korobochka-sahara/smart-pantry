import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is not set. Expected .env at: {ENV_FILE}"
    )

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
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
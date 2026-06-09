"""Database engine, session factory, and declarative base."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

_connect_args = (
    # check_same_thread=False: connections are used across the ASGI threadpool.
    # timeout=30: wait on SQLite's write lock instead of erroring under
    # concurrency (defense in depth alongside the audit chain's own lock).
    {"check_same_thread": False, "timeout": 30}
    if settings.DB_URL.startswith("sqlite")
    else {}
)
engine = create_engine(settings.DB_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

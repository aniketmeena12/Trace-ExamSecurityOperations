"""Database engine, session factory, and declarative base."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

_is_sqlite = settings.DB_URL.startswith("sqlite")
_connect_args = (
    # check_same_thread=False: connections are used across the ASGI threadpool.
    # timeout=30: wait on SQLite's write lock instead of erroring under
    # concurrency (defense in depth alongside the audit chain's own lock).
    {"check_same_thread": False, "timeout": 30}
    if _is_sqlite
    else {}
)
engine = create_engine(settings.DB_URL, connect_args=_connect_args, future=True)


if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        """Make SQLite tolerant of concurrent access.

        WAL lets readers proceed while a writer is active (so concurrent logins
        don't hit 'database is locked'); busy_timeout makes any remaining
        contention wait rather than error.
        """
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=30000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

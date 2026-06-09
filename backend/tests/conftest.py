"""Shared test fixtures.

Sets an isolated temp SQLite DB and a test secret BEFORE any Trace module is
imported, so the global engine binds to throwaway storage.
"""

import os
import tempfile

os.environ.setdefault("TRACE_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
os.environ.setdefault("TRACE_PBKDF2_ITERS", "1000")  # fast hashing for tests
_TMPDIR = tempfile.mkdtemp(prefix="trace-test-")
os.environ["TRACE_DB_URL"] = f"sqlite:///{_TMPDIR}/test.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    """Fresh schema + demo users per test (startup event re-bootstraps)."""
    from trace.db import Base, engine

    Base.metadata.drop_all(bind=engine)
    from trace.api.app import app

    with TestClient(app) as c:  # triggers startup -> create tables + demo users
        yield c


@pytest.fixture()
def db_session():
    from trace.bootstrap import bootstrap
    from trace.db import Base, SessionLocal, engine

    Base.metadata.drop_all(bind=engine)
    bootstrap()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}

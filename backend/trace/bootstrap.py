"""Minimal account bootstrap so the M2 API is usable out of the box.

This is the *small* fixture needed to exercise the API. The full demo fixture
(sample paper, ~20-candidate roster, one-command demo) lands in M6.
"""

from .db import Base, SessionLocal, engine
from .models import (
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_CUSTODIAN,
    ROLE_INVESTIGATOR,
    User,
)
from .security.passwords import hash_password

# (username, password, display_name, role, candidate_code, center_id)
DEMO_USERS = [
    ("admin", "admin123", "Exam Controller", ROLE_ADMIN, None, None),
    ("investigator", "invest123", "Forensic Investigator", ROLE_INVESTIGATOR, None, None),
    ("cust1", "custodian1", "Custodian — Registrar", ROLE_CUSTODIAN, None, None),
    ("cust2", "custodian2", "Custodian — Controller", ROLE_CUSTODIAN, None, None),
    ("cust3", "custodian3", "Custodian — Dean", ROLE_CUSTODIAN, None, None),
    ("cust4", "custodian4", "Custodian — Vigilance", ROLE_CUSTODIAN, None, None),
    ("cust5", "custodian5", "Custodian — Board Sec.", ROLE_CUSTODIAN, None, None),
    ("cand001", "candidate1", "Candidate 001", ROLE_CANDIDATE, "R-001", "DEL-01"),
    ("cand002", "candidate2", "Candidate 002", ROLE_CANDIDATE, "R-002", "DEL-01"),
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_demo_users(db) -> None:
    for username, password, display, role, code, center in DEMO_USERS:
        if db.query(User).filter_by(username=username).first():
            continue
        db.add(
            User(
                username=username,
                display_name=display,
                role=role,
                password_hash=hash_password(password),
                candidate_code=code,
                center_id=center,
            )
        )
    db.commit()


def bootstrap() -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_demo_users(db)
    finally:
        db.close()

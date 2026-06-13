"""Minimal account bootstrap so the M2 API is usable out of the box.

This is the *small* fixture needed to exercise the API. The full demo fixture
(sample paper, ~20-candidate roster, one-command demo) lands in M6.
"""

import json

from sqlalchemy import inspect, text

from .config import settings
from .crypto import aes_gcm
from .db import Base, SessionLocal, engine
from .models import (
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_CUSTODIAN,
    ROLE_INVESTIGATOR,
    Question,
    User,
)
from .security.passwords import hash_password
from .util import utcnow

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


# Demo question bank for the dynamic-assembly walkthrough (subject "MATH-DEMO").
# (section, topic, difficulty, prompt, options)
DEMO_QUESTIONS = [
    ("A", "algebra", "easy", "Solve for x: 2x + 6 = 14.",
     ["(a) 2", "(b) 4", "(c) 6", "(d) 8"]),
    ("A", "algebra", "easy", "Simplify: (3a + 2a) - a.",
     ["(a) 4a", "(b) 5a", "(c) 6a", "(d) a"]),
    ("A", "algebra", "easy", "If y = 3, evaluate 5y - 2.",
     ["(a) 11", "(b) 12", "(c) 13", "(d) 15"]),
    ("A", "algebra", "easy", "Factor: x^2 - 9.",
     ["(a) (x-3)(x-3)", "(b) (x+3)(x-3)", "(c) (x+9)(x-1)", "(d) (x-9)(x+1)"]),
    ("A", "algebra", "easy", "Solve: x/4 = 5.",
     ["(a) 9", "(b) 16", "(c) 20", "(d) 25"]),
    ("B", "geometry", "hard", "A circle has area 49π. Find its circumference.",
     ["(a) 7π", "(b) 14π", "(c) 21π", "(d) 49π"]),
    ("B", "geometry", "hard", "Interior angle sum of a regular heptagon?",
     ["(a) 720°", "(b) 900°", "(c) 1080°", "(d) 1260°"]),
    ("B", "geometry", "hard", "Distance between (1,2) and (4,6).",
     ["(a) 3", "(b) 4", "(c) 5", "(d) 7"]),
    ("B", "geometry", "hard", "Volume of a cone, r=3, h=4 (use π).",
     ["(a) 12π", "(b) 24π", "(c) 36π", "(d) 48π"]),
    ("B", "geometry", "hard", "A triangle has sides 9, 12, 15. It is:",
     ["(a) acute", "(b) right", "(c) obtuse", "(d) equilateral"]),
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_exam_columns()


def _migrate_exam_columns() -> None:
    """Add M5 columns to a pre-existing exams table (SQLite has no ALTER-if-missing).

    create_all() builds the new questions/candidate_papers tables but never alters
    an existing one, so a database created before M5 is missing the dynamic
    columns. This idempotent migration adds them in place, preserving demo data.
    """
    inspector = inspect(engine)
    if "exams" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("exams")}
    statements = []
    if "assembly_mode" not in cols:
        statements.append(
            "ALTER TABLE exams ADD COLUMN assembly_mode VARCHAR NOT NULL DEFAULT 'static'"
        )
    if "blueprint" not in cols:
        statements.append("ALTER TABLE exams ADD COLUMN blueprint TEXT")
    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))


def ensure_demo_questions(db) -> None:
    """Seed a small encrypted question bank if it is empty (idempotent)."""
    if db.query(Question).first() is not None:
        return
    for section, topic, difficulty, prompt, options in DEMO_QUESTIONS:
        body = aes_gcm.encrypt(
            _encode_demo_body(prompt, options), settings.question_bank_key()
        )
        db.add(
            Question(
                subject="MATH-DEMO",
                section=section,
                topic=topic,
                difficulty=difficulty,
                nonce=body.nonce,
                tag=body.tag,
                ciphertext=body.data,
                contributor="admin",
                active=1,
                created_at=utcnow(),
            )
        )
    db.commit()


def _encode_demo_body(prompt: str, options: list[str]) -> bytes:
    return json.dumps(
        {"prompt": prompt, "options": options, "answer": None},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
        ensure_demo_questions(db)
    finally:
        db.close()

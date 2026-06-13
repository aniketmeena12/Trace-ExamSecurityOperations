"""SQLAlchemy models for Trace.

Security-relevant invariants encoded here:
  * Exam stores only the ciphertext (nonce/tag/body) + metadata, never the AES key.
  * CustodianShare holds one Shamir share per custodian (escrowed for this
    single-node demo; see README trust model).
  * ShareSubmission records a custodian *authorizing* release during the unlock
    ceremony — the key is reconstructed only when k of these exist AND the
    server-enforced release time has passed.
  * AuditEvent is an append-only SHA-256 hash chain (see audit/chain.py).
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base

# Roles
ROLE_ADMIN = "admin"
ROLE_CUSTODIAN = "custodian"
ROLE_CANDIDATE = "candidate"
ROLE_INVESTIGATOR = "investigator"
ALL_ROLES = (ROLE_ADMIN, ROLE_CUSTODIAN, ROLE_CANDIDATE, ROLE_INVESTIGATOR)

# Exam status
STATUS_SEALED = "SEALED"
STATUS_UNLOCKED = "UNLOCKED"

# Paper assembly mode
ASSEMBLY_STATIC = "static"    # one fixed paper sealed in the vault (M2 default)
ASSEMBLY_DYNAMIC = "dynamic"  # paper assembled per-candidate from the question bank


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

    # candidate-specific (nullable for other roles)
    candidate_code = Column(String, nullable=True)  # e.g. roll number
    center_id = Column(String, nullable=True)


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    center_id = Column(String, nullable=False)

    release_time = Column(DateTime, nullable=False)  # naive UTC; the time gate
    threshold_k = Column(Integer, nullable=False)
    num_custodians_n = Column(Integer, nullable=False)

    # AES-256-GCM ciphertext of the paper. NO key is ever stored here.
    nonce = Column(LargeBinary, nullable=False)
    tag = Column(LargeBinary, nullable=False)
    ciphertext = Column(LargeBinary, nullable=False)
    aad = Column(String, nullable=False)

    status = Column(String, nullable=False, default=STATUS_SEALED)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    unlocked_at = Column(DateTime, nullable=True)

    # After a legitimate unlock, the paper's AES key is re-wrapped under the
    # server wrapping key so candidates can be served. Null until unlocked.
    released_key_wrapped = Column(LargeBinary, nullable=True)

    # Dynamic assembly (M5): when assembly_mode == "dynamic" the vault holds a
    # manifest (blueprint + question-pool ids) instead of a fixed paper, and each
    # candidate's paper is assembled on demand from the encrypted question bank.
    # blueprint is non-secret structure (sections + counts), kept out-of-vault for
    # the dashboard; it reveals how many questions, never which ones are selected.
    assembly_mode = Column(String, nullable=False, default=ASSEMBLY_STATIC)
    blueprint = Column(Text, nullable=True)  # canonical JSON, dynamic exams only

    shares = relationship("CustodianShare", cascade="all, delete-orphan")
    submissions = relationship("ShareSubmission", cascade="all, delete-orphan")


class CustodianShare(Base):
    """One custodian's Shamir share for one exam (x-coordinate + y bytes)."""

    __tablename__ = "custodian_shares"
    __table_args__ = (UniqueConstraint("exam_id", "custodian_id"),)

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    custodian_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(LargeBinary, nullable=False)


class ShareSubmission(Base):
    """A custodian authorizing release of their share during an unlock ceremony."""

    __tablename__ = "share_submissions"
    __table_args__ = (UniqueConstraint("exam_id", "custodian_id"),)

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    custodian_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, nullable=False)


class IssuedWatermark(Base):
    """Registry of every watermarked copy handed out: fingerprint -> source.

    Populated when a candidate fetches their watermarked paper image; queried by
    the investigator's trace endpoint to name the exact source of a leak.
    fingerprint is stored as a 16-hex-char string (64-bit) to avoid SQLite's
    signed-integer range limits.
    """

    __tablename__ = "issued_watermarks"
    __table_args__ = (UniqueConstraint("exam_id", "username"),)

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    username = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False, index=True)
    center_id = Column(String, nullable=False)
    candidate_code = Column(String, nullable=False)
    issued_at = Column(DateTime, nullable=False)


class Question(Base):
    """One encrypted question in the dynamic bank (M5).

    Contributed by a setter/admin *before* any exam is sealed. The body (prompt +
    options + answer) is AES-256-GCM ciphertext at rest, encrypted under the
    server question-bank key — a raw DB dump cannot read it. The metadata columns
    (subject/section/topic/difficulty) are plaintext: they drive blueprint
    selection but reveal nothing about which questions land on a given paper.
    """

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False, index=True)
    section = Column(String, nullable=False, default="")
    topic = Column(String, nullable=False, default="", index=True)
    difficulty = Column(String, nullable=False, default="medium", index=True)

    # AES-256-GCM of the question body JSON. NO plaintext body is ever stored.
    nonce = Column(LargeBinary, nullable=False)
    tag = Column(LargeBinary, nullable=False)
    ciphertext = Column(LargeBinary, nullable=False)

    contributor = Column(String, nullable=False)
    active = Column(Integer, nullable=False, default=1)  # 1 = in pool, 0 = retired
    created_at = Column(DateTime, nullable=False)


class CandidatePaper(Base):
    """Which questions were assembled for one candidate on one exam.

    Records only the *selection* (a list of question ids) — never the assembled
    plaintext paper, which exists transiently in memory during serving and is
    never persisted. Lets the investigator reproduce/inspect a candidate's exact
    variant and cross-reference a leak trace.
    """

    __tablename__ = "candidate_papers"
    __table_args__ = (UniqueConstraint("exam_id", "username"),)

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    username = Column(String, nullable=False)
    candidate_code = Column(String, nullable=False)
    selected_question_ids = Column(Text, nullable=False)  # canonical JSON list
    assembled_at = Column(DateTime, nullable=False)


class AuditEvent(Base):
    """Append-only, SHA-256 hash-chained audit record.

    hash = SHA256(id | timestamp | actor | action | target | details | prev_hash)
    Altering any field of any row breaks `hash` and the linkage to the next row.
    """

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String, nullable=False)  # ISO-8601 string, hashed verbatim
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False, default="")
    details = Column(Text, nullable=False, default="{}")  # canonical JSON
    prev_hash = Column(String, nullable=False)
    hash = Column(String, nullable=False)

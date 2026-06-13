"""Persisted forensic leak cases.

Every image trace and text match creates a LeakCase so an investigator can later
reopen a detection (via the case_id stamped on its audit event) and see the full
candidate profiles implicated — without re-supplying the leaked artifact.

enrich_candidate() is the single place that joins the identity details together:
the candidate's roll number and name (User), their exam centre, the exact copy
they were issued (IssuedWatermark), and the questions on their paper
(CandidatePaper).
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..models import CandidatePaper, IssuedWatermark, LeakCase, User
from ..util import utcnow

_CANON = {"sort_keys": True, "separators": (",", ":")}


def enrich_candidate(
    db: Session, *, username: str, exam_id: int | None = None, **extra
) -> dict:
    """Full identity profile for one implicated candidate."""
    user = db.query(User).filter_by(username=username).first()
    profile: dict = {
        "username": username,
        "candidate_code": user.candidate_code if user else None,
        "display_name": user.display_name if user else None,
        "center_id": user.center_id if user else None,
        "exam_id": exam_id,
    }
    if exam_id is not None:
        wm = (
            db.query(IssuedWatermark)
            .filter_by(exam_id=exam_id, username=username)
            .first()
        )
        if wm:
            profile["fingerprint"] = wm.fingerprint
            profile["issued_at"] = wm.issued_at.isoformat()
        cp = (
            db.query(CandidatePaper)
            .filter_by(exam_id=exam_id, username=username)
            .first()
        )
        if cp:
            profile["question_ids"] = json.loads(cp.selected_question_ids)
            profile["assembled_at"] = cp.assembled_at.isoformat()
    profile.update(extra)  # match-specific fields: has_all, matched_of_leak, confidence…
    return profile


def create_case(
    db: Session,
    *,
    kind: str,
    created_by: str,
    summary: str,
    query_preview: str,
    payload: dict,
    top_candidate: str | None,
) -> LeakCase:
    """Persist a detection result. Caller commits."""
    case = LeakCase(
        kind=kind,
        created_at=utcnow(),
        created_by=created_by,
        summary=summary,
        top_candidate=top_candidate,
        query_preview=query_preview[:280],
        payload=json.dumps(payload, **_CANON),
    )
    db.add(case)
    db.flush()  # assign id
    return case


def list_cases(db: Session, limit: int = 100) -> list[LeakCase]:
    return db.query(LeakCase).order_by(LeakCase.id.desc()).limit(limit).all()


def get_case(db: Session, case_id: int) -> LeakCase | None:
    return db.query(LeakCase).filter_by(id=case_id).first()

"""Dynamic per-candidate paper assembly from an encrypted question bank (M5).

Why this strengthens leak resistance
------------------------------------
A static exam is one secret blob: leak it once and the whole exam is compromised,
for everyone. With dynamic assembly there is no single paper. A large bank of
*individually encrypted* questions is maintained ahead of time; at serve time a
blueprint (sections + counts) and a per-candidate seed select a unique subset and
assemble that candidate's paper on demand. Two properties follow:

  * **Unpredictable** — the selection seed is derived from the exam key, which only
    exists after the Shamir quorum *and* the time gate open. So no setter, admin,
    or DB reader can know which questions reach which candidate before release.
  * **Low blast radius + traceable** — every candidate's paper is content-distinct,
    so a leaked copy exposes only one variant and (with the DCT watermark) names
    its owner. The full assembled paper is never persisted in plaintext.

This module never stores a plaintext paper: question bodies are AES-256-GCM
ciphertext at rest, and the assembled text lives only transiently in memory while
a single request is served.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import random

from sqlalchemy.orm import Session

from .. import audit
from ..config import settings
from ..crypto import aes_gcm
from ..models import STATUS_UNLOCKED, CandidatePaper, Exam, Question
from ..security import keywrap
from ..util import utcnow
from .exams import UnlockError

_CANON = {"sort_keys": True, "separators": (",", ":")}


# ---- question bank -----------------------------------------------------------
def _encode_body(prompt: str, options: list[str], answer: str | None) -> bytes:
    return json.dumps(
        {"prompt": prompt, "options": list(options), "answer": answer}, **_CANON
    ).encode("utf-8")


def add_question(
    db: Session,
    *,
    contributor: str,
    subject: str,
    section: str = "",
    topic: str = "",
    difficulty: str = "medium",
    prompt: str,
    options: list[str] | None = None,
    answer: str | None = None,
) -> Question:
    """Encrypt a question body and add it to the bank. Body is never stored raw."""
    body = _encode_body(prompt, options or [], answer)
    ct = aes_gcm.encrypt(body, settings.question_bank_key())
    q = Question(
        subject=subject,
        section=section,
        topic=topic,
        difficulty=difficulty,
        nonce=ct.nonce,
        tag=ct.tag,
        ciphertext=ct.data,
        contributor=contributor,
        active=1,
        created_at=utcnow(),
    )
    db.add(q)
    db.flush()  # assign id
    audit.record(
        db,
        actor=contributor,
        action=audit.chain.QUESTION_ADDED,
        target=f"question:{q.id}",
        details={"subject": subject, "topic": topic, "difficulty": difficulty},
    )
    db.commit()
    db.refresh(q)
    return q


def decrypt_question_body(q: Question) -> dict:
    """Decrypt one question body to {prompt, options, answer}."""
    raw = aes_gcm.decrypt(
        aes_gcm.Ciphertext(q.nonce, q.tag, q.ciphertext), settings.question_bank_key()
    )
    return json.loads(raw.decode("utf-8"))


def _matching_pool(db: Session, subject: str, section: dict) -> list[int]:
    """Sorted ids of active questions a blueprint section may draw from."""
    query = db.query(Question.id).filter(Question.subject == subject, Question.active == 1)
    if section.get("topic"):
        query = query.filter(Question.topic == section["topic"])
    if section.get("difficulty"):
        query = query.filter(Question.difficulty == section["difficulty"])
    return sorted(row[0] for row in query.all())


# ---- blueprint ---------------------------------------------------------------
def validate_blueprint(db: Session, subject: str, blueprint: dict) -> list[list[int]]:
    """Check the bank can satisfy every section; return per-section candidate pools.

    Returns a list aligned to the blueprint's sections, each a sorted list of the
    question ids that section may draw from. Raises ValueError (mapped to HTTP 400
    by the router) on a malformed blueprint or an under-stocked section, so a
    dynamic exam can never be sealed in a state that would fail at serve time.
    """
    sections = blueprint.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("blueprint must have a non-empty 'sections' list")

    section_pools: list[list[int]] = []
    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"section {i} must be an object")
        count = section.get("count")
        if not isinstance(count, int) or count < 1:
            raise ValueError(f"section {i} needs an integer 'count' >= 1")
        ids = _matching_pool(db, subject, section)
        if len(ids) < count:
            label = section.get("name", i)
            raise ValueError(
                f"section '{label}' needs {count} questions but the bank has "
                f"only {len(ids)} matching (subject={subject}, "
                f"topic={section.get('topic')}, difficulty={section.get('difficulty')})"
            )
        section_pools.append(ids)
    return section_pools


def pool_size(section_pools: list[list[int]]) -> int:
    """Distinct questions across all section pools (for the dashboard)."""
    return len({qid for pool in section_pools for qid in pool})


def manifest_for(blueprint: dict, section_pools: list[list[int]]) -> str:
    """Canonical JSON sealed inside the vault for a dynamic exam.

    Freezes the exact per-section candidate pools at seal time and encrypts them
    under the exam key. This ties the gated key to the blueprint AND makes each
    candidate's selection immutable: retiring or editing a bank question later
    cannot change (or break) the papers of an already-sealed exam.
    """
    return json.dumps(
        {"mode": "dynamic", "blueprint": blueprint, "pools": [list(p) for p in section_pools]},
        **_CANON,
    )


# ---- per-candidate selection -------------------------------------------------
def _section_seed(exam_key: bytes, exam_id: int, candidate_code: str, name: str) -> int:
    """Deterministic, per-(candidate, section) seed bound to the exam key.

    Keyed by the exam key (HMAC), so the selection is uncomputable until the key
    is reconstructed at release — and unique per candidate and per section.
    """
    msg = f"{exam_id}:{candidate_code}:{name}".encode("utf-8")
    return int.from_bytes(hmac.new(exam_key, msg, hashlib.sha256).digest(), "big")


def _open_manifest(exam: Exam) -> tuple[bytes, dict]:
    """Unwrap the exam key and decrypt the sealed manifest (post-release only)."""
    if exam.status != STATUS_UNLOCKED or exam.released_key_wrapped is None:
        raise UnlockError("SEALED", "This paper has not been released yet.")
    exam_key = keywrap.unwrap_key(exam.released_key_wrapped)
    raw = aes_gcm.decrypt(
        aes_gcm.Ciphertext(exam.nonce, exam.tag, exam.ciphertext),
        exam_key,
        aad=exam.aad.encode(),
    )
    return exam_key, json.loads(raw.decode("utf-8"))


def _select(exam: Exam, exam_key: bytes, manifest: dict, candidate_code: str) -> tuple[dict, list[int]]:
    """Return (blueprint, ordered ids) selected from the frozen per-section pools."""
    blueprint = manifest.get("blueprint") or {"sections": []}
    pools = manifest.get("pools", [])
    chosen: list[int] = []
    for i, section in enumerate(blueprint.get("sections", [])):
        name = str(section.get("name", i))
        pool = pools[i] if i < len(pools) else []
        rng = random.Random(_section_seed(exam_key, exam.id, candidate_code, name))
        chosen.extend(rng.sample(pool, section["count"]))
    return blueprint, chosen


def select_question_ids(db: Session, exam: Exam, candidate_code: str) -> list[int]:
    """The ordered question ids for one candidate. Requires a released exam key."""
    exam_key, manifest = _open_manifest(exam)
    _, ids = _select(exam, exam_key, manifest, candidate_code)
    return ids


# ---- assembly ----------------------------------------------------------------
def _format_paper(exam: Exam, blueprint: dict, sections_q: list[tuple[str, list[dict]]]) -> str:
    lines = [exam.name, f"Subject: {exam.subject}    Centre: {exam.center_id}", ""]
    n = 0
    for sec_name, questions in sections_q:
        lines.append(f"— Section {sec_name} —")
        for body in questions:
            n += 1
            lines.append(f"{n}. {body['prompt']}")
            for opt in body.get("options", []):
                lines.append(f"    {opt}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def assemble_paper_text(
    db: Session, exam: Exam, *, username: str, candidate_code: str, record: bool = True
) -> tuple[str, list[int]]:
    """Assemble one candidate's paper in memory (post-release only).

    Selects per the blueprint, decrypts only the chosen questions, formats the
    paper (prompts + options, never the answer key), and records the *selection*
    (ids only) for audit/trace. The assembled text is returned, not stored.
    """
    exam_key, manifest = _open_manifest(exam)
    blueprint, ids = _select(exam, exam_key, manifest, candidate_code)
    by_id = {q.id: q for q in db.query(Question).filter(Question.id.in_(ids)).all()}

    # Group the chosen ids back under their sections, in blueprint order.
    sections_q: list[tuple[str, list[dict]]] = []
    cursor = 0
    for i, section in enumerate(blueprint.get("sections", [])):
        name = str(section.get("name", i))
        count = section["count"]
        sec_ids = ids[cursor : cursor + count]
        cursor += count
        sections_q.append((name, [decrypt_question_body(by_id[qid]) for qid in sec_ids]))

    text = _format_paper(exam, blueprint, sections_q)

    if record:
        _record_selection(db, exam, username, candidate_code, ids)
    return text, ids


def _record_selection(
    db: Session, exam: Exam, username: str, candidate_code: str, ids: list[int]
) -> None:
    row = (
        db.query(CandidatePaper)
        .filter_by(exam_id=exam.id, username=username)
        .first()
    )
    payload = json.dumps(ids, separators=(",", ":"))
    if row is None:
        db.add(
            CandidatePaper(
                exam_id=exam.id,
                username=username,
                candidate_code=candidate_code,
                selected_question_ids=payload,
                assembled_at=utcnow(),
            )
        )
        audit.record(
            db,
            actor=username,
            action=audit.chain.PAPER_ASSEMBLED,
            target=f"exam:{exam.id}",
            details={"candidate_code": candidate_code, "question_count": len(ids)},
        )
        db.commit()
    # Deterministic selection: an existing row already matches; no rewrite needed.

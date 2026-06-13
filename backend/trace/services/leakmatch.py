"""Leak-match detector (Milestone B).

When a suspected leak surfaces (a question circulating on chat/social), an
investigator pastes the text here. We match it against the encrypted question
bank and then narrow the source using the per-candidate selection records:

  * **What leaked** — each bank question whose text is largely contained in the
    pasted leak is flagged (containment score, robust to extra surrounding text).
  * **Who could have leaked it** — every candidate whose assembled paper
    contained *all* the matched questions. One leaked question rarely narrows the
    field; a leak containing several questions intersects to a tiny suspect set,
    because dynamic assembly gave each candidate a different combination.

Combined with the DCT watermark trace (which needs an image), this works on
text-only leaks where no image is available.
"""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from .. import audit
from ..models import CandidatePaper, IssuedWatermark, Question
from .assembly import decrypt_question_body

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    """Normalise to a set of lowercase alphanumeric tokens."""
    return set(_TOKEN.findall(text.lower()))


def _containment(needle: set[str], haystack: set[str]) -> float:
    """Fraction of the question's tokens present in the leaked text (0..1)."""
    if not needle:
        return 0.0
    return len(needle & haystack) / len(needle)


def match_leak(
    db: Session, text: str, *, actor: str, threshold: float = 0.75, top_k: int = 10
) -> dict:
    """Identify which bank questions a leaked text contains, and likely sources.

    Matching is on the question *prompt* (the discriminative stem). Option labels
    like "(a)/(b)" are shared by every question and would inflate the score, so
    they are deliberately excluded — a leaked question is recognised by its stem.
    """
    leak_tokens = _tokens(text)

    matched: list[dict] = []
    for q in db.query(Question).all():
        body = decrypt_question_body(q)
        score = _containment(_tokens(body.get("prompt", "")), leak_tokens)
        if score >= threshold:
            matched.append(
                {
                    "question_id": q.id,
                    "subject": q.subject,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "containment": round(score, 4),
                    "prompt_preview": body.get("prompt", "")[:120],
                }
            )
    matched.sort(key=lambda m: m["containment"], reverse=True)
    matched = matched[:top_k]
    matched_ids = {m["question_id"] for m in matched}

    suspects = _narrow_candidates(db, matched_ids) if matched_ids else []

    audit.record(
        db,
        actor=actor,
        action=audit.chain.LEAK_MATCHED,
        details={
            "matched_questions": len(matched),
            "best_containment": matched[0]["containment"] if matched else 0.0,
            "suspects": len(suspects),
        },
    )
    db.commit()

    return {
        "leaked_chars": len(text),
        "matched_questions": matched,
        "suspects": suspects,
        "note": _summarise(matched, suspects),
    }


def _narrow_candidates(db: Session, matched_ids: set[int]) -> list[dict]:
    """Candidates whose assembled paper contained every matched question.

    Ranked by overlap; an exact-superset candidate is a prime suspect. We attach
    the issued-watermark fingerprint so a follow-up image trace can confirm.
    """
    out: list[dict] = []
    for cp in db.query(CandidatePaper).all():
        selected = set(json.loads(cp.selected_question_ids))
        overlap = matched_ids & selected
        if not overlap:
            continue
        wm = (
            db.query(IssuedWatermark)
            .filter_by(exam_id=cp.exam_id, username=cp.username)
            .first()
        )
        out.append(
            {
                "username": cp.username,
                "candidate_code": cp.candidate_code,
                "exam_id": cp.exam_id,
                "matched_of_leak": len(overlap),
                "has_all": overlap == matched_ids,
                "fingerprint": wm.fingerprint if wm else None,
            }
        )
    # Prime suspects (contain every leaked question) first, then by overlap.
    out.sort(key=lambda c: (c["has_all"], c["matched_of_leak"]), reverse=True)
    return out


def _summarise(matched: list[dict], suspects: list[dict]) -> str:
    if not matched:
        return "No bank question matched this text — leak not from this bank, or paraphrased."
    prime = [s for s in suspects if s["has_all"]]
    q = f"{len(matched)} question(s) matched"
    if not suspects:
        return f"{q}, but no issued paper contained them (not yet served?)."
    if len(prime) == 1:
        s = prime[0]
        return f"{q}. Source narrowed to a single candidate: {s['candidate_code']} ({s['username']})."
    if prime:
        return f"{q}. Narrowed to {len(prime)} candidates who received all of them."
    # No exact-superset candidate: name the strongest lead by overlap.
    top = suspects[0]
    return (
        f"{q}. Strongest lead: {top['candidate_code']} ({top['username']}) — "
        f"{top['matched_of_leak']} of {len(matched)} matched questions."
    )

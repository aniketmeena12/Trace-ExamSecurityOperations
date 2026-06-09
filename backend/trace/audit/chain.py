"""Append-only, tamper-evident audit log built as a SHA-256 hash chain.

Each event's hash binds its own contents to the previous event's hash:

    hash_i = SHA256( id | timestamp | actor | action | target | details | hash_{i-1} )

So editing any field of any past event changes that event's hash, which no
longer matches the `prev_hash` stored in the next event — the break is detectable
and its location is pinpointed by verify_chain(). The first event chains from a
fixed GENESIS hash.
"""

import hashlib
import json

from ..models import AuditEvent
from ..util import utcnow

GENESIS_HASH = "0" * 64

# Canonical action vocabulary (kept here so endpoints stay consistent).
LOGIN = "LOGIN"
EXAM_SEALED = "EXAM_SEALED"
SHARE_SUBMITTED = "SHARE_SUBMITTED"
UNLOCK_DENIED = "UNLOCK_DENIED"
PAPER_UNLOCKED = "PAPER_UNLOCKED"
PAPER_ACCESSED = "PAPER_ACCESSED"
AUDIT_VERIFIED = "AUDIT_VERIFIED"


def _digest(seq, timestamp, actor, action, target, details_json, prev_hash) -> str:
    message = "|".join(
        [str(seq), timestamp, actor, action, target, details_json, prev_hash]
    )
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _canonical(details) -> str:
    return json.dumps(details or {}, sort_keys=True, separators=(",", ":"))


def record(db, actor: str, action: str, target: str = "", details: dict | None = None):
    """Append an event to the chain and return it.

    Caller is responsible for committing the surrounding transaction.
    """
    details_json = _canonical(details)
    last = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    prev_hash = last.hash if last else GENESIS_HASH
    timestamp = utcnow().isoformat()

    event = AuditEvent(
        timestamp=timestamp,
        actor=actor,
        action=action,
        target=target,
        details=details_json,
        prev_hash=prev_hash,
        hash="",  # filled after we know the autoincrement id
    )
    db.add(event)
    db.flush()  # assigns event.id
    event.hash = _digest(
        event.id, timestamp, actor, action, target, details_json, prev_hash
    )
    db.flush()
    return event


def verify_chain(db) -> dict:
    """Recompute the whole chain and report integrity.

    Returns {ok, count, broken: [ids], first_broken}. An event id appears in
    `broken` if its stored hash doesn't match a recomputation of its own fields,
    or if its prev_hash doesn't match the actual previous event's hash.
    """
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    prev_hash = GENESIS_HASH
    broken = []
    for ev in events:
        expected = _digest(
            ev.id, ev.timestamp, ev.actor, ev.action, ev.target, ev.details, ev.prev_hash
        )
        if ev.hash != expected or ev.prev_hash != prev_hash:
            broken.append(ev.id)
        prev_hash = ev.hash
    return {
        "ok": len(broken) == 0,
        "count": len(events),
        "broken": broken,
        "first_broken": broken[0] if broken else None,
    }

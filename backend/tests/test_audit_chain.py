"""Unit tests for the SHA-256 hash-chained audit log."""

from trace import audit
from trace.models import AuditEvent


def test_chain_links_and_verifies(db_session):
    db = db_session
    audit.record(db, actor="admin", action="A", target="x:1", details={"k": 1})
    audit.record(db, actor="cust1", action="B", target="x:1")
    audit.record(db, actor="cust2", action="C")
    db.commit()

    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    assert len(events) == 3
    # First chains from genesis; each subsequent prev_hash == previous hash.
    assert events[0].prev_hash == audit.GENESIS_HASH
    assert events[1].prev_hash == events[0].hash
    assert events[2].prev_hash == events[1].hash

    result = audit.verify_chain(db)
    assert result["ok"] is True
    assert result["count"] == 3
    assert result["broken"] == []


def test_tampering_with_a_field_breaks_the_chain(db_session):
    db = db_session
    audit.record(db, actor="admin", action="EXAM_SEALED", target="exam:1")
    audit.record(db, actor="cust1", action="SHARE_SUBMITTED", target="exam:1")
    audit.record(db, actor="cust2", action="SHARE_SUBMITTED", target="exam:1")
    db.commit()

    # An attacker edits the actor of event #2 directly in the database.
    victim = db.query(AuditEvent).filter_by(id=2).first()
    victim.actor = "mallory"
    db.commit()

    result = audit.verify_chain(db)
    assert result["ok"] is False
    # Event 2's own hash no longer matches; event 3's prev_hash mismatch may
    # also flag — at minimum the tampered event is detected.
    assert 2 in result["broken"]
    assert result["first_broken"] == 2


def test_tampering_with_stored_hash_is_detected(db_session):
    db = db_session
    audit.record(db, actor="admin", action="LOGIN")
    audit.record(db, actor="admin", action="EXAM_SEALED", target="exam:1")
    db.commit()

    victim = db.query(AuditEvent).filter_by(id=1).first()
    victim.hash = "f" * 64
    db.commit()

    result = audit.verify_chain(db)
    assert result["ok"] is False
    assert 1 in result["broken"]

"""Audit-log endpoints (investigator / admin)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import audit
from ...db import get_db
from ...models import ROLE_ADMIN, ROLE_INVESTIGATOR, AuditEvent, User
from ...schemas import AuditEventOut, ChainVerifyOut
from ...security.deps import require_role

router = APIRouter(prefix="/audit", tags=["audit"])

_VIEWERS = require_role(ROLE_INVESTIGATOR, ROLE_ADMIN)


@router.get("", response_model=list[AuditEventOut])
def list_events(
    limit: int = 200,
    db: Session = Depends(get_db),
    user: User = Depends(_VIEWERS),
):
    # Return the most RECENT `limit` events (so fresh detections stay visible as
    # the ledger grows), in ascending order for the dashboard's chronological view.
    rows = (
        db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all()
    )
    return list(reversed(rows))


@router.get("/verify", response_model=ChainVerifyOut)
def verify(db: Session = Depends(get_db), user: User = Depends(_VIEWERS)):
    """Recompute the SHA-256 hash chain and report whether it is intact."""
    result = audit.verify_chain(db)
    # Record the verification itself (chains on top of what was just verified).
    audit.record(
        db,
        actor=user.username,
        action=audit.chain.AUDIT_VERIFIED,
        details={"ok": result["ok"], "count": result["count"]},
    )
    db.commit()
    return result

"""Exam lifecycle: seal -> custodian submissions -> time-gated unlock -> serve.

This module is where the three M2 guarantees meet:
  * the AES key is split with Shamir at seal time and never stored whole,
  * unlock requires k distinct custodian submissions AND now >= release_time,
  * every state transition is written to the hash-chained audit log.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from .. import audit
from ..crypto import aes_gcm, shamir
from ..models import (
    ASSEMBLY_STATIC,
    STATUS_SEALED,
    STATUS_UNLOCKED,
    CustodianShare,
    Exam,
    ShareSubmission,
    User,
)
from ..security import keywrap
from ..util import utcnow


class UnlockError(Exception):
    """Raised when an unlock is not (yet) permitted; `reason` is machine-readable."""

    def __init__(self, reason: str, message: str, **extra):
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.extra = extra


def seal_exam(
    db: Session,
    admin: User,
    *,
    name: str,
    subject: str,
    center_id: str,
    paper_text: str,
    release_time: datetime,
    threshold_k: int,
    custodians: list[User],
    assembly_mode: str = ASSEMBLY_STATIC,
    blueprint: str | None = None,
) -> Exam:
    """Encrypt the paper, split its key across custodians, and persist (SEALED).

    For a static exam, `paper_text` is the whole paper. For a dynamic exam it is
    the assembly manifest (blueprint + pool ids); the per-candidate papers are
    assembled later from the encrypted question bank. Either way a single AES key
    is generated, Shamir-split, and never stored whole.
    """
    n = len(custodians)
    if not (1 <= threshold_k <= n <= 255):
        raise ValueError("require 1 <= threshold_k <= number_of_custodians <= 255")

    key = aes_gcm.generate_key()
    aad = f"center={center_id};exam={name}"
    ct = aes_gcm.encrypt(paper_text.encode("utf-8"), key, aad=aad.encode())

    exam = Exam(
        name=name,
        subject=subject,
        center_id=center_id,
        release_time=release_time,
        threshold_k=threshold_k,
        num_custodians_n=n,
        nonce=ct.nonce,
        tag=ct.tag,
        ciphertext=ct.data,
        aad=aad,
        status=STATUS_SEALED,
        created_by=admin.id,
        created_at=utcnow(),
        assembly_mode=assembly_mode,
        blueprint=blueprint,
    )
    db.add(exam)
    db.flush()  # assign exam.id

    shares = shamir.split(key, n=n, k=threshold_k)
    for share, custodian in zip(shares, custodians):
        db.add(
            CustodianShare(
                exam_id=exam.id,
                custodian_id=custodian.id,
                x=share.x,
                y=share.y,
            )
        )

    # The plaintext key goes out of scope here and is never stored.
    audit.record(
        db,
        actor=admin.username,
        action=audit.chain.EXAM_SEALED,
        target=f"exam:{exam.id}",
        details={
            "name": name,
            "subject": subject,
            "center_id": center_id,
            "threshold": f"{threshold_k}-of-{n}",
            "release_time": release_time.isoformat(),
            "assembly_mode": assembly_mode,
        },
    )
    db.commit()
    db.refresh(exam)
    return exam


def submit_share(db: Session, exam: Exam, custodian: User) -> dict:
    """Record a custodian authorizing release, then attempt unlock.

    Returns the current unlock status dict. Idempotent per custodian.
    """
    existing = (
        db.query(ShareSubmission)
        .filter_by(exam_id=exam.id, custodian_id=custodian.id)
        .first()
    )
    if existing is None:
        # The custodian must actually hold a share for this exam.
        holds = (
            db.query(CustodianShare)
            .filter_by(exam_id=exam.id, custodian_id=custodian.id)
            .first()
        )
        if holds is None:
            raise UnlockError(
                "NOT_A_CUSTODIAN",
                "You are not a custodian for this exam.",
            )
        db.add(
            ShareSubmission(
                exam_id=exam.id, custodian_id=custodian.id, submitted_at=utcnow()
            )
        )
        audit.record(
            db,
            actor=custodian.username,
            action=audit.chain.SHARE_SUBMITTED,
            target=f"exam:{exam.id}",
            details={"custodian": custodian.username},
        )
        db.flush()

    status = _attempt_unlock(db, exam, actor=custodian.username)
    db.commit()
    return status


def unlock_status(db: Session, exam: Exam) -> dict:
    """Read-only snapshot of unlock progress (no state change)."""
    submitted = (
        db.query(ShareSubmission).filter_by(exam_id=exam.id).count()
    )
    now = utcnow()
    seconds_remaining = max(0.0, (exam.release_time - now).total_seconds())
    return {
        "exam_id": exam.id,
        "status": exam.status,
        "threshold_k": exam.threshold_k,
        "num_custodians_n": exam.num_custodians_n,
        "shares_submitted": submitted,
        "shares_needed": exam.threshold_k,
        "time_locked": now < exam.release_time,
        "release_time": exam.release_time.isoformat(),
        "seconds_remaining": seconds_remaining,
        "unlocked_at": exam.unlocked_at.isoformat() if exam.unlocked_at else None,
    }


def _attempt_unlock(db: Session, exam: Exam, actor: str) -> dict:
    """Reconstruct + decrypt iff enough shares AND the time gate has opened.

    Writes the appropriate audit event. Does not commit (caller commits).
    """
    if exam.status == STATUS_UNLOCKED:
        return unlock_status(db, exam)

    submissions = db.query(ShareSubmission).filter_by(exam_id=exam.id).all()
    have = len(submissions)

    # Guard 1: threshold of distinct custodians.
    if have < exam.threshold_k:
        return unlock_status(db, exam)

    # Guard 2: the server-enforced time gate. This is unconditional — even with
    # every valid share present, the vault stays sealed until release_time.
    now = utcnow()
    if now < exam.release_time:
        audit.record(
            db,
            actor=actor,
            action=audit.chain.UNLOCK_DENIED,
            target=f"exam:{exam.id}",
            details={
                "reason": "TIME_LOCKED",
                "shares_present": have,
                "seconds_remaining": round((exam.release_time - now).total_seconds(), 2),
            },
        )
        db.flush()
        return unlock_status(db, exam)

    # Both guards passed: reconstruct the key from the actually-submitted shares.
    shares = []
    for sub in submissions:
        cs = (
            db.query(CustodianShare)
            .filter_by(exam_id=exam.id, custodian_id=sub.custodian_id)
            .first()
        )
        shares.append(shamir.Share(cs.x, cs.y))

    key = shamir.combine(shares)
    # Decrypt-and-verify: proves the reconstruction is correct (GCM auth tag).
    aes_gcm.decrypt(
        aes_gcm.Ciphertext(exam.nonce, exam.tag, exam.ciphertext),
        key,
        aad=exam.aad.encode(),
    )

    # Re-wrap the key under the server key so we can serve candidates post-release.
    exam.released_key_wrapped = keywrap.wrap_key(key)
    exam.status = STATUS_UNLOCKED
    exam.unlocked_at = now
    audit.record(
        db,
        actor=actor,
        action=audit.chain.PAPER_UNLOCKED,
        target=f"exam:{exam.id}",
        details={"shares_used": have, "threshold": exam.threshold_k},
    )
    db.flush()
    return unlock_status(db, exam)


def decrypt_paper_text(exam: Exam) -> str:
    """Decrypt the paper to text (post-release only). No audit side effect.

    Shared by the plaintext endpoint and the per-candidate watermark renderer.
    """
    if exam.status != STATUS_UNLOCKED or exam.released_key_wrapped is None:
        raise UnlockError("SEALED", "This paper has not been released yet.")
    key = keywrap.unwrap_key(exam.released_key_wrapped)
    plaintext = aes_gcm.decrypt(
        aes_gcm.Ciphertext(exam.nonce, exam.tag, exam.ciphertext),
        key,
        aad=exam.aad.encode(),
    )
    return plaintext.decode("utf-8")


def get_paper_plaintext(db: Session, exam: Exam, requester: User) -> str:
    """Return the decrypted paper text (post-release only). Audited as access."""
    text = decrypt_paper_text(exam)
    audit.record(
        db,
        actor=requester.username,
        action=audit.chain.PAPER_ACCESSED,
        target=f"exam:{exam.id}",
        details={
            "role": requester.role,
            "candidate_code": requester.candidate_code,
            "center_id": requester.center_id,
        },
    )
    db.commit()
    return text

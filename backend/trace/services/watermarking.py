"""Service layer connecting the M3 watermark engine to the API + registry.

issue_paper_image(): renders the released paper, embeds a per-candidate
fingerprint, records it in the issued-watermark registry, and returns PNG bytes.

trace_leak(): rebuilds the registry from the DB and identifies the source of an
uploaded (possibly recompressed) image.
"""

from __future__ import annotations

import io

from PIL import Image
from sqlalchemy.orm import Session

from .. import audit
from ..models import ASSEMBLY_DYNAMIC, Exam, IssuedWatermark
from ..util import utcnow
from ..watermark import (
    Registry,
    embed_fingerprint,
    make_fingerprint,
    render_paper,
    trace_image,
)
from . import assembly as assembly_service
from . import exams as exam_service


def _fingerprint_for(exam: Exam, candidate_code: str) -> int:
    # Exam-scoped so each issued copy is unique even for the same candidate.
    return make_fingerprint(exam.center_id, f"{exam.id}:{candidate_code}")


def issue_paper_image(
    db: Session, exam: Exam, *, username: str, candidate_code: str
) -> tuple[bytes, str]:
    """Render + watermark the paper for one candidate; register the fingerprint.

    Returns (png_bytes, fingerprint_hex). Raises UnlockError if not released.

    For a dynamic exam the text is assembled from the question bank for this exact
    candidate; for a static exam it is the single sealed paper. Both paths raise
    UnlockError while the vault is still sealed.
    """
    if exam.assembly_mode == ASSEMBLY_DYNAMIC:
        text, _ = assembly_service.assemble_paper_text(
            db, exam, username=username, candidate_code=candidate_code
        )
    else:
        text = exam_service.decrypt_paper_text(exam)  # raises if still sealed

    fp_int = _fingerprint_for(exam, candidate_code)
    fp_hex = f"{fp_int:016x}"

    image = render_paper(text)
    watermarked = embed_fingerprint(image, fp_int)

    row = (
        db.query(IssuedWatermark)
        .filter_by(exam_id=exam.id, username=username)
        .first()
    )
    if row is None:
        db.add(
            IssuedWatermark(
                exam_id=exam.id,
                username=username,
                fingerprint=fp_hex,
                center_id=exam.center_id,
                candidate_code=candidate_code,
                issued_at=utcnow(),
            )
        )
    else:
        row.fingerprint = fp_hex
        row.issued_at = utcnow()

    audit.record(
        db,
        actor=username,
        action=audit.chain.WATERMARK_ISSUED,
        target=f"exam:{exam.id}",
        details={"fingerprint": fp_hex, "candidate_code": candidate_code},
    )
    db.commit()

    buf = io.BytesIO()
    watermarked.save(buf, "PNG")
    return buf.getvalue(), fp_hex


def trace_leak(db: Session, image_bytes: bytes, *, actor: str) -> dict:
    """Identify the source of a leaked image against the issued-watermark registry."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    registry = Registry()
    for row in db.query(IssuedWatermark).all():
        registry.entries[int(row.fingerprint, 16)] = {
            "center_id": row.center_id,
            "candidate_id": row.candidate_code,
            "exam_id": row.exam_id,
            "username": row.username,
        }

    result = trace_image(image, registry)

    match = result["match"] if (result["watermark_present"] and result["match"]) else None
    out = {
        "watermark_present": result["watermark_present"],
        "magic_hd": result["magic_hd"],
        "extracted_fingerprint": f"{result['extracted_fingerprint']:016x}",
        "match": match,
        "bit_distance": result["bit_distance"],
        "confidence": result["confidence"],
    }

    audit.record(
        db,
        actor=actor,
        action=audit.chain.LEAK_TRACED,
        details={
            "present": out["watermark_present"],
            "fingerprint": out["extracted_fingerprint"],
            "matched_candidate": match["candidate_id"] if match else None,
            "confidence": round(out["confidence"], 4),
        },
    )
    db.commit()
    return out

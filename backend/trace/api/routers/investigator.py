"""Investigator endpoints: forensic image trace + text leak-match."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import ROLE_ADMIN, ROLE_INVESTIGATOR, User
from ...schemas import LeakMatchIn, LeakMatchOut, TraceOut
from ...security.deps import require_role
from ...services import leakmatch as leak_service
from ...services import watermarking as wm_service

router = APIRouter(prefix="/investigator", tags=["investigator"])


@router.post("/trace", response_model=TraceOut)
async def trace_leak(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(ROLE_INVESTIGATOR, ROLE_ADMIN)),
):
    """Upload a leaked image; recover its fingerprint and name the source copy."""
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload."
        )
    try:
        return wm_service.trace_leak(db, image_bytes, actor=user.username)
    except Exception as exc:  # malformed image, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not process image: {exc}",
        )


@router.post("/match", response_model=LeakMatchOut)
def match_leak(
    body: LeakMatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(ROLE_INVESTIGATOR, ROLE_ADMIN)),
):
    """Match suspected leaked text to bank questions and narrow the source.

    Works on text-only leaks (no image): finds which encrypted questions the text
    contains, then intersects the per-candidate selection records to a suspect set.
    """
    return leak_service.match_leak(db, body.text, actor=user.username)

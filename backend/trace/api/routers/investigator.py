"""Investigator endpoints: forensic trace of a leaked image."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import ROLE_ADMIN, ROLE_INVESTIGATOR, User
from ...schemas import TraceOut
from ...security.deps import require_role
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

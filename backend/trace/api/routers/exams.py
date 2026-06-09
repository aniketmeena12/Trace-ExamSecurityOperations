"""Exam endpoints: seal, list, inspect, custodian unlock ceremony, serve paper."""

from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import (
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_CUSTODIAN,
    ROLE_INVESTIGATOR,
    CustodianShare,
    Exam,
    ShareSubmission,
    User,
)
from ...crypto.shamir import Share
from ...schemas import ExamCreate, ExamOut, MyShareOut, PaperOut, UnlockStatusOut
from ...security.deps import get_current_user, require_role
from ...services import exams as exam_service
from ...services import watermarking as wm_service
from ...services.exams import UnlockError
from ...util import utcnow

router = APIRouter(prefix="/exams", tags=["exams"])

_SAMPLE_PAPER = Path(__file__).resolve().parents[4] / "sample_data" / "sample_paper.txt"


def _get_exam_or_404(db: Session, exam_id: int) -> Exam:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


@router.post("", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    body: ExamCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(ROLE_ADMIN)),
):
    # Resolve release time: explicit timestamp wins, else offset-from-now.
    if body.release_time is not None:
        release_time = body.release_time.replace(tzinfo=None)
    elif body.release_offset_seconds is not None:
        release_time = utcnow() + timedelta(seconds=body.release_offset_seconds)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide release_time or release_offset_seconds.",
        )

    # Resolve custodians.
    if body.custodian_usernames:
        custodians = (
            db.query(User)
            .filter(User.username.in_(body.custodian_usernames), User.role == ROLE_CUSTODIAN)
            .all()
        )
        missing = set(body.custodian_usernames) - {c.username for c in custodians}
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown/non-custodian usernames: {sorted(missing)}",
            )
    else:
        custodians = db.query(User).filter(User.role == ROLE_CUSTODIAN).all()

    if body.threshold_k > len(custodians):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"threshold_k ({body.threshold_k}) exceeds custodian count ({len(custodians)}).",
        )

    paper_text = body.paper_text
    if paper_text is None:
        paper_text = _SAMPLE_PAPER.read_text(encoding="utf-8")

    exam = exam_service.seal_exam(
        db,
        admin,
        name=body.name,
        subject=body.subject,
        center_id=body.center_id,
        paper_text=paper_text,
        release_time=release_time,
        threshold_k=body.threshold_k,
        custodians=custodians,
    )
    return exam


@router.get("", response_model=list[ExamOut])
def list_exams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Exam).order_by(Exam.id.asc()).all()


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return _get_exam_or_404(db, exam_id)


@router.get("/{exam_id}/unlock/status", response_model=UnlockStatusOut)
def get_unlock_status(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    exam = _get_exam_or_404(db, exam_id)
    return exam_service.unlock_status(db, exam)


@router.post("/{exam_id}/shares/submit", response_model=UnlockStatusOut)
def submit_share(
    exam_id: int,
    db: Session = Depends(get_db),
    custodian: User = Depends(require_role(ROLE_CUSTODIAN)),
):
    """A custodian authorizes release of their escrowed share for this exam.

    Triggers an unlock attempt; the server reconstructs the key only when k
    distinct custodians have submitted AND the release time has passed.
    """
    exam = _get_exam_or_404(db, exam_id)
    try:
        return exam_service.submit_share(db, exam, custodian)
    except UnlockError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.get("/{exam_id}/my-share", response_model=MyShareOut)
def my_share(
    exam_id: int,
    db: Session = Depends(get_db),
    custodian: User = Depends(require_role(ROLE_CUSTODIAN)),
):
    """This custodian's escrowed share, revealed only once the window is open.

    The actual share bytes are masked until `release_time` has passed — before
    that the custodian can see *that* they hold a share (and its x-coordinate)
    but not its value.
    """
    exam = _get_exam_or_404(db, exam_id)
    cs = (
        db.query(CustodianShare)
        .filter_by(exam_id=exam.id, custodian_id=custodian.id)
        .first()
    )
    if cs is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a custodian for this exam.",
        )
    st = exam_service.unlock_status(db, exam)
    window_open = not st["time_locked"]
    submitted = (
        db.query(ShareSubmission)
        .filter_by(exam_id=exam.id, custodian_id=custodian.id)
        .first()
        is not None
    )
    return MyShareOut(
        exam_id=exam.id,
        custodian=custodian.username,
        x=cs.x,
        share=Share(cs.x, cs.y).to_hex() if window_open else None,
        masked=not window_open,
        window_open=window_open,
        submitted=submitted,
        status=exam.status,
        release_time=st["release_time"],
        seconds_remaining=st["seconds_remaining"],
    )


@router.get("/{exam_id}/paper", response_model=PaperOut)
def get_paper(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(ROLE_CANDIDATE, ROLE_ADMIN, ROLE_INVESTIGATOR)),
):
    """Serve the released paper text (post-unlock only)."""
    exam = _get_exam_or_404(db, exam_id)
    try:
        content = exam_service.get_paper_plaintext(db, exam, user)
    except UnlockError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    return PaperOut(exam_id=exam.id, name=exam.name, subject=exam.subject, content=content)


@router.get("/{exam_id}/paper/image")
def get_paper_image(
    exam_id: int,
    candidate_username: str | None = Query(
        default=None, description="Admin only: preview a specific candidate's copy."
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(ROLE_CANDIDATE, ROLE_ADMIN)),
):
    """Per-candidate invisible-watermarked paper as a PNG (post-unlock only).

    Candidates always get their own copy; an admin may preview a named
    candidate's copy. Each issuance registers the fingerprint for tracing.
    """
    exam = _get_exam_or_404(db, exam_id)

    if user.role == ROLE_CANDIDATE:
        target = user
    else:  # admin preview
        if not candidate_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="candidate_username is required for admin preview.",
            )
        target = db.query(User).filter_by(username=candidate_username).first()
        if target is None or target.role != ROLE_CANDIDATE:
            raise HTTPException(status_code=404, detail="Candidate not found.")

    candidate_code = target.candidate_code or target.username
    try:
        png_bytes, fp_hex = wm_service.issue_paper_image(
            db, exam, username=target.username, candidate_code=candidate_code
        )
    except UnlockError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "X-Trace-Fingerprint": fp_hex,
            "Cache-Control": "no-store",
        },
    )

"""Question-bank endpoints for dynamic assembly (M5).

Setters/admins contribute individually-encrypted questions ahead of time. Bodies
are AES-256-GCM ciphertext at rest and are never returned over the API — only
metadata (subject/section/topic/difficulty) is listable, so the bank can be
managed without exposing question content.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import ROLE_ADMIN, Question, User
from ...schemas import QuestionCreate, QuestionOut
from ...security.deps import require_role
from ...services import assembly as assembly_service

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def add_question(
    body: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(ROLE_ADMIN)),
):
    """Add one encrypted question to the bank. The body is stored as ciphertext."""
    return assembly_service.add_question(
        db,
        contributor=admin.username,
        subject=body.subject,
        section=body.section,
        topic=body.topic,
        difficulty=body.difficulty,
        prompt=body.prompt,
        options=body.options,
        answer=body.answer,
    )


@router.get("", response_model=list[QuestionOut])
def list_questions(
    subject: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(ROLE_ADMIN)),
):
    """List bank metadata only (never the encrypted bodies)."""
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject == subject)
    return query.order_by(Question.id.asc()).all()

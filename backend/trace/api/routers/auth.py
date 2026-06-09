"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ... import audit
from ...db import get_db
from ...models import User
from ...schemas import TokenOut, UserOut
from ...security.deps import get_current_user
from ...security.passwords import verify_password
from ...security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    audit.record(db, actor=user.username, action=audit.chain.LOGIN, details={"role": user.role})
    db.commit()
    token = create_access_token(user.username, user.role)
    return TokenOut(access_token=token, role=user.role, username=user.username)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

"""FastAPI dependencies for authentication and role-based authorization."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from .tokens import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC
    username = payload.get("sub")
    if not username:
        raise _CREDENTIALS_EXC
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def require_role(*roles: str):
    """Dependency factory: allow only users whose role is in `roles`."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of roles: {', '.join(roles)}",
            )
        return user

    return _dep

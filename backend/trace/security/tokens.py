"""JWT access-token creation and verification (HS256)."""

from datetime import timedelta

import jwt

from ..config import settings
from ..util import utcnow


def create_access_token(username: str, role: str) -> str:
    now = utcnow()
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    """Decode & validate a token. Raises jwt.PyJWTError on any problem."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])

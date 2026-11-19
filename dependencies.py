"""Authentication dependencies used by protected routes."""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RevokedToken, User
from app.security.tokens import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.") from None

    revoked = db.scalar(select(RevokedToken).where(RevokedToken.jti == payload["jti"]))
    if revoked is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This session has ended. Please log in again.",
        )

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    if user.role != payload.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    return user


def require_administrator(user: User = Depends(get_current_user)) -> User:
    if user.role != "administrator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required.")
    return user


def revoke_token(db: Session, jti: str, expires_at: datetime) -> None:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    existing = db.scalar(select(RevokedToken).where(RevokedToken.jti == jti))
    if existing is None:
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
        db.commit()

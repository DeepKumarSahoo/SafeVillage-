"""JSON Web Tokens.

A JWT is a signed ticket. The server does not store the token itself.
It stores only the token id (jti) after logout, in revoked_tokens.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from app.config import get_settings


class TokenError(Exception):
    pass


def create_access_token(user_id: int, role: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    jti = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "exp": expires_at,
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired token.") from exc
    if payload.get("type") != "access" or not payload.get("sub") or not payload.get("jti"):
        raise TokenError("Invalid or expired token.")
    return payload

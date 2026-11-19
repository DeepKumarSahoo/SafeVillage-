from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, MessageResponse, RegisterRequest, TokenResponse, UserPublic
from app.security.dependencies import bearer_scheme, get_current_user, revoke_token
from app.security.passwords import hash_password, verify_password
from app.security.rate_limit import rate_limit
from app.security.tokens import TokenError, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", limit=5))],
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = body.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    try:
        password_hash = hash_password(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    user = User(
        full_name=body.full_name,
        email=email,
        phone=body.phone,
        hashed_password=password_hash,
        role="citizen",
        village=body.village,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit("login", limit=10))])
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    password_ok = False
    if user is not None and user.is_active:
        password_ok = verify_password(body.password, user.hashed_password)
    else:
        # Spend similar time when the account does not exist.
        verify_password(body.password, "$2b$12$C6UzMDM.H6dfI/f/IKcEe.OqYdQ4v1d6q0n1n1n1n1n1n1n1n1n1n")
    if user is None or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    token, _jti, _expires = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=get_settings().access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.") from exc
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    revoke_token(db, payload["jti"], expires_at)
    return MessageResponse(message=f"Signed out {user.full_name}.")

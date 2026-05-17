# Authentication Router — Login and Registration
# API Documentation: Ergasheva Fotima (U2310076)
#
# This file handles how users register and log in to CineLuxe.
#
# ENDPOINT 1: POST /api/auth/register
# What it does: Creates a new user account
# Who can use it: Anyone (no login needed)
# Request body: { "email": "...", "password": "...", "full_name": "..." }
# Response: { "access_token": "...", "token_type": "bearer" }
# Rate limited: max 3 attempts per IP per 60 seconds (prevents bot signups)
# Error codes:
#   400 — email already exists
#   422 — missing required fields
#   429 — too many registration attempts
#
# ENDPOINT 2: POST /api/auth/login
# What it does: Signs in an existing user and returns a JWT token
# Who can use it: Anyone (no login needed)
# Request body: form data with username (email) and password
# Response: { "access_token": "...", "token_type": "bearer" }
# Error codes:
#   401 — wrong email or password
#
# ENDPOINT 3: GET /api/auth/me
# What it does: Returns the profile of the currently logged-in user
# Who can use it: Logged-in users only (JWT token required)
# Response: { "id": "...", "email": "...", "full_name": "...", "is_admin": false }
# Error codes:
#   401 — not logged in (no token or invalid token)
#
# HOW JWT TOKENS WORK:
# 1. User logs in with email + password
# 2. Backend checks if password is correct
# 3. Backend creates a signed JWT token (expires in 24 hours)
# 4. User stores token and sends it with every future request
# 5. Backend verifies the signature — no database lookup needed
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt_lib

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db
from components.rate_limiter import TokenBucketLimiter
from core.config import settings
from models.user import User
from schemas.auth import Token, UserCreate, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 3 registration attempts per IP per 60 s — called once so FastAPI can cache.
_register_limit = TokenBucketLimiter(capacity=3, window_seconds=60, key_prefix="register")
_check_register_rate = _register_limit.limit_by_ip()

_TOKEN_EXPIRE_HOURS = 24


def _hash_password(plain: str) -> str:
    return _bcrypt_lib.hashpw(plain.encode(), _bcrypt_lib.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(plain.encode(), hashed.encode())


def _make_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.secret_key, algorithm="HS256")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(_check_register_rate)],
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(
        email=body.email,
        hashed_password=_hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return Token(access_token=_make_token(str(user.id)))


@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    return Token(access_token=_make_token(str(user.id)))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

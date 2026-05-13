import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_redis():
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise exc
    except JWTError:
        raise exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise exc
    return user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

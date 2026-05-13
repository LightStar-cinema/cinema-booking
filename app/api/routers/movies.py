import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_admin
from models.movie import Movie
from schemas.movie import MovieCreate, MovieOut, MovieUpdate

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
async def list_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    genre: str | None = Query(None),
    active_only: bool = Query(True),
    coming_soon: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    q = select(Movie)
    if coming_soon is True:
        q = q.where(Movie.is_coming_soon == True)   # noqa: E712
    elif coming_soon is False:
        q = q.where(Movie.is_coming_soon == False)  # noqa: E712
    if active_only and coming_soon is not True:
        # Don't apply active_only when browsing coming-soon titles (they're inactive by design)
        q = q.where(Movie.is_active == True)        # noqa: E712
    if genre:
        q = q.where(Movie.genre.ilike(f"%{genre}%"))
    q = q.order_by(Movie.release_date.asc() if coming_soon else Movie.release_date.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    return movie


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
async def create_movie(
    body: MovieCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Movie, Depends(require_admin)],
):
    movie = Movie(**body.model_dump())
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie


@router.patch("/{movie_id}", response_model=MovieOut)
async def update_movie(
    movie_id: uuid.UUID,
    body: MovieUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Movie, Depends(require_admin)],
):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)
    await db.commit()
    await db.refresh(movie)
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Movie, Depends(require_admin)],
):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    movie.is_active = False
    await db.commit()

"""Async SQLAlchemy session factory."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def _build_db_url() -> str:
    if url := os.environ.get("DB_URL"):
        return url
    user = os.environ.get("POSTGRES_USER", "soccercv_user")
    password = os.environ.get("POSTGRES_PASSWORD", "LiverP00l4Ever")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "soccercv_db")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

DB_URL = _build_db_url()

engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

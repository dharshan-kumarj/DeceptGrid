"""
database.py – Async SQLAlchemy engine + session factory.

All environment variables are loaded from .env via python-dotenv.
The DATABASE_URL must use the asyncpg driver:
  postgresql+asyncpg://user:pass@host:port/db
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv(find_dotenv())

# Load and prepare DATABASE_URL
DATABASE_URL: str = os.environ["DATABASE_URL"]

# Auto-fix driver for async SQLAlchemy if standard postgres:// is used
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # Set to True for SQL debug logging; never in production.
    pool_pre_ping=True,   # Detect stale connections before use.
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession per request.
    The session is always closed even if the handler raises.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

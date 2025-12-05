"""
Database Session Management

Provides synchronous and asynchronous database session factories
with proper connection pooling and lifecycle management.
"""

import os
import logging
from typing import Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from db.base import Base

logger = logging.getLogger(__name__)


# =============================================================================
# Database Configuration
# =============================================================================

class DatabaseConfig:
    """Database configuration from environment variables."""
    
    # PostgreSQL connection settings
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "nexus")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nexus_password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "nexus_admin")
    
    # Connection pool settings
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    
    # SQLite fallback for development/testing
    USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
    SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./nexus_admin.db")
    
    @classmethod
    def get_sync_url(cls) -> str:
        """Get synchronous database URL."""
        if cls.USE_SQLITE:
            return cls.SQLITE_URL
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )
    
    @classmethod
    def get_async_url(cls) -> str:
        """Get asynchronous database URL."""
        if cls.USE_SQLITE:
            return cls.SQLITE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return (
            f"postgresql+asyncpg://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )


# =============================================================================
# Engine Creation
# =============================================================================

def create_sync_engine():
    """Create synchronous SQLAlchemy engine."""
    url = DatabaseConfig.get_sync_url()
    
    if DatabaseConfig.USE_SQLITE:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=DatabaseConfig.POOL_SIZE,
        max_overflow=DatabaseConfig.MAX_OVERFLOW,
        pool_timeout=DatabaseConfig.POOL_TIMEOUT,
        pool_recycle=DatabaseConfig.POOL_RECYCLE,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )


def create_async_engine_instance():
    """Create asynchronous SQLAlchemy engine."""
    url = DatabaseConfig.get_async_url()
    
    if DatabaseConfig.USE_SQLITE:
        return create_async_engine(
            url,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    
    return create_async_engine(
        url,
        pool_size=DatabaseConfig.POOL_SIZE,
        max_overflow=DatabaseConfig.MAX_OVERFLOW,
        pool_timeout=DatabaseConfig.POOL_TIMEOUT,
        pool_recycle=DatabaseConfig.POOL_RECYCLE,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )


# Create engine instances
engine = create_sync_engine()
async_engine = create_async_engine_instance()


# =============================================================================
# Session Factories
# =============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# Dependency Injection
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Synchronous database session dependency.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous database session dependency.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
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


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_async_db_context() as db:
            result = await db.execute(select(Item))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# Database Initialization
# =============================================================================

def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in the models.
    Call this during application startup.
    """
    # Import all models to ensure they're registered with Base
    from models import user, role, audit_log, refresh_token  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


async def init_async_db() -> None:
    """
    Initialize database tables asynchronously.
    """
    from models import user, role, audit_log, refresh_token  # noqa: F401
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully (async)")


def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


# =============================================================================
# Connection Health Check
# =============================================================================

def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with get_db_context() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def check_async_db_connection() -> bool:
    """Check if async database connection is healthy."""
    try:
        async with get_async_db_context() as db:
            await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        return False


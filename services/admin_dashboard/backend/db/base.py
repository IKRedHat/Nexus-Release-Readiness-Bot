"""
SQLAlchemy Base Configuration

Defines the declarative base and common model mixins.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common functionality and metadata configuration.
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UUIDMixin:
    """
    Mixin that provides a UUID primary key.
    """
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


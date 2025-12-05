"""
Refresh Token Model

SQLAlchemy model for managing JWT refresh tokens.
Supports token rotation and revocation for security.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, generate_uuid
import secrets


class RefreshTokenModel(Base):
    """
    Refresh token database model.
    
    Manages refresh tokens for JWT authentication with support for:
    - Token rotation (new token issued on refresh)
    - Token revocation (logout, security concerns)
    - Expiration tracking
    - Device/session tracking
    """
    __tablename__ = "refresh_tokens"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    # The actual token (hashed for security)
    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Token owner
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Revocation
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Token chain (for rotation tracking)
    previous_token_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True
    )
    
    # Device/session info
    device_info: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True
    )
    
    # Composite indexes
    __table_args__ = (
        Index("ix_refresh_user_valid", "user_id", "revoked_at", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"
    
    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired
    
    def revoke(self, reason: str = "manual") -> None:
        """Revoke this token."""
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason
    
    @classmethod
    def create_token(
        cls,
        user_id: str,
        expires_in_days: int = 7,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        previous_token_id: Optional[str] = None,
    ) -> tuple["RefreshTokenModel", str]:
        """
        Create a new refresh token.
        
        Returns:
            tuple: (RefreshTokenModel instance, plain token string)
        """
        # Generate secure token
        plain_token = secrets.token_urlsafe(64)
        
        # Hash for storage
        import hashlib
        token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
        
        instance = cls(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            device_info=device_info,
            ip_address=ip_address,
            previous_token_id=previous_token_id,
        )
        
        return instance, plain_token
    
    @classmethod
    def hash_token(cls, plain_token: str) -> str:
        """Hash a plain token for lookup."""
        import hashlib
        return hashlib.sha256(plain_token.encode()).hexdigest()


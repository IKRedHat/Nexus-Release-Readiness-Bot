"""
User Model

SQLAlchemy model for user management with SSO and local authentication support.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Enum, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from models.role import RoleModel
    from models.audit_log import AuditLogModel


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SSOProvider(str, enum.Enum):
    """Supported SSO providers."""
    LOCAL = "local"
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    GITHUB = "github"


class UserModel(Base, TimestampMixin):
    """
    User database model.
    
    Stores user information including authentication details,
    SSO provider info, and role assignments.
    """
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    # Basic info
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # Authentication
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True  # Null for SSO users
    )
    sso_provider: Mapped[str] = mapped_column(
        String(50),
        default=SSOProvider.LOCAL.value,
        nullable=False
    )
    sso_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True  # External SSO identifier
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Security
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    roles: Mapped[List["RoleModel"]] = relationship(
        "RoleModel",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    
    audit_logs: Mapped[List["AuditLogModel"]] = relationship(
        "AuditLogModel",
        back_populates="user",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE.value
    
    @property
    def is_local(self) -> bool:
        """Check if user uses local authentication."""
        return self.sso_provider == SSOProvider.LOCAL.value
    
    @property
    def role_names(self) -> List[str]:
        """Get list of role names."""
        return [role.name for role in self.roles]
    
    @property
    def permissions(self) -> set:
        """Get all permissions from assigned roles."""
        perms = set()
        for role in self.roles:
            if role.permissions:
                perms.update(role.permissions)
        return perms
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "status": self.status,
            "sso_provider": self.sso_provider,
            "avatar_url": self.avatar_url,
            "department": self.department,
            "title": self.title,
            "roles": self.role_names,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


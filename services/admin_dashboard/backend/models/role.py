"""
Role Model

SQLAlchemy model for role-based access control (RBAC).
"""

from datetime import datetime
from typing import List, Optional, Set, TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from db.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from models.user import UserModel


# Association table for many-to-many user-role relationship
UserRoleAssociation = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default="now()"),
    Column("assigned_by", String(36), nullable=True),
)


class RoleModel(Base, TimestampMixin):
    """
    Role database model.
    
    Defines roles with permissions for RBAC.
    Supports role hierarchy through parent_role_id.
    """
    __tablename__ = "roles"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Permissions stored as JSON array
    permissions: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    # Role hierarchy
    parent_role_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # System role flag (can't be deleted)
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Who created this role
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )
    
    parent_role: Mapped[Optional["RoleModel"]] = relationship(
        "RoleModel",
        remote_side=[id],
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, is_system={self.is_system_role})>"
    
    @property
    def all_permissions(self) -> Set[str]:
        """
        Get all permissions including inherited from parent role.
        """
        perms = set(self.permissions or [])
        if self.parent_role:
            perms.update(self.parent_role.all_permissions)
        return perms
    
    @property
    def user_count(self) -> int:
        """Get number of users with this role."""
        return len(self.users) if self.users else 0
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.all_permissions
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions or []),
            "parent_role_id": self.parent_role_id,
            "is_system_role": self.is_system_role,
            "user_count": self.user_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# Default System Roles
# =============================================================================

SYSTEM_ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full system administrator with all permissions",
        "permissions": [
            "system:admin", "system:config", "system:audit",
            "users:create", "users:read", "users:update", "users:delete",
            "roles:create", "roles:read", "roles:update", "roles:delete",
            "releases:create", "releases:read", "releases:update", "releases:delete",
            "feature_requests:create", "feature_requests:read", "feature_requests:update", "feature_requests:delete",
            "health:read", "metrics:read", "audit:read",
        ],
        "is_system_role": True,
    },
    "developer": {
        "name": "Developer",
        "description": "Developer role with release and feature request access",
        "permissions": [
            "releases:create", "releases:read", "releases:update",
            "feature_requests:create", "feature_requests:read", "feature_requests:update",
            "health:read", "metrics:read",
        ],
        "is_system_role": True,
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access to dashboard data",
        "permissions": [
            "releases:read",
            "feature_requests:read",
            "health:read", "metrics:read",
        ],
        "is_system_role": True,
    },
    "operator": {
        "name": "Operator",
        "description": "Operations team with health and metrics focus",
        "permissions": [
            "releases:read",
            "health:read", "metrics:read",
            "system:config",
        ],
        "is_system_role": True,
    },
}


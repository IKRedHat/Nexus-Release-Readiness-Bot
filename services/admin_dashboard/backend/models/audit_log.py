"""
Audit Log Model

SQLAlchemy model for tracking all system activities and changes.
Provides complete audit trail for compliance and debugging.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from db.base import Base, generate_uuid

if TYPE_CHECKING:
    from models.user import UserModel


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"
    
    # Role management
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    
    # Release management
    RELEASE_CREATE = "release_create"
    RELEASE_UPDATE = "release_update"
    RELEASE_DELETE = "release_delete"
    RELEASE_PUBLISH = "release_publish"
    
    # Feature requests
    FEATURE_REQUEST_CREATE = "feature_request_create"
    FEATURE_REQUEST_UPDATE = "feature_request_update"
    FEATURE_REQUEST_DELETE = "feature_request_delete"
    FEATURE_REQUEST_APPROVE = "feature_request_approve"
    FEATURE_REQUEST_REJECT = "feature_request_reject"
    
    # System
    CONFIG_UPDATE = "config_update"
    MODE_CHANGE = "mode_change"
    SYSTEM_ERROR = "system_error"


class AuditLogModel(Base):
    """
    Audit log database model.
    
    Records all significant actions in the system for 
    compliance, debugging, and activity tracking.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    # Timestamp (not using mixin - we want immutable timestamps)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=datetime.utcnow
    )
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True  # Stored separately for historical accuracy
    )
    
    # What action was performed
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # What resource was affected
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )
    
    # Additional details as JSON
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Result
    success: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        back_populates="audit_logs",
        lazy="joined"
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_audit_user_time", "user_id", "timestamp"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_action_time", "action", "timestamp"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_email})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "success": self.success,
            "error_message": self.error_message,
        }
    
    @classmethod
    def create_log(
        cls,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> "AuditLogModel":
        """Factory method to create audit log entries."""
        return cls(
            action=action.value if isinstance(action, AuditAction) else action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )


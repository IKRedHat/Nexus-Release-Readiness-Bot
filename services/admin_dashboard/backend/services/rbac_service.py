"""
RBAC Database Service

High-level service for Role-Based Access Control operations.
Provides a unified interface that can work with either:
- PostgreSQL database (production)
- In-memory storage (fallback/development)
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Configuration
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"


class RBACDatabaseService:
    """
    RBAC service with database persistence.
    
    This service provides a clean interface for RBAC operations
    and handles the complexity of database vs in-memory storage.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize service.
        
        Args:
            db: Optional database session. If None, uses in-memory storage.
        """
        self.db = db
        self._use_db = USE_DATABASE and db is not None
    
    # ==========================================================================
    # User Operations
    # ==========================================================================
    
    def create_user(
        self,
        email: str,
        name: str,
        password: Optional[str] = None,
        sso_provider: str = "local",
        sso_id: Optional[str] = None,
        roles: List[str] = None,
        status: str = "active",
    ) -> Dict[str, Any]:
        """Create a new user."""
        if self._use_db:
            from crud import crud_user
            from crud.user import UserCreate
            
            user_data = UserCreate(
                email=email,
                name=name,
                password=password,
                sso_provider=sso_provider,
                sso_id=sso_id,
                roles=roles or [],
                status=status,
            )
            
            user = crud_user.create_with_roles(
                self.db,
                obj_in=user_data,
                role_ids=roles or [],
            )
            return user.to_dict()
        else:
            # Fallback to in-memory
            from auth import rbac_store, RBACService
            return RBACService.create_user_dict(
                email=email,
                name=name,
                roles=roles or [],
                sso_provider=sso_provider,
            )
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        if self._use_db:
            from crud import crud_user
            user = crud_user.get(self.db, id=user_id)
            return user.to_dict() if user else None
        else:
            from auth import RBACService
            user = RBACService.get_user(user_id)
            return user.model_dump() if user else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        if self._use_db:
            from crud import crud_user
            user = crud_user.get_by_email(self.db, email=email)
            return user.to_dict() if user else None
        else:
            from auth import rbac_store
            for user in rbac_store.users.values():
                if user.email == email:
                    return user.model_dump()
            return None
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all users."""
        if self._use_db:
            from crud import crud_user
            if status == "active":
                users = crud_user.get_active_users(self.db, skip=skip, limit=limit)
            else:
                users = crud_user.get_multi(self.db, skip=skip, limit=limit)
            return [u.to_dict() for u in users]
        else:
            from auth import RBACService
            users = RBACService.list_users()
            return [u.model_dump() for u in users][skip:skip+limit]
    
    def update_user(
        self,
        user_id: str,
        **updates,
    ) -> Optional[Dict[str, Any]]:
        """Update user."""
        if self._use_db:
            from crud import crud_user
            from crud.user import UserUpdate
            
            user = crud_user.get(self.db, id=user_id)
            if not user:
                return None
            
            update_data = UserUpdate(**{k: v for k, v in updates.items() if v is not None})
            user = crud_user.update(self.db, db_obj=user, obj_in=update_data)
            return user.to_dict()
        else:
            from auth import RBACService, rbac_store
            user = RBACService.get_user(user_id)
            if not user:
                return None
            for key, value in updates.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            rbac_store.users[user_id] = user
            return user.model_dump()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        if self._use_db:
            from crud import crud_user
            user = crud_user.soft_delete(self.db, id=user_id)
            return user is not None
        else:
            from auth import RBACService
            return RBACService.delete_user(user_id)
    
    # ==========================================================================
    # Role Operations
    # ==========================================================================
    
    def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: List[str] = None,
        parent_role_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new role."""
        if self._use_db:
            from crud import crud_role
            from crud.role import RoleCreate
            
            role_data = RoleCreate(
                name=name,
                description=description,
                permissions=permissions or [],
                parent_role_id=parent_role_id,
            )
            role = crud_role.create(self.db, obj_in=role_data)
            return role.to_dict()
        else:
            from auth import RBACService
            role = RBACService.create_role(
                name=name,
                description=description,
                permissions=set(permissions or []),
            )
            return role.model_dump() if role else {}
    
    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID."""
        if self._use_db:
            from crud import crud_role
            role = crud_role.get(self.db, id=role_id)
            return role.to_dict() if role else None
        else:
            from auth import rbac_store
            role = rbac_store.roles.get(role_id)
            return role.model_dump() if role else None
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles."""
        if self._use_db:
            from crud import crud_role
            roles = crud_role.get_multi(self.db, limit=1000)
            return [r.to_dict() for r in roles]
        else:
            from auth import rbac_store
            return [r.model_dump() for r in rbac_store.roles.values()]
    
    def update_role(
        self,
        role_id: str,
        **updates,
    ) -> Optional[Dict[str, Any]]:
        """Update role."""
        if self._use_db:
            from crud import crud_role
            from crud.role import RoleUpdate
            
            role = crud_role.get(self.db, id=role_id)
            if not role:
                return None
            
            update_data = RoleUpdate(**{k: v for k, v in updates.items() if v is not None})
            role = crud_role.update(self.db, db_obj=role, obj_in=update_data)
            return role.to_dict()
        else:
            from auth import RBACService, rbac_store
            role = rbac_store.roles.get(role_id)
            if not role:
                return None
            for key, value in updates.items():
                if hasattr(role, key) and value is not None:
                    setattr(role, key, value)
            return role.model_dump()
    
    def delete_role(self, role_id: str) -> bool:
        """Delete role."""
        if self._use_db:
            from crud import crud_role
            try:
                role = crud_role.soft_delete(self.db, id=role_id)
                return role is not None
            except ValueError:
                return False
        else:
            from auth import RBACService
            return RBACService.delete_role(role_id)
    
    # ==========================================================================
    # Audit Log Operations
    # ==========================================================================
    
    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create audit log entry."""
        if self._use_db:
            from crud import crud_audit
            log = crud_audit.create_log(
                self.db,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                user_email=user_email,
                details=details,
                ip_address=ip_address,
                success=success,
                error_message=error_message,
            )
            return log.to_dict()
        else:
            from auth import RBACService
            log = RBACService.log_action(
                user_email=user_email or "system",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
            )
            return log.model_dump() if log else {}
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get audit logs with filtering."""
        if self._use_db:
            from crud import crud_audit
            from crud.audit_log import AuditLogFilter
            
            filters = AuditLogFilter(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                start_date=start_date,
                end_date=end_date,
            )
            logs, total = crud_audit.filter_logs(
                self.db,
                filters=filters,
                skip=skip,
                limit=limit,
            )
            return [log.to_dict() for log in logs], total
        else:
            from auth import RBACService
            logs = RBACService.get_audit_logs(limit=limit)
            return [log.model_dump() for log in logs], len(logs)
    
    def get_audit_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get audit log statistics."""
        if self._use_db:
            from crud import crud_audit
            return crud_audit.get_stats(self.db, days=days)
        else:
            from auth import rbac_store
            return {
                "total_events": len(rbac_store.audit_logs),
                "success_rate": 100.0,
                "by_action": {},
                "by_resource": {},
                "period_days": days,
            }
    
    # ==========================================================================
    # Token Operations
    # ==========================================================================
    
    def create_refresh_token(
        self,
        user_id: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, datetime]:
        """
        Create refresh token.
        
        Returns:
            Tuple of (token_string, expires_at)
        """
        if self._use_db:
            from crud import crud_refresh_token
            token_model, plain_token = crud_refresh_token.create_token(
                self.db,
                user_id=user_id,
                device_info=device_info,
                ip_address=ip_address,
            )
            return plain_token, token_model.expires_at
        else:
            from auth import create_refresh_token
            token = create_refresh_token(user_id)
            from datetime import timedelta
            expires = datetime.utcnow() + timedelta(days=7)
            return token, expires
    
    def validate_refresh_token(self, token: str) -> Optional[str]:
        """
        Validate refresh token.
        
        Returns:
            user_id if valid, None otherwise
        """
        if self._use_db:
            from crud import crud_refresh_token
            token_model = crud_refresh_token.validate_token(self.db, plain_token=token)
            return token_model.user_id if token_model else None
        else:
            from auth import rbac_store
            return rbac_store.refresh_tokens.get(token)
    
    def rotate_refresh_token(
        self,
        old_token: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Tuple[str, datetime]]:
        """
        Rotate refresh token.
        
        Returns:
            Tuple of (new_token_string, expires_at) or None if invalid
        """
        if self._use_db:
            from crud import crud_refresh_token
            result = crud_refresh_token.rotate_token(
                self.db,
                plain_token=old_token,
                device_info=device_info,
                ip_address=ip_address,
            )
            if result:
                token_model, plain_token = result
                return plain_token, token_model.expires_at
            return None
        else:
            from auth import rbac_store, create_refresh_token
            user_id = rbac_store.refresh_tokens.get(old_token)
            if not user_id:
                return None
            del rbac_store.refresh_tokens[old_token]
            new_token = create_refresh_token(user_id)
            from datetime import timedelta
            expires = datetime.utcnow() + timedelta(days=7)
            return new_token, expires
    
    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token."""
        if self._use_db:
            from crud import crud_refresh_token
            result = crud_refresh_token.revoke_token(self.db, plain_token=token)
            return result is not None
        else:
            from auth import rbac_store
            if token in rbac_store.refresh_tokens:
                del rbac_store.refresh_tokens[token]
                return True
            return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        if self._use_db:
            from crud import crud_refresh_token
            return crud_refresh_token.revoke_all_user_tokens(self.db, user_id=user_id)
        else:
            from auth import rbac_store
            tokens_to_remove = [
                t for t, uid in rbac_store.refresh_tokens.items() 
                if uid == user_id
            ]
            for t in tokens_to_remove:
                del rbac_store.refresh_tokens[t]
            return len(tokens_to_remove)


# =============================================================================
# Dependency Injection
# =============================================================================

def get_rbac_service(db: Session = None) -> RBACDatabaseService:
    """
    Get RBAC service instance.
    
    For use as FastAPI dependency:
        @app.get("/users")
        def get_users(rbac: RBACDatabaseService = Depends(get_rbac_service)):
            return rbac.list_users()
    """
    if USE_DATABASE:
        from db.session import get_db_context
        with get_db_context() as session:
            return RBACDatabaseService(session)
    return RBACDatabaseService(None)


async def get_rbac_service_async(db: AsyncSession = None) -> RBACDatabaseService:
    """
    Get RBAC service instance (async).
    
    For use as FastAPI async dependency.
    """
    if USE_DATABASE and db:
        return RBACDatabaseService(db)
    return RBACDatabaseService(None)


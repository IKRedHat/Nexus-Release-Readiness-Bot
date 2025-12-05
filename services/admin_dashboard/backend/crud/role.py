"""
Role CRUD Operations

Specialized CRUD operations for role management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.role import RoleModel, SYSTEM_ROLES


class RoleCreate(BaseModel):
    """Schema for role creation."""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    parent_role_id: Optional[str] = None
    is_system_role: bool = False


class RoleUpdate(BaseModel):
    """Schema for role updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    parent_role_id: Optional[str] = None


class CRUDRole(CRUDBase[RoleModel, RoleCreate, RoleUpdate]):
    """
    Role CRUD operations with additional role-specific methods.
    """
    
    # ==========================================================================
    # Synchronous Operations
    # ==========================================================================
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[RoleModel]:
        """Get role by name."""
        return db.query(RoleModel).filter(RoleModel.name == name).first()
    
    def get_system_roles(self, db: Session) -> List[RoleModel]:
        """Get all system roles."""
        return db.query(RoleModel).filter(
            RoleModel.is_system_role == True,
            RoleModel.deleted_at.is_(None),
        ).all()
    
    def get_custom_roles(self, db: Session) -> List[RoleModel]:
        """Get all custom (non-system) roles."""
        return db.query(RoleModel).filter(
            RoleModel.is_system_role == False,
            RoleModel.deleted_at.is_(None),
        ).all()
    
    def get_with_users(
        self,
        db: Session,
        *,
        id: str,
    ) -> Optional[RoleModel]:
        """Get role with users loaded."""
        return db.query(RoleModel).options(
            selectinload(RoleModel.users)
        ).filter(RoleModel.id == id).first()
    
    def get_permissions(self, db: Session, *, id: str) -> Set[str]:
        """Get all permissions for a role including inherited."""
        role = self.get(db, id=id)
        if not role:
            return set()
        return role.all_permissions
    
    def add_permission(
        self,
        db: Session,
        *,
        role: RoleModel,
        permission: str,
    ) -> RoleModel:
        """Add permission to role."""
        if role.permissions is None:
            role.permissions = []
        if permission not in role.permissions:
            role.permissions = list(role.permissions) + [permission]
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def remove_permission(
        self,
        db: Session,
        *,
        role: RoleModel,
        permission: str,
    ) -> RoleModel:
        """Remove permission from role."""
        if role.permissions and permission in role.permissions:
            perms = list(role.permissions)
            perms.remove(permission)
            role.permissions = perms
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def set_permissions(
        self,
        db: Session,
        *,
        role: RoleModel,
        permissions: List[str],
    ) -> RoleModel:
        """Set role permissions."""
        role.permissions = permissions
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def soft_delete(self, db: Session, *, id: str) -> Optional[RoleModel]:
        """Soft delete role (mark as deleted)."""
        role = self.get(db, id=id)
        if role:
            if role.is_system_role:
                raise ValueError("Cannot delete system role")
            role.deleted_at = datetime.utcnow()
            db.add(role)
            db.commit()
            db.refresh(role)
        return role
    
    def initialize_system_roles(self, db: Session) -> List[RoleModel]:
        """Initialize predefined system roles."""
        created = []
        for role_id, role_data in SYSTEM_ROLES.items():
            existing = self.get_by_name(db, name=role_data["name"])
            if not existing:
                role = RoleModel(
                    id=role_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system_role=role_data["is_system_role"],
                    created_by="system",
                )
                db.add(role)
                created.append(role)
        
        if created:
            db.commit()
            for role in created:
                db.refresh(role)
        
        return created
    
    # ==========================================================================
    # Asynchronous Operations
    # ==========================================================================
    
    async def get_by_name_async(
        self,
        db: AsyncSession,
        *,
        name: str,
    ) -> Optional[RoleModel]:
        """Get role by name (async)."""
        result = await db.execute(
            select(RoleModel).where(RoleModel.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_system_roles_async(self, db: AsyncSession) -> List[RoleModel]:
        """Get all system roles (async)."""
        result = await db.execute(
            select(RoleModel)
            .where(
                RoleModel.is_system_role == True,
                RoleModel.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
    
    async def get_with_users_async(
        self,
        db: AsyncSession,
        *,
        id: str,
    ) -> Optional[RoleModel]:
        """Get role with users loaded (async)."""
        result = await db.execute(
            select(RoleModel)
            .where(RoleModel.id == id)
            .options(selectinload(RoleModel.users))
        )
        return result.scalar_one_or_none()
    
    async def initialize_system_roles_async(
        self,
        db: AsyncSession,
    ) -> List[RoleModel]:
        """Initialize predefined system roles (async)."""
        created = []
        for role_id, role_data in SYSTEM_ROLES.items():
            existing = await self.get_by_name_async(db, name=role_data["name"])
            if not existing:
                role = RoleModel(
                    id=role_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system_role=role_data["is_system_role"],
                    created_by="system",
                )
                db.add(role)
                created.append(role)
        
        if created:
            await db.commit()
            for role in created:
                await db.refresh(role)
        
        return created


# Global CRUD instance
crud_role = CRUDRole(RoleModel)


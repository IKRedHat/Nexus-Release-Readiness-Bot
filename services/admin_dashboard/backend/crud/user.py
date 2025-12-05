"""
User CRUD Operations

Specialized CRUD operations for user management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

from crud.base import CRUDBase
from models.user import UserModel, UserStatus, SSOProvider
from models.role import RoleModel


class UserCreate(BaseModel):
    """Schema for user creation."""
    email: str
    name: str
    password: Optional[str] = None
    sso_provider: str = "local"
    sso_id: Optional[str] = None
    status: str = "active"
    roles: List[str] = []
    department: Optional[str] = None
    title: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[str]] = None
    department: Optional[str] = None
    title: Optional[str] = None
    avatar_url: Optional[str] = None


class CRUDUser(CRUDBase[UserModel, UserCreate, UserUpdate]):
    """
    User CRUD operations with additional user-specific methods.
    """
    
    # ==========================================================================
    # Synchronous Operations
    # ==========================================================================
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[UserModel]:
        """Get user by email address."""
        return db.query(UserModel).filter(UserModel.email == email).first()
    
    def get_by_sso(
        self,
        db: Session,
        *,
        provider: str,
        sso_id: str,
    ) -> Optional[UserModel]:
        """Get user by SSO provider and ID."""
        return db.query(UserModel).filter(
            UserModel.sso_provider == provider,
            UserModel.sso_id == sso_id,
        ).first()
    
    def get_active_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get all active users."""
        return db.query(UserModel).filter(
            UserModel.status == UserStatus.ACTIVE.value,
            UserModel.deleted_at.is_(None),
        ).offset(skip).limit(limit).all()
    
    def get_by_role(
        self,
        db: Session,
        *,
        role_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get users with a specific role."""
        return db.query(UserModel).join(
            UserModel.roles
        ).filter(
            RoleModel.name == role_name,
        ).offset(skip).limit(limit).all()
    
    def search(
        self,
        db: Session,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Search users by email or name."""
        search_pattern = f"%{query}%"
        return db.query(UserModel).filter(
            or_(
                UserModel.email.ilike(search_pattern),
                UserModel.name.ilike(search_pattern),
            )
        ).offset(skip).limit(limit).all()
    
    def create_with_roles(
        self,
        db: Session,
        *,
        obj_in: UserCreate,
        role_ids: List[str],
    ) -> UserModel:
        """Create user with role assignments."""
        # Hash password if provided
        password_hash = None
        if obj_in.password:
            password_hash = hashlib.sha256(obj_in.password.encode()).hexdigest()
        
        user = UserModel(
            email=obj_in.email,
            name=obj_in.name,
            password_hash=password_hash,
            sso_provider=obj_in.sso_provider,
            sso_id=obj_in.sso_id,
            status=obj_in.status,
            department=obj_in.department,
            title=obj_in.title,
        )
        
        # Assign roles
        if role_ids:
            roles = db.query(RoleModel).filter(RoleModel.id.in_(role_ids)).all()
            user.roles = roles
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def update_roles(
        self,
        db: Session,
        *,
        user: UserModel,
        role_ids: List[str],
    ) -> UserModel:
        """Update user's role assignments."""
        roles = db.query(RoleModel).filter(RoleModel.id.in_(role_ids)).all()
        user.roles = roles
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def verify_password(self, user: UserModel, password: str) -> bool:
        """Verify user password."""
        if not user.password_hash:
            return False
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return user.password_hash == hashed
    
    def update_password(
        self,
        db: Session,
        *,
        user: UserModel,
        new_password: str,
    ) -> UserModel:
        """Update user password."""
        user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user.password_changed_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def record_login(
        self,
        db: Session,
        *,
        user: UserModel,
        success: bool = True,
    ) -> UserModel:
        """Record login attempt."""
        if success:
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            user.locked_until = None
        else:
            user.failed_login_attempts += 1
            # Lock after 5 failed attempts
            if user.failed_login_attempts >= 5:
                from datetime import timedelta
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def soft_delete(self, db: Session, *, id: str) -> Optional[UserModel]:
        """Soft delete user (mark as deleted)."""
        user = self.get(db, id=id)
        if user:
            user.status = UserStatus.DELETED.value
            user.deleted_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def suspend(self, db: Session, *, id: str) -> Optional[UserModel]:
        """Suspend user account."""
        user = self.get(db, id=id)
        if user:
            user.status = UserStatus.SUSPENDED.value
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def activate(self, db: Session, *, id: str) -> Optional[UserModel]:
        """Activate user account."""
        user = self.get(db, id=id)
        if user:
            user.status = UserStatus.ACTIVE.value
            user.locked_until = None
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    # ==========================================================================
    # Asynchronous Operations
    # ==========================================================================
    
    async def get_by_email_async(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> Optional[UserModel]:
        """Get user by email (async)."""
        result = await db.execute(
            select(UserModel)
            .where(UserModel.email == email)
            .options(selectinload(UserModel.roles))
        )
        return result.scalar_one_or_none()
    
    async def get_by_sso_async(
        self,
        db: AsyncSession,
        *,
        provider: str,
        sso_id: str,
    ) -> Optional[UserModel]:
        """Get user by SSO provider and ID (async)."""
        result = await db.execute(
            select(UserModel)
            .where(
                UserModel.sso_provider == provider,
                UserModel.sso_id == sso_id,
            )
            .options(selectinload(UserModel.roles))
        )
        return result.scalar_one_or_none()
    
    async def get_active_users_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get all active users (async)."""
        result = await db.execute(
            select(UserModel)
            .where(
                UserModel.status == UserStatus.ACTIVE.value,
                UserModel.deleted_at.is_(None),
            )
            .options(selectinload(UserModel.roles))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def search_async(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Search users by email or name (async)."""
        search_pattern = f"%{query}%"
        result = await db.execute(
            select(UserModel)
            .where(
                or_(
                    UserModel.email.ilike(search_pattern),
                    UserModel.name.ilike(search_pattern),
                )
            )
            .options(selectinload(UserModel.roles))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Global CRUD instance
crud_user = CRUDUser(UserModel)


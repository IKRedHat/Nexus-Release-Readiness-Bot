"""
Refresh Token CRUD Operations

Specialized CRUD operations for JWT refresh token management.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.refresh_token import RefreshTokenModel


class RefreshTokenCreate(BaseModel):
    """Schema for refresh token creation."""
    user_id: str
    expires_in_days: int = 7
    device_info: Optional[str] = None
    ip_address: Optional[str] = None


class CRUDRefreshToken(CRUDBase[RefreshTokenModel, RefreshTokenCreate, BaseModel]):
    """
    Refresh token CRUD operations.
    
    Manages JWT refresh tokens with support for:
    - Token creation with automatic hashing
    - Token validation and lookup
    - Token rotation
    - Revocation (single and bulk)
    """
    
    # ==========================================================================
    # Synchronous Operations
    # ==========================================================================
    
    def create_token(
        self,
        db: Session,
        *,
        user_id: str,
        expires_in_days: int = 7,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        previous_token_id: Optional[str] = None,
    ) -> Tuple[RefreshTokenModel, str]:
        """
        Create new refresh token.
        
        Returns:
            Tuple of (RefreshTokenModel, plain_token_string)
        """
        token_model, plain_token = RefreshTokenModel.create_token(
            user_id=user_id,
            expires_in_days=expires_in_days,
            device_info=device_info,
            ip_address=ip_address,
            previous_token_id=previous_token_id,
        )
        
        db.add(token_model)
        db.commit()
        db.refresh(token_model)
        
        return token_model, plain_token
    
    def get_by_token(
        self,
        db: Session,
        *,
        plain_token: str,
    ) -> Optional[RefreshTokenModel]:
        """
        Get refresh token by plain token string.
        
        Validates token hash against stored hash.
        """
        token_hash = RefreshTokenModel.hash_token(plain_token)
        return db.query(RefreshTokenModel).filter(
            RefreshTokenModel.token_hash == token_hash
        ).first()
    
    def validate_token(
        self,
        db: Session,
        *,
        plain_token: str,
    ) -> Optional[RefreshTokenModel]:
        """
        Validate refresh token.
        
        Returns token if valid, None if invalid/expired/revoked.
        """
        token = self.get_by_token(db, plain_token=plain_token)
        if token and token.is_valid:
            return token
        return None
    
    def get_user_tokens(
        self,
        db: Session,
        *,
        user_id: str,
        active_only: bool = True,
    ) -> List[RefreshTokenModel]:
        """Get all tokens for a user."""
        query = db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_id == user_id
        )
        
        if active_only:
            query = query.filter(
                RefreshTokenModel.revoked_at.is_(None),
                RefreshTokenModel.expires_at > datetime.utcnow(),
            )
        
        return query.order_by(RefreshTokenModel.created_at.desc()).all()
    
    def revoke_token(
        self,
        db: Session,
        *,
        plain_token: str,
        reason: str = "manual",
    ) -> Optional[RefreshTokenModel]:
        """Revoke a specific token."""
        token = self.get_by_token(db, plain_token=plain_token)
        if token:
            token.revoke(reason)
            db.add(token)
            db.commit()
            db.refresh(token)
        return token
    
    def revoke_by_id(
        self,
        db: Session,
        *,
        token_id: str,
        reason: str = "manual",
    ) -> Optional[RefreshTokenModel]:
        """Revoke token by ID."""
        token = self.get(db, id=token_id)
        if token:
            token.revoke(reason)
            db.add(token)
            db.commit()
            db.refresh(token)
        return token
    
    def revoke_all_user_tokens(
        self,
        db: Session,
        *,
        user_id: str,
        reason: str = "logout_all",
    ) -> int:
        """
        Revoke all tokens for a user.
        
        Returns:
            Number of tokens revoked
        """
        tokens = self.get_user_tokens(db, user_id=user_id, active_only=True)
        for token in tokens:
            token.revoke(reason)
            db.add(token)
        db.commit()
        return len(tokens)
    
    def rotate_token(
        self,
        db: Session,
        *,
        plain_token: str,
        expires_in_days: int = 7,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Tuple[RefreshTokenModel, str]]:
        """
        Rotate refresh token.
        
        Revokes old token and creates new one with link to previous.
        
        Returns:
            Tuple of (new RefreshTokenModel, new plain_token) or None if invalid
        """
        old_token = self.validate_token(db, plain_token=plain_token)
        if not old_token:
            return None
        
        # Revoke old token
        old_token.revoke("rotation")
        db.add(old_token)
        
        # Create new token
        new_token, new_plain = self.create_token(
            db,
            user_id=old_token.user_id,
            expires_in_days=expires_in_days,
            device_info=device_info or old_token.device_info,
            ip_address=ip_address or old_token.ip_address,
            previous_token_id=old_token.id,
        )
        
        return new_token, new_plain
    
    def cleanup_expired(self, db: Session) -> int:
        """
        Delete expired tokens.
        
        Returns:
            Number of deleted tokens
        """
        deleted = db.query(RefreshTokenModel).filter(
            RefreshTokenModel.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        return deleted
    
    def cleanup_revoked(
        self,
        db: Session,
        *,
        older_than_days: int = 30,
    ) -> int:
        """
        Delete revoked tokens older than specified days.
        
        Returns:
            Number of deleted tokens
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        deleted = db.query(RefreshTokenModel).filter(
            RefreshTokenModel.revoked_at.isnot(None),
            RefreshTokenModel.revoked_at < cutoff,
        ).delete()
        db.commit()
        return deleted
    
    def get_active_session_count(self, db: Session, *, user_id: str) -> int:
        """Get count of active sessions (tokens) for a user."""
        return db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.utcnow(),
        ).count()
    
    # ==========================================================================
    # Asynchronous Operations
    # ==========================================================================
    
    async def create_token_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        expires_in_days: int = 7,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        previous_token_id: Optional[str] = None,
    ) -> Tuple[RefreshTokenModel, str]:
        """Create new refresh token (async)."""
        token_model, plain_token = RefreshTokenModel.create_token(
            user_id=user_id,
            expires_in_days=expires_in_days,
            device_info=device_info,
            ip_address=ip_address,
            previous_token_id=previous_token_id,
        )
        
        db.add(token_model)
        await db.commit()
        await db.refresh(token_model)
        
        return token_model, plain_token
    
    async def get_by_token_async(
        self,
        db: AsyncSession,
        *,
        plain_token: str,
    ) -> Optional[RefreshTokenModel]:
        """Get refresh token by plain token string (async)."""
        token_hash = RefreshTokenModel.hash_token(plain_token)
        result = await db.execute(
            select(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
    
    async def validate_token_async(
        self,
        db: AsyncSession,
        *,
        plain_token: str,
    ) -> Optional[RefreshTokenModel]:
        """Validate refresh token (async)."""
        token = await self.get_by_token_async(db, plain_token=plain_token)
        if token and token.is_valid:
            return token
        return None
    
    async def revoke_token_async(
        self,
        db: AsyncSession,
        *,
        plain_token: str,
        reason: str = "manual",
    ) -> Optional[RefreshTokenModel]:
        """Revoke a specific token (async)."""
        token = await self.get_by_token_async(db, plain_token=plain_token)
        if token:
            token.revoke(reason)
            db.add(token)
            await db.commit()
            await db.refresh(token)
        return token
    
    async def revoke_all_user_tokens_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        reason: str = "logout_all",
    ) -> int:
        """Revoke all tokens for a user (async)."""
        result = await db.execute(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
                RefreshTokenModel.expires_at > datetime.utcnow(),
            )
        )
        tokens = result.scalars().all()
        
        for token in tokens:
            token.revoke(reason)
            db.add(token)
        
        await db.commit()
        return len(tokens)
    
    async def rotate_token_async(
        self,
        db: AsyncSession,
        *,
        plain_token: str,
        expires_in_days: int = 7,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Tuple[RefreshTokenModel, str]]:
        """Rotate refresh token (async)."""
        old_token = await self.validate_token_async(db, plain_token=plain_token)
        if not old_token:
            return None
        
        # Revoke old token
        old_token.revoke("rotation")
        db.add(old_token)
        
        # Create new token
        new_token, new_plain = await self.create_token_async(
            db,
            user_id=old_token.user_id,
            expires_in_days=expires_in_days,
            device_info=device_info or old_token.device_info,
            ip_address=ip_address or old_token.ip_address,
            previous_token_id=old_token.id,
        )
        
        return new_token, new_plain


# Global CRUD instance
crud_refresh_token = CRUDRefreshToken(RefreshTokenModel)


"""
Audit Log CRUD Operations

Specialized CRUD operations for audit logging.
Provides immutable audit trail management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.audit_log import AuditLogModel, AuditAction


class AuditLogCreate(BaseModel):
    """Schema for audit log creation."""
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CRUDAudit(CRUDBase[AuditLogModel, AuditLogCreate, BaseModel]):
    """
    Audit log CRUD operations.
    
    Note: Audit logs are immutable - no update/delete operations.
    """
    
    # ==========================================================================
    # Synchronous Operations
    # ==========================================================================
    
    def create_log(
        self,
        db: Session,
        *,
        action: Union[AuditAction, str],
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLogModel:
        """
        Create audit log entry.
        
        This is the primary method for logging actions.
        """
        action_str = action.value if isinstance(action, AuditAction) else action
        
        log = AuditLogModel(
            action=action_str,
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
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    def get_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get audit logs for a specific user."""
        return db.query(AuditLogModel).filter(
            AuditLogModel.user_id == user_id
        ).order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_resource(
        self,
        db: Session,
        *,
        resource_type: str,
        resource_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get audit logs for a specific resource."""
        query = db.query(AuditLogModel).filter(
            AuditLogModel.resource_type == resource_type
        )
        if resource_id:
            query = query.filter(AuditLogModel.resource_id == resource_id)
        
        return query.order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_action(
        self,
        db: Session,
        *,
        action: Union[AuditAction, str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get audit logs for a specific action type."""
        action_str = action.value if isinstance(action, AuditAction) else action
        return db.query(AuditLogModel).filter(
            AuditLogModel.action == action_str
        ).order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_date_range(
        self,
        db: Session,
        *,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get audit logs within a date range."""
        return db.query(AuditLogModel).filter(
            and_(
                AuditLogModel.timestamp >= start_date,
                AuditLogModel.timestamp <= end_date,
            )
        ).order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def filter_logs(
        self,
        db: Session,
        *,
        filters: AuditLogFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[AuditLogModel], int]:
        """
        Filter audit logs with multiple criteria.
        
        Returns:
            tuple: (list of logs, total count)
        """
        query = db.query(AuditLogModel)
        count_query = db.query(func.count(AuditLogModel.id))
        
        # Apply filters
        conditions = []
        if filters.user_id:
            conditions.append(AuditLogModel.user_id == filters.user_id)
        if filters.user_email:
            conditions.append(AuditLogModel.user_email.ilike(f"%{filters.user_email}%"))
        if filters.action:
            conditions.append(AuditLogModel.action == filters.action)
        if filters.resource_type:
            conditions.append(AuditLogModel.resource_type == filters.resource_type)
        if filters.resource_id:
            conditions.append(AuditLogModel.resource_id == filters.resource_id)
        if filters.success is not None:
            conditions.append(AuditLogModel.success == filters.success)
        if filters.start_date:
            conditions.append(AuditLogModel.timestamp >= filters.start_date)
        if filters.end_date:
            conditions.append(AuditLogModel.timestamp <= filters.end_date)
        
        if conditions:
            query = query.filter(and_(*conditions))
            count_query = count_query.filter(and_(*conditions))
        
        total = count_query.scalar() or 0
        logs = query.order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
        
        return logs, total
    
    def get_recent_activity(
        self,
        db: Session,
        *,
        hours: int = 24,
        limit: int = 50,
    ) -> List[AuditLogModel]:
        """Get recent activity within specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return db.query(AuditLogModel).filter(
            AuditLogModel.timestamp >= cutoff
        ).order_by(
            AuditLogModel.timestamp.desc()
        ).limit(limit).all()
    
    def get_failed_actions(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get all failed actions."""
        return db.query(AuditLogModel).filter(
            AuditLogModel.success == False
        ).order_by(
            AuditLogModel.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_stats(
        self,
        db: Session,
        *,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total count
        total = db.query(func.count(AuditLogModel.id)).filter(
            AuditLogModel.timestamp >= cutoff
        ).scalar() or 0
        
        # Count by action
        action_counts = db.query(
            AuditLogModel.action,
            func.count(AuditLogModel.id)
        ).filter(
            AuditLogModel.timestamp >= cutoff
        ).group_by(AuditLogModel.action).all()
        
        # Count by resource type
        resource_counts = db.query(
            AuditLogModel.resource_type,
            func.count(AuditLogModel.id)
        ).filter(
            AuditLogModel.timestamp >= cutoff
        ).group_by(AuditLogModel.resource_type).all()
        
        # Success rate
        success_count = db.query(func.count(AuditLogModel.id)).filter(
            AuditLogModel.timestamp >= cutoff,
            AuditLogModel.success == True
        ).scalar() or 0
        
        return {
            "total_events": total,
            "success_rate": (success_count / total * 100) if total > 0 else 100,
            "by_action": dict(action_counts),
            "by_resource": dict(resource_counts),
            "period_days": days,
        }
    
    def cleanup_old_logs(
        self,
        db: Session,
        *,
        days: int = 90,
    ) -> int:
        """
        Delete logs older than specified days.
        
        Returns:
            Number of deleted records
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(AuditLogModel).filter(
            AuditLogModel.timestamp < cutoff
        ).delete()
        db.commit()
        return deleted
    
    # ==========================================================================
    # Asynchronous Operations
    # ==========================================================================
    
    async def create_log_async(
        self,
        db: AsyncSession,
        *,
        action: Union[AuditAction, str],
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLogModel:
        """Create audit log entry (async)."""
        action_str = action.value if isinstance(action, AuditAction) else action
        
        log = AuditLogModel(
            action=action_str,
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
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
    
    async def get_by_user_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get audit logs for a specific user (async)."""
        result = await db.execute(
            select(AuditLogModel)
            .where(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def filter_logs_async(
        self,
        db: AsyncSession,
        *,
        filters: AuditLogFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[AuditLogModel], int]:
        """Filter audit logs (async)."""
        stmt = select(AuditLogModel)
        count_stmt = select(func.count()).select_from(AuditLogModel)
        
        conditions = []
        if filters.user_id:
            conditions.append(AuditLogModel.user_id == filters.user_id)
        if filters.user_email:
            conditions.append(AuditLogModel.user_email.ilike(f"%{filters.user_email}%"))
        if filters.action:
            conditions.append(AuditLogModel.action == filters.action)
        if filters.resource_type:
            conditions.append(AuditLogModel.resource_type == filters.resource_type)
        if filters.resource_id:
            conditions.append(AuditLogModel.resource_id == filters.resource_id)
        if filters.success is not None:
            conditions.append(AuditLogModel.success == filters.success)
        if filters.start_date:
            conditions.append(AuditLogModel.timestamp >= filters.start_date)
        if filters.end_date:
            conditions.append(AuditLogModel.timestamp <= filters.end_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(AuditLogModel.timestamp.desc()).offset(skip).limit(limit)
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        result = await db.execute(stmt)
        logs = list(result.scalars().all())
        
        return logs, total


# Global CRUD instance
crud_audit = CRUDAudit(AuditLogModel)


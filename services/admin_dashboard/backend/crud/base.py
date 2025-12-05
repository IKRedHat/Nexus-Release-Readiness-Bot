"""
Base CRUD Operations

Generic CRUD class that provides common database operations.
Inherit from this class for model-specific CRUD implementations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import Base

# Type variables for generic typing
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD operations base class.
    
    Provides common database operations that can be inherited
    and customized for specific models.
    
    Type Parameters:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for creation
        UpdateSchemaType: Pydantic schema for updates
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD with model class.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    # ==========================================================================
    # Synchronous Operations
    # ==========================================================================
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
            descending: Whether to order descending
            
        Returns:
            List of model instances
        """
        query = db.query(self.model)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            query = query.order_by(column.desc() if descending else column)
        
        return query.offset(skip).limit(limit).all()
    
    def get_count(self, db: Session) -> int:
        """Get total count of records."""
        return db.query(func.count(self.model.id)).scalar() or 0
    
    def create(self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create new record.
        
        Args:
            db: Database session
            obj_in: Creation data (Pydantic schema or dict)
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Update data (Pydantic schema or dict)
            
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Delete record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Deleted model instance or None
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def exists(self, db: Session, id: Any) -> bool:
        """Check if record exists."""
        return db.query(self.model).filter(self.model.id == id).first() is not None
    
    # ==========================================================================
    # Asynchronous Operations
    # ==========================================================================
    
    async def get_async(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get single record by ID (async).
        
        Args:
            db: Async database session
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination (async).
        
        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
            descending: Whether to order descending
            
        Returns:
            List of model instances
        """
        stmt = select(self.model)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            stmt = stmt.order_by(column.desc() if descending else column)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_count_async(self, db: AsyncSession) -> int:
        """Get total count of records (async)."""
        result = await db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0
    
    async def create_async(
        self,
        db: AsyncSession,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Create new record (async).
        
        Args:
            db: Async database session
            obj_in: Creation data (Pydantic schema or dict)
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_async(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update existing record (async).
        
        Args:
            db: Async database session
            db_obj: Existing model instance
            obj_in: Update data (Pydantic schema or dict)
            
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove_async(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Delete record by ID (async).
        
        Args:
            db: Async database session
            id: Record ID
            
        Returns:
            Deleted model instance or None
        """
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def exists_async(self, db: AsyncSession, id: Any) -> bool:
        """Check if record exists (async)."""
        result = await db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None


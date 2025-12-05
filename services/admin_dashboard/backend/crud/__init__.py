"""
Nexus Admin Dashboard - CRUD Operations

This module provides database CRUD (Create, Read, Update, Delete) operations
for all models with both synchronous and asynchronous support.
"""

from crud.base import CRUDBase
from crud.user import crud_user, CRUDUser
from crud.role import crud_role, CRUDRole
from crud.audit_log import crud_audit, CRUDAudit
from crud.refresh_token import crud_refresh_token, CRUDRefreshToken

__all__ = [
    "CRUDBase",
    "crud_user",
    "CRUDUser",
    "crud_role",
    "CRUDRole",
    "crud_audit",
    "CRUDAudit",
    "crud_refresh_token",
    "CRUDRefreshToken",
]


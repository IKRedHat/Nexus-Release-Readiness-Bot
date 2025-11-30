"""
Tenant Repository
Storage and retrieval of tenant data
"""
import os
import json
import logging
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

from .tenant import Tenant, TenantStatus, TenantPlan, TenantLimits, TenantConfig

logger = logging.getLogger("nexus.multitenancy.repository")


class TenantRepository:
    """
    Repository for tenant CRUD operations
    
    Supports multiple backends:
    - Memory (default, for development)
    - File-based (for simple deployments)
    - PostgreSQL (for production)
    - Redis (for distributed caching)
    """
    
    def __init__(self, backend: str = "memory"):
        self.backend = backend
        self._memory_store: Dict[str, Tenant] = {}
        self._slug_index: Dict[str, str] = {}  # slug -> id
        self._api_key_index: Dict[str, str] = {}  # api_key -> id
        
        # Initialize with default tenant in memory mode
        if backend == "memory":
            self._init_default_tenant()
    
    def _init_default_tenant(self):
        """Create default tenant for development"""
        default_tenant = Tenant(
            id="default",
            name="Default Organization",
            slug="default",
            status=TenantStatus.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
            owner_email="admin@example.com",
            owner_name="Admin User",
            limits=TenantLimits.for_plan(TenantPlan.ENTERPRISE),
            config=TenantConfig(
                features={
                    "react_engine": True,
                    "vector_memory": True,
                    "hygiene_agent": True,
                    "slack_integration": True,
                    "confluence_reports": True,
                    "ai_recommendations": True,
                }
            ),
        )
        self._memory_store[default_tenant.id] = default_tenant
        self._slug_index[default_tenant.slug] = default_tenant.id
    
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        if self.backend == "memory":
            return self._memory_store.get(tenant_id)
        
        # TODO: Implement database lookup
        return None
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        if self.backend == "memory":
            tenant_id = self._slug_index.get(slug)
            if tenant_id:
                return self._memory_store.get(tenant_id)
            return None
        
        # TODO: Implement database lookup
        return None
    
    async def get_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        if self.backend == "memory":
            tenant_id = self._api_key_index.get(api_key)
            if tenant_id:
                return self._memory_store.get(tenant_id)
            return None
        
        # TODO: Implement database lookup
        return None
    
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant"""
        if self.backend == "memory":
            # Validate slug uniqueness
            if tenant.slug in self._slug_index:
                raise ValueError(f"Tenant with slug '{tenant.slug}' already exists")
            
            self._memory_store[tenant.id] = tenant
            self._slug_index[tenant.slug] = tenant.id
            
            logger.info(f"Created tenant: {tenant.slug} (id={tenant.id})")
            return tenant
        
        # TODO: Implement database insert
        return tenant
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update an existing tenant"""
        tenant.updated_at = datetime.utcnow()
        
        if self.backend == "memory":
            if tenant.id not in self._memory_store:
                raise ValueError(f"Tenant with id '{tenant.id}' not found")
            
            # Update slug index if changed
            old_tenant = self._memory_store[tenant.id]
            if old_tenant.slug != tenant.slug:
                del self._slug_index[old_tenant.slug]
                self._slug_index[tenant.slug] = tenant.id
            
            self._memory_store[tenant.id] = tenant
            
            logger.info(f"Updated tenant: {tenant.slug}")
            return tenant
        
        # TODO: Implement database update
        return tenant
    
    async def delete(self, tenant_id: str, soft: bool = True) -> bool:
        """Delete a tenant"""
        if self.backend == "memory":
            if tenant_id not in self._memory_store:
                return False
            
            tenant = self._memory_store[tenant_id]
            
            if soft:
                # Soft delete
                tenant.status = TenantStatus.DELETED
                tenant.deleted_at = datetime.utcnow()
                tenant.updated_at = datetime.utcnow()
            else:
                # Hard delete
                del self._memory_store[tenant_id]
                del self._slug_index[tenant.slug]
            
            logger.info(f"Deleted tenant: {tenant.slug} (soft={soft})")
            return True
        
        # TODO: Implement database delete
        return False
    
    async def list_all(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Tenant]:
        """List all tenants with optional filters"""
        if self.backend == "memory":
            tenants = list(self._memory_store.values())
            
            # Apply filters
            if status:
                tenants = [t for t in tenants if t.status == status]
            if plan:
                tenants = [t for t in tenants if t.plan == plan]
            
            # Apply pagination
            return tenants[offset:offset + limit]
        
        # TODO: Implement database query
        return []
    
    async def count(
        self,
        status: Optional[TenantStatus] = None,
    ) -> int:
        """Count tenants"""
        if self.backend == "memory":
            tenants = list(self._memory_store.values())
            if status:
                tenants = [t for t in tenants if t.status == status]
            return len(tenants)
        
        # TODO: Implement database count
        return 0
    
    async def set_api_key(self, tenant_id: str, api_key: str) -> bool:
        """Set API key for a tenant"""
        if self.backend == "memory":
            if tenant_id not in self._memory_store:
                return False
            
            # Remove old API key if exists
            old_keys = [k for k, v in self._api_key_index.items() if v == tenant_id]
            for key in old_keys:
                del self._api_key_index[key]
            
            # Set new API key
            self._api_key_index[api_key] = tenant_id
            return True
        
        # TODO: Implement database update
        return False


# Singleton instance
_repository: Optional[TenantRepository] = None


def get_tenant_repository() -> TenantRepository:
    """Get the tenant repository singleton"""
    global _repository
    if _repository is None:
        backend = os.environ.get("TENANT_STORAGE_BACKEND", "memory")
        _repository = TenantRepository(backend=backend)
    return _repository


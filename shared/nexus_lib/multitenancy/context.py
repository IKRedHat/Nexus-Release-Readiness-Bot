"""
Tenant Context Management
Request-scoped tenant context using contextvars
"""
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any

from .tenant import Tenant

logger = logging.getLogger("nexus.multitenancy")

# Context variable for current tenant
_current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)


class TenantContext:
    """
    Tenant context manager for request-scoped tenant isolation
    
    Usage:
        async with TenantContext(tenant):
            # All code here runs in tenant context
            current = get_current_tenant()
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self._token = None
    
    def __enter__(self):
        self._token = _current_tenant.set(self.tenant)
        logger.debug(f"Entered tenant context: {self.tenant.slug}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _current_tenant.reset(self._token)
        logger.debug(f"Exited tenant context: {self.tenant.slug}")
        return False
    
    async def __aenter__(self):
        self._token = _current_tenant.set(self.tenant)
        logger.debug(f"Entered async tenant context: {self.tenant.slug}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        _current_tenant.reset(self._token)
        logger.debug(f"Exited async tenant context: {self.tenant.slug}")
        return False


def get_current_tenant() -> Optional[Tenant]:
    """
    Get the current tenant from context
    
    Returns:
        Current tenant or None if not in tenant context
    """
    return _current_tenant.get()


def set_current_tenant(tenant: Optional[Tenant]) -> None:
    """
    Set the current tenant in context
    
    Args:
        tenant: Tenant to set as current
    """
    _current_tenant.set(tenant)


def require_tenant() -> Tenant:
    """
    Get the current tenant, raising if not available
    
    Returns:
        Current tenant
    
    Raises:
        RuntimeError: If not in tenant context
    """
    tenant = get_current_tenant()
    if tenant is None:
        raise RuntimeError("No tenant in current context")
    return tenant


def get_tenant_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value for the current tenant
    
    Args:
        key: Configuration key
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    tenant = get_current_tenant()
    if tenant is None:
        return default
    
    # Check in config
    if hasattr(tenant.config, key):
        return getattr(tenant.config, key)
    
    # Check in metadata
    return tenant.metadata.get(key, default)


def tenant_has_feature(feature: str) -> bool:
    """
    Check if current tenant has a feature enabled
    
    Args:
        feature: Feature name
    
    Returns:
        True if feature is enabled
    """
    tenant = get_current_tenant()
    if tenant is None:
        return False
    return tenant.has_feature(feature)


def get_tenant_header() -> Dict[str, str]:
    """
    Get headers for inter-service communication with tenant info
    
    Returns:
        Headers dict with tenant information
    """
    tenant = get_current_tenant()
    if tenant is None:
        return {}
    
    return {
        "X-Tenant-ID": tenant.id,
        "X-Tenant-Slug": tenant.slug,
    }


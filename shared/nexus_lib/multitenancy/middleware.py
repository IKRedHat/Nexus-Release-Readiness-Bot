"""
Tenant Middleware
FastAPI middleware for tenant resolution and context management
"""
import logging
from typing import Optional, Callable, Awaitable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .tenant import Tenant, TenantStatus
from .context import set_current_tenant, get_current_tenant
from .repository import TenantRepository

logger = logging.getLogger("nexus.multitenancy.middleware")


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that resolves tenant from request and sets context
    
    Tenant can be resolved from:
    1. X-Tenant-ID header
    2. X-Tenant-Slug header
    3. Subdomain (e.g., acme.nexus.example.com)
    4. Path prefix (e.g., /t/acme/...)
    5. API key association
    """
    
    def __init__(
        self,
        app,
        repository: Optional[TenantRepository] = None,
        require_tenant: bool = False,
        exclude_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.repository = repository or TenantRepository()
        self.require_tenant = require_tenant
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with tenant context"""
        # Skip tenant resolution for excluded paths
        path = request.url.path
        if any(path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)
        
        # Try to resolve tenant
        tenant = await self._resolve_tenant(request)
        
        if tenant is None and self.require_tenant:
            raise HTTPException(
                status_code=401,
                detail="Tenant not found. Please provide X-Tenant-ID or X-Tenant-Slug header."
            )
        
        if tenant:
            # Validate tenant status
            if not tenant.is_active():
                raise HTTPException(
                    status_code=403,
                    detail=f"Tenant is {tenant.status.value}. Access denied."
                )
            
            # Set tenant in context
            set_current_tenant(tenant)
            
            # Add tenant info to request state
            request.state.tenant = tenant
            request.state.tenant_id = tenant.id
            request.state.tenant_slug = tenant.slug
        
        try:
            response = await call_next(request)
            
            # Add tenant info to response headers
            if tenant:
                response.headers["X-Tenant-ID"] = tenant.id
            
            return response
            
        finally:
            # Clear tenant context
            set_current_tenant(None)
    
    async def _resolve_tenant(self, request: Request) -> Optional[Tenant]:
        """Resolve tenant from request"""
        
        # 1. Try X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            tenant = await self.repository.get_by_id(tenant_id)
            if tenant:
                logger.debug(f"Resolved tenant from ID header: {tenant.slug}")
                return tenant
        
        # 2. Try X-Tenant-Slug header
        tenant_slug = request.headers.get("X-Tenant-Slug")
        if tenant_slug:
            tenant = await self.repository.get_by_slug(tenant_slug)
            if tenant:
                logger.debug(f"Resolved tenant from slug header: {tenant.slug}")
                return tenant
        
        # 3. Try subdomain
        host = request.headers.get("host", "")
        if host and "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "localhost"]:
                tenant = await self.repository.get_by_slug(subdomain)
                if tenant:
                    logger.debug(f"Resolved tenant from subdomain: {tenant.slug}")
                    return tenant
        
        # 4. Try path prefix (/t/{slug}/...)
        path = request.url.path
        if path.startswith("/t/"):
            parts = path.split("/")
            if len(parts) >= 3:
                slug = parts[2]
                tenant = await self.repository.get_by_slug(slug)
                if tenant:
                    logger.debug(f"Resolved tenant from path: {tenant.slug}")
                    return tenant
        
        # 5. Try API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            tenant = await self.repository.get_by_api_key(api_key)
            if tenant:
                logger.debug(f"Resolved tenant from API key: {tenant.slug}")
                return tenant
        
        return None


def get_tenant_from_request(request: Request) -> Optional[Tenant]:
    """
    Get tenant from request state
    
    Args:
        request: FastAPI request
    
    Returns:
        Tenant if available
    """
    return getattr(request.state, "tenant", None)


def require_active_tenant(request: Request) -> Tenant:
    """
    FastAPI dependency that requires an active tenant
    
    Usage:
        @app.get("/api/data")
        async def get_data(tenant: Tenant = Depends(require_active_tenant)):
            ...
    """
    tenant = get_tenant_from_request(request)
    if tenant is None:
        raise HTTPException(
            status_code=401,
            detail="Tenant required"
        )
    if not tenant.is_active():
        raise HTTPException(
            status_code=403,
            detail=f"Tenant is {tenant.status.value}"
        )
    return tenant


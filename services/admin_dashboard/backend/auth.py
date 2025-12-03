"""
SSO and RBAC Authentication Module for Nexus Admin Dashboard

Provides:
- OAuth2/OIDC SSO integration (Okta, Azure AD, Google, GitHub)
- JWT token management
- Role-based access control
- Permission checking middleware
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from functools import wraps

import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, HTTPBearer
from pydantic import BaseModel

from nexus_lib.schemas.rbac import (
    User, UserCreate, UserUpdate, UserWithPermissions,
    Role, RoleCreate, RoleUpdate,
    Permission, ROLE_TEMPLATES,
    SSOProvider, UserStatus,
    TokenPayload, AuthToken,
    AuditLog, AuditAction,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

class AuthConfig:
    """Authentication configuration"""
    
    # JWT Settings
    SECRET_KEY = os.getenv("NEXUS_JWT_SECRET", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("NEXUS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("NEXUS_REFRESH_TOKEN_DAYS", "7"))
    
    # SSO Provider Settings
    SSO_PROVIDER = os.getenv("NEXUS_SSO_PROVIDER", "local")  # okta, azure_ad, google, github, local
    
    # Okta
    OKTA_DOMAIN = os.getenv("OKTA_DOMAIN", "")
    OKTA_CLIENT_ID = os.getenv("OKTA_CLIENT_ID", "")
    OKTA_CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET", "")
    
    # Azure AD
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    
    # Google
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # GitHub
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    
    # App URLs
    FRONTEND_URL = os.getenv("NEXUS_FRONTEND_URL", "http://localhost:5173")
    BACKEND_URL = os.getenv("NEXUS_BACKEND_URL", "http://localhost:8088")
    
    # Default admin
    DEFAULT_ADMIN_EMAIL = os.getenv("NEXUS_ADMIN_EMAIL", "admin@nexus.local")


# =============================================================================
# IN-MEMORY STORAGE (Replace with Redis/PostgreSQL in production)
# =============================================================================

class RBACStore:
    """In-memory RBAC store - replace with database in production"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.audit_logs: List[AuditLog] = []
        self.refresh_tokens: Dict[str, str] = {}  # token -> user_id
        
        # Initialize default roles
        self._init_default_roles()
        
        # Create default admin user
        self._init_admin_user()
    
    def _init_default_roles(self):
        """Initialize predefined roles"""
        for role_id, permissions in ROLE_TEMPLATES.items():
            self.roles[role_id] = Role(
                id=role_id,
                name=role_id.replace("_", " ").title(),
                description=f"Predefined {role_id} role",
                permissions={str(p.value) if hasattr(p, 'value') else str(p) for p in permissions},
                is_system_role=True,
                created_by="system",
            )
    
    def _init_admin_user(self):
        """Create default admin user"""
        admin_id = "admin-001"
        self.users[admin_id] = User(
            id=admin_id,
            email=AuthConfig.DEFAULT_ADMIN_EMAIL,
            name="System Administrator",
            roles=["admin"],
            status=UserStatus.ACTIVE,
            sso_provider=SSOProvider.LOCAL,
        )


# Global store instance
rbac_store = RBACStore()


# =============================================================================
# JWT TOKEN MANAGEMENT
# =============================================================================

oauth2_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: User, roles: List[Role]) -> str:
    """Create JWT access token"""
    # Compute all permissions from roles
    permissions = set()
    for role in roles:
        permissions.update(role.permissions)
        # Handle role inheritance
        if role.parent_role_id and role.parent_role_id in rbac_store.roles:
            parent = rbac_store.roles[role.parent_role_id]
            permissions.update(parent.permissions)
    
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "permissions": list(permissions),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iss": "nexus-admin",
    }
    
    return jwt.encode(payload, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create refresh token"""
    token = secrets.token_urlsafe(64)
    rbac_store.refresh_tokens[token] = user_id
    return token


def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# SSO PROVIDERS
# =============================================================================

class SSOHandler:
    """Base SSO handler"""
    
    @staticmethod
    async def get_authorization_url(provider: SSOProvider, state: str) -> str:
        """Get OAuth2 authorization URL"""
        redirect_uri = f"{AuthConfig.BACKEND_URL}/auth/callback/{provider.value}"
        
        if provider == SSOProvider.OKTA:
            return (
                f"https://{AuthConfig.OKTA_DOMAIN}/oauth2/default/v1/authorize"
                f"?client_id={AuthConfig.OKTA_CLIENT_ID}"
                f"&response_type=code"
                f"&scope=openid%20email%20profile"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
        
        elif provider == SSOProvider.AZURE_AD:
            return (
                f"https://login.microsoftonline.com/{AuthConfig.AZURE_TENANT_ID}/oauth2/v2.0/authorize"
                f"?client_id={AuthConfig.AZURE_CLIENT_ID}"
                f"&response_type=code"
                f"&scope=openid%20email%20profile"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
        
        elif provider == SSOProvider.GOOGLE:
            return (
                f"https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={AuthConfig.GOOGLE_CLIENT_ID}"
                f"&response_type=code"
                f"&scope=openid%20email%20profile"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
        
        elif provider == SSOProvider.GITHUB:
            return (
                f"https://github.com/login/oauth/authorize"
                f"?client_id={AuthConfig.GITHUB_CLIENT_ID}"
                f"&scope=user:email"
                f"&redirect_uri={redirect_uri}"
                f"&state={state}"
            )
        
        raise ValueError(f"Unsupported SSO provider: {provider}")
    
    @staticmethod
    async def exchange_code(provider: SSOProvider, code: str) -> dict:
        """Exchange authorization code for tokens"""
        redirect_uri = f"{AuthConfig.BACKEND_URL}/auth/callback/{provider.value}"
        
        async with httpx.AsyncClient() as client:
            if provider == SSOProvider.OKTA:
                response = await client.post(
                    f"https://{AuthConfig.OKTA_DOMAIN}/oauth2/default/v1/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": AuthConfig.OKTA_CLIENT_ID,
                        "client_secret": AuthConfig.OKTA_CLIENT_SECRET,
                    },
                )
            
            elif provider == SSOProvider.AZURE_AD:
                response = await client.post(
                    f"https://login.microsoftonline.com/{AuthConfig.AZURE_TENANT_ID}/oauth2/v2.0/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": AuthConfig.AZURE_CLIENT_ID,
                        "client_secret": AuthConfig.AZURE_CLIENT_SECRET,
                    },
                )
            
            elif provider == SSOProvider.GOOGLE:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": AuthConfig.GOOGLE_CLIENT_ID,
                        "client_secret": AuthConfig.GOOGLE_CLIENT_SECRET,
                    },
                )
            
            elif provider == SSOProvider.GITHUB:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": AuthConfig.GITHUB_CLIENT_ID,
                        "client_secret": AuthConfig.GITHUB_CLIENT_SECRET,
                    },
                )
            
            else:
                raise ValueError(f"Unsupported SSO provider: {provider}")
            
            return response.json()
    
    @staticmethod
    async def get_user_info(provider: SSOProvider, access_token: str) -> dict:
        """Get user info from SSO provider"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            if provider == SSOProvider.OKTA:
                response = await client.get(
                    f"https://{AuthConfig.OKTA_DOMAIN}/oauth2/default/v1/userinfo",
                    headers=headers,
                )
            
            elif provider == SSOProvider.AZURE_AD:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers=headers,
                )
            
            elif provider == SSOProvider.GOOGLE:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=headers,
                )
            
            elif provider == SSOProvider.GITHUB:
                response = await client.get(
                    "https://api.github.com/user",
                    headers=headers,
                )
                user_data = response.json()
                
                # GitHub requires separate call for email
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers=headers,
                )
                emails = email_response.json()
                primary_email = next((e["email"] for e in emails if e["primary"]), None)
                user_data["email"] = primary_email
                return user_data
            
            else:
                raise ValueError(f"Unsupported SSO provider: {provider}")
            
            return response.json()


# =============================================================================
# RBAC SERVICE
# =============================================================================

class RBACService:
    """Service for managing RBAC operations"""
    
    # -------------------------------------------------------------------------
    # User Management
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_user(user_id: str) -> Optional[User]:
        """Get user by ID"""
        return rbac_store.users.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        for user in rbac_store.users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    @staticmethod
    def create_user(data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create a new user"""
        user_id = f"user-{secrets.token_hex(8)}"
        
        # Assign default role if none specified
        roles = data.roles if data.roles else ["viewer"]
        
        user = User(
            id=user_id,
            email=data.email,
            name=data.name,
            roles=roles,
            department=data.department,
            title=data.title,
            sso_provider=data.sso_provider,
        )
        
        rbac_store.users[user_id] = user
        return user
    
    @staticmethod
    def update_user(user_id: str, data: UserUpdate) -> Optional[User]:
        """Update a user"""
        user = rbac_store.users.get(user_id)
        if not user:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        rbac_store.users[user_id] = user
        return user
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete a user"""
        if user_id in rbac_store.users:
            del rbac_store.users[user_id]
            return True
        return False
    
    @staticmethod
    def list_users() -> List[User]:
        """List all users"""
        return list(rbac_store.users.values())
    
    @staticmethod
    def get_user_with_permissions(user: User) -> UserWithPermissions:
        """Get user with computed permissions"""
        permissions = set()
        is_admin = False
        
        for role_id in user.roles:
            role = rbac_store.roles.get(role_id)
            if role:
                permissions.update(role.permissions)
                if role_id == "admin":
                    is_admin = True
                
                # Handle inheritance
                if role.parent_role_id:
                    parent = rbac_store.roles.get(role.parent_role_id)
                    if parent:
                        permissions.update(parent.permissions)
        
        return UserWithPermissions(
            **user.model_dump(),
            permissions=permissions,
            is_admin=is_admin,
        )
    
    # -------------------------------------------------------------------------
    # Role Management
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_role(role_id: str) -> Optional[Role]:
        """Get role by ID"""
        return rbac_store.roles.get(role_id)
    
    @staticmethod
    def create_role(data: RoleCreate, created_by: str) -> Role:
        """Create a new role"""
        role_id = data.name.lower().replace(" ", "_")
        
        # Ensure unique ID
        if role_id in rbac_store.roles:
            role_id = f"{role_id}-{secrets.token_hex(4)}"
        
        role = Role(
            id=role_id,
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            parent_role_id=data.parent_role_id,
            is_default=data.is_default,
            created_by=created_by,
        )
        
        rbac_store.roles[role_id] = role
        return role
    
    @staticmethod
    def update_role(role_id: str, data: RoleUpdate) -> Optional[Role]:
        """Update a role"""
        role = rbac_store.roles.get(role_id)
        if not role:
            return None
        
        # Prevent modifying system roles' core attributes
        if role.is_system_role and data.permissions is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify permissions of system roles",
            )
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role, key, value)
        
        role.updated_at = datetime.utcnow()
        rbac_store.roles[role_id] = role
        return role
    
    @staticmethod
    def delete_role(role_id: str) -> bool:
        """Delete a role"""
        role = rbac_store.roles.get(role_id)
        if not role:
            return False
        
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete system roles",
            )
        
        # Remove role from all users
        for user in rbac_store.users.values():
            if role_id in user.roles:
                user.roles.remove(role_id)
        
        del rbac_store.roles[role_id]
        return True
    
    @staticmethod
    def list_roles() -> List[Role]:
        """List all roles"""
        return list(rbac_store.roles.values())
    
    # -------------------------------------------------------------------------
    # Permission Checking
    # -------------------------------------------------------------------------
    
    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        """Check if user has a specific permission"""
        for role_id in user.roles:
            role = rbac_store.roles.get(role_id)
            if role and permission in role.permissions:
                return True
            
            # Check parent role
            if role and role.parent_role_id:
                parent = rbac_store.roles.get(role.parent_role_id)
                if parent and permission in parent.permissions:
                    return True
        
        return False
    
    @staticmethod
    def has_any_permission(user: User, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(RBACService.has_permission(user, p) for p in permissions)
    
    @staticmethod
    def has_all_permissions(user: User, permissions: List[str]) -> bool:
        """Check if user has all specified permissions"""
        return all(RBACService.has_permission(user, p) for p in permissions)
    
    # -------------------------------------------------------------------------
    # Audit Logging
    # -------------------------------------------------------------------------
    
    @staticmethod
    def log_action(
        user_id: str,
        user_email: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Dict = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log an auditable action"""
        log_entry = AuditLog(
            id=f"audit-{secrets.token_hex(8)}",
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        rbac_store.audit_logs.append(log_entry)
        
        # Keep only last 10000 entries (in production, use database)
        if len(rbac_store.audit_logs) > 10000:
            rbac_store.audit_logs = rbac_store.audit_logs[-10000:]
    
    @staticmethod
    def get_audit_logs(
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs with optional filters"""
        logs = rbac_store.audit_logs
        
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        
        if action:
            logs = [l for l in logs if l.action == action]
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPBearer] = Security(oauth2_scheme),
) -> UserWithPermissions:
    """Get current authenticated user from JWT token"""
    
    # Check for token in Authorization header
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    
    # Get user
    user = RBACService.get_user(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status}",
        )
    
    return RBACService.get_user_with_permissions(user)


def require_permission(*permissions: str):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: UserWithPermissions = Depends(get_current_user), **kwargs):
            if current_user.is_admin:
                return await func(*args, current_user=current_user, **kwargs)
            
            if not any(p in current_user.permissions for p in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {', '.join(permissions)}",
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def RequirePermission(*permissions: str):
    """Dependency for requiring permissions"""
    async def check_permission(current_user: UserWithPermissions = Depends(get_current_user)):
        if current_user.is_admin:
            return current_user
        
        if not any(p in current_user.permissions for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {', '.join(permissions)}",
            )
        
        return current_user
    
    return check_permission


# =============================================================================
# LOCAL AUTH (For Development)
# =============================================================================

class LocalAuthRequest(BaseModel):
    """Local authentication request"""
    email: str
    password: str


def verify_local_auth(email: str, password: str) -> Optional[User]:
    """Verify local authentication (for development)"""
    # In production, use proper password hashing
    # For now, accept any password for existing users
    user = RBACService.get_user_by_email(email)
    
    if not user:
        # Auto-create user in development mode
        if os.getenv("NEXUS_ENV", "development") == "development":
            user = RBACService.create_user(
                UserCreate(
                    email=email,
                    name=email.split("@")[0].replace(".", " ").title(),
                    roles=["admin"] if email == AuthConfig.DEFAULT_ADMIN_EMAIL else ["viewer"],
                )
            )
    
    return user


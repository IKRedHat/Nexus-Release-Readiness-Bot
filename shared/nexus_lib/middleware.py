"""
Nexus Middleware Components
JWT Authentication and Metrics Middleware for inter-service communication
"""
import os
import time
import logging
import jwt
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger("nexus.middleware")


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'agent_type']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'agent_type'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

HTTP_REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

HTTP_RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['agent_type']
)

# Error Metrics
HTTP_ERRORS_TOTAL = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type', 'agent_type']
)


# ============================================================================
# JWT AUTHENTICATION
# ============================================================================

class JWTConfig:
    """JWT Configuration"""
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        issuer: str = "nexus-orchestrator",
        audience: str = "nexus-agents"
    ):
        self.secret_key = secret_key or os.environ.get("NEXUS_JWT_SECRET", "nexus-dev-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.issuer = issuer
        self.audience = audience


class JWTHandler:
    """JWT Token Handler for creating and validating tokens"""
    
    def __init__(self, config: JWTConfig = None):
        self.config = config or JWTConfig()
    
    def create_access_token(
        self,
        subject: str,
        agent_type: str = None,
        additional_claims: dict = None,
        expires_delta: timedelta = None
    ) -> str:
        """Create a new JWT access token"""
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=self.config.access_token_expire_minutes)
        )
        
        payload = {
            "sub": subject,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if agent_type:
            payload["agent_type"] = agent_type
            
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_service_token(self, service_name: str, agent_type: str) -> str:
        """Create a long-lived service-to-service token"""
        return self.create_access_token(
            subject=service_name,
            agent_type=agent_type,
            expires_delta=timedelta(days=365),
            additional_claims={"service": True}
        )
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    def verify_token(self, token: str) -> bool:
        """Verify if a token is valid"""
        try:
            self.decode_token(token)
            return True
        except HTTPException:
            return False


class JWTBearer(HTTPBearer):
    """FastAPI dependency for JWT Bearer token authentication"""
    
    def __init__(
        self,
        jwt_handler: JWTHandler = None,
        required_agent_types: List[str] = None,
        auto_error: bool = True
    ):
        super().__init__(auto_error=auto_error)
        self.jwt_handler = jwt_handler or JWTHandler()
        self.required_agent_types = required_agent_types
    
    async def __call__(self, request: Request) -> Optional[dict]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(status_code=403, detail="Invalid authorization code")
            return None
        
        if credentials.scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            return None
        
        payload = self.jwt_handler.decode_token(credentials.credentials)
        
        # Check agent type if required
        if self.required_agent_types:
            agent_type = payload.get("agent_type")
            if agent_type not in self.required_agent_types:
                raise HTTPException(
                    status_code=403,
                    detail=f"Agent type '{agent_type}' not authorized for this endpoint"
                )
        
        # Attach payload to request state
        request.state.jwt_payload = payload
        return payload


def require_auth(agent_types: List[str] = None):
    """Decorator to require JWT authentication on routes"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# METRICS MIDDLEWARE
# ============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture HTTP request metrics
    - Request count by method, endpoint, status
    - Request latency histogram
    - Active request gauge
    - Error tracking
    """
    
    def __init__(self, app, agent_type: str = "unknown"):
        super().__init__(app)
        self.agent_type = agent_type
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics for health endpoints
        if request.url.path in ["/health", "/metrics", "/ready", "/live"]:
            return await call_next(request)
        
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Track active requests
        ACTIVE_REQUESTS.labels(agent_type=self.agent_type).inc()
        
        # Track request size
        content_length = request.headers.get("content-length")
        if content_length:
            HTTP_REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(int(content_length))
        
        start_time = time.perf_counter()
        status_code = 500
        error_type = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Track response size
            response_size = response.headers.get("content-length")
            if response_size:
                HTTP_RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(int(response_size))
            
            return response
            
        except Exception as e:
            error_type = type(e).__name__
            logger.exception(f"Request failed: {method} {endpoint}")
            raise
            
        finally:
            duration = time.perf_counter() - start_time
            
            # Record request count
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
                agent_type=self.agent_type
            ).inc()
            
            # Record latency
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                agent_type=self.agent_type
            ).observe(duration)
            
            # Track errors
            if status_code >= 400 or error_type:
                HTTP_ERRORS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type or f"http_{status_code}",
                    agent_type=self.agent_type
                ).inc()
            
            # Decrease active requests
            ACTIVE_REQUESTS.labels(agent_type=self.agent_type).dec()
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint paths to prevent high cardinality
        e.g., /users/123 -> /users/{id}
        """
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append("{id}")
            elif self._looks_like_uuid(part):
                normalized.append("{uuid}")
            elif self._looks_like_ticket_key(part):
                normalized.append("{ticket_key}")
            else:
                normalized.append(part)
        return "/".join(normalized)
    
    @staticmethod
    def _looks_like_uuid(s: str) -> bool:
        """Check if string looks like a UUID"""
        if len(s) == 36 and s.count("-") == 4:
            return all(c.isalnum() or c == "-" for c in s)
        return False
    
    @staticmethod
    def _looks_like_ticket_key(s: str) -> bool:
        """Check if string looks like a Jira ticket key (e.g., PROJ-123)"""
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2:
                return parts[0].isalpha() and parts[1].isdigit()
        return False


# ============================================================================
# AUTH MIDDLEWARE (Legacy compatibility)
# ============================================================================

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for validating JWT tokens
    Wraps the JWT validation logic for use as middleware
    """
    
    def __init__(
        self,
        app,
        secret_key: str = None,
        exclude_paths: List[str] = None,
        require_auth: bool = True
    ):
        super().__init__(app)
        self.jwt_handler = JWTHandler(JWTConfig(secret_key=secret_key))
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/ready", "/live", "/docs", "/openapi.json"]
        self.require_auth = require_auth
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Skip auth if not required (development mode)
        if not self.require_auth:
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # Allow requests without auth in development
            if os.environ.get("NEXUS_ENV", "development") == "development":
                logger.debug("No auth header, allowing in development mode")
                return await call_next(request)
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        # Extract and validate token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authorization scheme")
            
            payload = self.jwt_handler.decode_token(token)
            request.state.user = payload
            request.state.agent_type = payload.get("agent_type")
            
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        return await call_next(request)


# ============================================================================
# REQUEST ID MIDDLEWARE
# ============================================================================

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        import uuid
        
        # Use existing request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self._request_counts: dict = {}
        self._last_reset = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Reset counts every minute
        current_time = time.time()
        if current_time - self._last_reset > 60:
            self._request_counts = {}
            self._last_reset = current_time
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        count = self._request_counts.get(client_id, 0)
        if count >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        self._request_counts[client_id] = count + 1
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute - count - 1)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user from JWT
        if hasattr(request.state, "user"):
            return request.state.user.get("sub", "anonymous")
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

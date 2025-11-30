"""
Nexus Utility Functions
HTTP Client, Retry Logic, and Common Helpers
"""
import os
import logging
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any, List, TypeVar, Callable
from datetime import datetime, timezone
from functools import wraps

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

logger = logging.getLogger("nexus.utils")

T = TypeVar("T")


# ============================================================================
# ASYNC HTTP CLIENT WITH RETRY
# ============================================================================

class AsyncHttpClient:
    """
    Async HTTP client with built-in retry logic, circuit breaker pattern,
    and comprehensive error handling.
    """
    
    def __init__(
        self,
        base_url: str = "",
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        retry_min_wait: float = 1.0,
        retry_max_wait: float = 10.0,
        auth_token: Optional[str] = None
    ):
        """
        Initialize the HTTP client
        
        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            headers: Default headers for all requests
            max_retries: Maximum retry attempts
            retry_min_wait: Minimum wait between retries (seconds)
            retry_max_wait: Maximum wait between retries (seconds)
            auth_token: Optional JWT token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_min_wait = retry_min_wait
        self.retry_max_wait = retry_max_wait
        
        # Build headers
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Nexus-Agent/1.0"
        }
        if headers:
            default_headers.update(headers)
        if auth_token:
            default_headers["Authorization"] = f"Bearer {auth_token}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=default_headers,
            follow_redirects=True
        )
        
        self._closed = False
    
    def _create_retry_decorator(self):
        """Create tenacity retry decorator"""
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait,
                max=self.retry_max_wait
            ),
            retry=retry_if_exception_type((
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.ConnectError,
                httpx.RemoteProtocolError
            )),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
    
    async def request(
        self,
        method: str,
        endpoint: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (will be joined with base_url)
            json_body: JSON body for POST/PUT/PATCH
            params: Query parameters
            headers: Additional headers for this request
            timeout: Override timeout for this request
        
        Returns:
            Response as dictionary
        """
        if self._closed:
            raise RuntimeError("Client has been closed")
        
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        
        @self._create_retry_decorator()
        async def _make_request():
            request_kwargs = {
                "method": method.upper(),
                "url": url,
                "params": params,
                "headers": headers
            }
            
            if json_body is not None:
                request_kwargs["json"] = json_body
            
            if timeout:
                request_kwargs["timeout"] = timeout
            
            logger.debug(f"{method.upper()} {url} params={params}")
            
            response = await self.client.request(**request_kwargs)
            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {"status": "success", "data": None}
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": "success", "data": response.text}
        
        try:
            return await _make_request()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {
                "status": "error",
                "error": str(e),
                "status_code": e.response.status_code,
                "response": e.response.text[:500] if e.response.text else None
            }
        except RetryError as e:
            logger.error(f"Max retries exceeded: {e}")
            return {"status": "error", "error": "Max retries exceeded", "details": str(e)}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request"""
        return await self.request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self,
        endpoint: str,
        json_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request"""
        return await self.request("POST", endpoint, json_body=json_body, **kwargs)
    
    async def put(
        self,
        endpoint: str,
        json_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a PUT request"""
        return await self.request("PUT", endpoint, json_body=json_body, **kwargs)
    
    async def patch(
        self,
        endpoint: str,
        json_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a PATCH request"""
        return await self.request("PATCH", endpoint, json_body=json_body, **kwargs)
    
    async def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def close(self):
        """Close the HTTP client"""
        if not self._closed:
            await self.client.aclose()
            self._closed = True
            logger.debug("HTTP client closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ============================================================================
# SERVICE DISCOVERY / AGENT ROUTING
# ============================================================================

class AgentRegistry:
    """Registry for discovering and routing to agents"""
    
    def __init__(self):
        self._agents: Dict[str, str] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Load agent URLs from environment variables"""
        agent_mappings = {
            "jira": "JIRA_AGENT_URL",
            "git_ci": "GIT_CI_AGENT_URL",
            "slack": "SLACK_AGENT_URL",
            "reporting": "REPORTING_AGENT_URL",
            "scheduling": "SCHEDULING_AGENT_URL"
        }
        
        for agent_type, env_var in agent_mappings.items():
            url = os.environ.get(env_var)
            if url:
                self._agents[agent_type] = url
            else:
                # Default to kubernetes service discovery pattern
                self._agents[agent_type] = f"http://{agent_type.replace('_', '-')}-agent:8080"
    
    def get_url(self, agent_type: str) -> Optional[str]:
        """Get URL for an agent type"""
        return self._agents.get(agent_type)
    
    def register(self, agent_type: str, url: str):
        """Register an agent URL"""
        self._agents[agent_type] = url
    
    def list_agents(self) -> Dict[str, str]:
        """List all registered agents"""
        return self._agents.copy()


# Global registry instance
agent_registry = AgentRegistry()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_task_id(prefix: str = "task") -> str:
    """Generate a unique task ID"""
    import uuid
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique = uuid.uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{unique}"


def hash_content(content: str) -> str:
    """Generate SHA256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def parse_ticket_key(key: str) -> tuple:
    """
    Parse a Jira ticket key into project and number
    
    Args:
        key: Ticket key like "PROJ-123"
    
    Returns:
        Tuple of (project, number) or (None, None) if invalid
    """
    if "-" not in key:
        return None, None
    
    parts = key.rsplit("-", 1)
    if len(parts) != 2:
        return None, None
    
    project, number = parts
    try:
        return project, int(number)
    except ValueError:
        return None, None


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_get(d: Dict, *keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def merge_dicts(*dicts: Dict) -> Dict:
    """Deep merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if d:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
    return result


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


# ============================================================================
# ASYNC UTILITIES
# ============================================================================

async def gather_with_concurrency(
    n: int,
    *coros,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Run coroutines with limited concurrency
    
    Args:
        n: Maximum number of concurrent coroutines
        *coros: Coroutines to run
        return_exceptions: If True, return exceptions instead of raising
    
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(n)
    
    async def sem_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(
        *(sem_coro(c) for c in coros),
        return_exceptions=return_exceptions
    )


async def retry_async(
    func: Callable,
    *args,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = delay * (backoff ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_attempts} attempts failed")
    
    raise last_exception


# ============================================================================
# CACHING UTILITIES
# ============================================================================

class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, tuple] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now(timezone.utc).timestamp() < expires_at:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        ttl = ttl or self._default_ttl
        expires_at = datetime.now(timezone.utc).timestamp() + ttl
        self._cache[key] = (value, expires_at)
    
    def delete(self, key: str):
        """Delete value from cache"""
        self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cached values"""
        self._cache.clear()
    
    def cleanup(self):
        """Remove expired entries"""
        now = datetime.now(timezone.utc).timestamp()
        expired = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired:
            del self._cache[key]


# Global cache instance
cache = SimpleCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hash_content(":".join(key_parts))
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hash_content(":".join(key_parts))
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# DATE/TIME UTILITIES
# ============================================================================

def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def parse_iso_datetime(s: str) -> Optional[datetime]:
    """Parse ISO format datetime string"""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def format_iso_datetime(dt: datetime) -> str:
    """Format datetime as ISO string"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

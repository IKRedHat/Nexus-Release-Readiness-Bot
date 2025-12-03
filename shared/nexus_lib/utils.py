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
    
    # Complete mapping of all specialist agents
    AGENT_MAPPINGS = {
        # Core Data Agents
        "jira": {"env": "JIRA_AGENT_URL", "port": 8081},
        "git_ci": {"env": "GIT_CI_AGENT_URL", "port": 8082},
        
        # Communication Agents
        "slack": {"env": "SLACK_AGENT_URL", "port": 8084},
        
        # Analysis Agents
        "reporting": {"env": "REPORTING_AGENT_URL", "port": 8083},
        "rca": {"env": "RCA_AGENT_URL", "port": 8006},
        
        # Automation Agents
        "hygiene": {"env": "HYGIENE_AGENT_URL", "port": 8005},
        "scheduling": {"env": "SCHEDULING_AGENT_URL", "port": 8085},
        "webhooks": {"env": "WEBHOOKS_URL", "port": 8087},
        
        # Observability
        "analytics": {"env": "ANALYTICS_URL", "port": 8086},
        
        # Admin Dashboard
        "admin": {"env": "ADMIN_DASHBOARD_URL", "port": 8088},
    }
    
    def __init__(self):
        self._agents: Dict[str, str] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Load agent URLs from environment variables"""
        for agent_type, config in self.AGENT_MAPPINGS.items():
            env_var = config["env"]
            default_port = config["port"]
            
            url = os.environ.get(env_var)
            if url:
                self._agents[agent_type] = url
            else:
                # Default to localhost with service port for development
                self._agents[agent_type] = f"http://localhost:{default_port}"
    
    def get_url(self, agent_type: str) -> Optional[str]:
        """Get URL for an agent type"""
        return self._agents.get(agent_type)
    
    def register(self, agent_type: str, url: str):
        """Register an agent URL"""
        self._agents[agent_type] = url
    
    def list_agents(self) -> Dict[str, str]:
        """List all registered agents"""
        return self._agents.copy()
    
    def get_all_agent_types(self) -> List[str]:
        """Get list of all known agent types"""
        return list(self.AGENT_MAPPINGS.keys())


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
# LOG PROCESSING UTILITIES (for RCA)
# ============================================================================

# Common error patterns to preserve in truncated logs
ERROR_PATTERNS = [
    # Python
    r"Traceback \(most recent call last\):.*?(?=\n\n|\Z)",
    r"^\s*File \".*\", line \d+.*$",
    r"^\w+Error:.*$",
    r"^\w+Exception:.*$",
    r"AssertionError:.*$",
    r"FAILED.*$",
    
    # Java/JVM
    r"Exception in thread.*$",
    r"^\s*at [\w\.$]+\(.*:\d+\).*$",
    r"Caused by:.*$",
    r"java\.\w+\.\w+Exception:.*$",
    r"BUILD FAILURE.*$",
    r"\[ERROR\].*$",
    
    # JavaScript/Node
    r"Error:.*$",
    r"^\s*at .*\(.*:\d+:\d+\).*$",
    r"ReferenceError:.*$",
    r"TypeError:.*$",
    r"SyntaxError:.*$",
    
    # Generic CI/Build
    r"FAILURE:.*$",
    r"ERROR:.*$",
    r"FATAL:.*$",
    r"Test failed:.*$",
    r"Compilation failed.*$",
    r"Permission denied.*$",
    r"Cannot find.*$",
    r"No such file or directory.*$",
    r"Command failed.*$",
    r"Exit code: [1-9]\d*.*$",
    r"npm ERR!.*$",
    r"ModuleNotFoundError:.*$",
    r"ImportError:.*$",
]

# Compiled patterns for efficiency
import re
COMPILED_ERROR_PATTERNS = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in ERROR_PATTERNS]


def truncate_build_log(
    log_content: str,
    max_total_chars: int = 100000,  # ~25k tokens for most models
    head_lines: int = 100,
    tail_lines: int = 200,
    error_context_lines: int = 10,
    preserve_error_blocks: bool = True
) -> str:
    """
    Intelligently truncate a build log to fit within LLM context windows
    while preserving the most relevant error information.
    
    Strategy:
    1. Keep the first N lines (build initialization, environment info)
    2. Keep the last M lines (final status, summary)
    3. Extract and preserve all error blocks with context
    4. Ensure total size fits within max_total_chars
    
    Args:
        log_content: The full build log content
        max_total_chars: Maximum total characters to return
        head_lines: Number of lines to keep from the start
        tail_lines: Number of lines to keep from the end
        error_context_lines: Lines of context around each error
        preserve_error_blocks: Whether to extract and preserve error blocks
    
    Returns:
        Truncated log with preserved error sections
    """
    if len(log_content) <= max_total_chars:
        return log_content
    
    lines = log_content.split('\n')
    total_lines = len(lines)
    
    if total_lines <= head_lines + tail_lines:
        return log_content[:max_total_chars]
    
    # Extract sections
    head_section = lines[:head_lines]
    tail_section = lines[-tail_lines:]
    middle_section = lines[head_lines:-tail_lines] if tail_lines > 0 else lines[head_lines:]
    
    # Find error blocks in the middle section
    error_blocks = []
    if preserve_error_blocks and middle_section:
        middle_text = '\n'.join(middle_section)
        
        for pattern in COMPILED_ERROR_PATTERNS:
            for match in pattern.finditer(middle_text):
                start_pos = match.start()
                end_pos = match.end()
                
                # Get line numbers
                start_line = middle_text[:start_pos].count('\n')
                end_line = middle_text[:end_pos].count('\n')
                
                # Add context
                context_start = max(0, start_line - error_context_lines)
                context_end = min(len(middle_section), end_line + error_context_lines + 1)
                
                error_block = '\n'.join(middle_section[context_start:context_end])
                
                # Avoid duplicates
                if error_block not in error_blocks:
                    error_blocks.append(error_block)
    
    # Build the truncated log
    separator = "\n\n" + "=" * 60 + "\n"
    
    parts = []
    
    # Header section
    parts.append("=== BUILD LOG START (first {} lines) ===\n".format(head_lines))
    parts.append('\n'.join(head_section))
    
    # Error blocks
    if error_blocks:
        parts.append(separator)
        parts.append("=== EXTRACTED ERROR BLOCKS ===\n")
        for i, block in enumerate(error_blocks[:20], 1):  # Limit to 20 blocks
            parts.append(f"\n--- Error Block {i} ---\n")
            parts.append(block)
    
    # Truncation notice
    skipped_lines = total_lines - head_lines - tail_lines
    parts.append(separator)
    parts.append(f"[... {skipped_lines} lines truncated ...]\n")
    
    # Tail section
    parts.append(separator)
    parts.append("=== BUILD LOG END (last {} lines) ===\n".format(tail_lines))
    parts.append('\n'.join(tail_section))
    
    result = ''.join(parts)
    
    # Final size check - if still too long, truncate from middle error blocks
    if len(result) > max_total_chars:
        # Calculate how much we need to cut
        excess = len(result) - max_total_chars
        
        # Remove error blocks until we fit
        while error_blocks and len(result) > max_total_chars:
            error_blocks.pop()
            parts = []
            parts.append("=== BUILD LOG START (first {} lines) ===\n".format(head_lines))
            parts.append('\n'.join(head_section))
            if error_blocks:
                parts.append(separator)
                parts.append("=== EXTRACTED ERROR BLOCKS ===\n")
                for i, block in enumerate(error_blocks, 1):
                    parts.append(f"\n--- Error Block {i} ---\n")
                    parts.append(block)
            parts.append(separator)
            parts.append(f"[... {skipped_lines} lines truncated ...]\n")
            parts.append(separator)
            parts.append("=== BUILD LOG END (last {} lines) ===\n".format(tail_lines))
            parts.append('\n'.join(tail_section))
            result = ''.join(parts)
        
        # If still too long, hard truncate
        if len(result) > max_total_chars:
            result = result[:max_total_chars] + "\n[... LOG TRUNCATED TO FIT CONTEXT WINDOW ...]"
    
    return result


def extract_error_summary(log_content: str, max_errors: int = 10) -> List[str]:
    """
    Extract a list of error messages from a build log.
    
    Args:
        log_content: The build log content
        max_errors: Maximum number of errors to extract
    
    Returns:
        List of unique error messages
    """
    errors = []
    
    for pattern in COMPILED_ERROR_PATTERNS:
        for match in pattern.finditer(log_content):
            error_text = match.group().strip()
            if error_text and error_text not in errors:
                errors.append(error_text)
                if len(errors) >= max_errors:
                    return errors
    
    return errors


def parse_stack_trace(log_content: str) -> Optional[Dict[str, Any]]:
    """
    Parse a stack trace from log content.
    
    Returns:
        Dictionary with parsed stack trace info or None
    """
    # Python traceback
    python_tb_pattern = r"Traceback \(most recent call last\):(.*?)(\w+(?:Error|Exception):.*?)(?=\n\n|\Z)"
    python_match = re.search(python_tb_pattern, log_content, re.DOTALL)
    
    if python_match:
        frames_text = python_match.group(1)
        error_line = python_match.group(2).strip()
        
        # Parse frames
        frame_pattern = r'File "([^"]+)", line (\d+), in (\w+)'
        frames = []
        for match in re.finditer(frame_pattern, frames_text):
            frames.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "function": match.group(3)
            })
        
        return {
            "type": "python",
            "error": error_line,
            "frames": frames,
            "top_frame": frames[-1] if frames else None
        }
    
    # Java stack trace
    java_pattern = r"([\w.]+(?:Exception|Error)):?\s*(.*?)(?:\n\s+at ([\w.$]+)\(([\w.]+):(\d+)\))?"
    java_match = re.search(java_pattern, log_content)
    
    if java_match:
        frames = []
        at_pattern = r"at ([\w.$]+)\(([\w.]+):(\d+)\)"
        for match in re.finditer(at_pattern, log_content):
            frames.append({
                "class": match.group(1),
                "file": match.group(2),
                "line": int(match.group(3))
            })
        
        return {
            "type": "java",
            "exception": java_match.group(1),
            "message": java_match.group(2).strip() if java_match.group(2) else "",
            "frames": frames[:20],  # Limit frames
            "top_frame": frames[0] if frames else None
        }
    
    return None


def identify_failing_test(log_content: str) -> Optional[Dict[str, Any]]:
    """
    Identify the failing test from log content.
    
    Returns:
        Dictionary with test info or None
    """
    # JUnit/TestNG pattern
    junit_pattern = r"(?:FAILED|FAILURE|ERROR)[\s:]+(\w+(?:\.\w+)*)[#.](\w+)"
    junit_match = re.search(junit_pattern, log_content)
    
    if junit_match:
        return {
            "framework": "junit",
            "class": junit_match.group(1),
            "method": junit_match.group(2),
            "full_name": f"{junit_match.group(1)}#{junit_match.group(2)}"
        }
    
    # pytest pattern
    pytest_pattern = r"FAILED\s+([\w/]+\.py)::(\w+)(?:::(\w+))?"
    pytest_match = re.search(pytest_pattern, log_content)
    
    if pytest_match:
        return {
            "framework": "pytest",
            "file": pytest_match.group(1),
            "class": pytest_match.group(2),
            "method": pytest_match.group(3) if pytest_match.group(3) else pytest_match.group(2),
            "full_name": pytest_match.group(0).replace("FAILED ", "")
        }
    
    return None


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

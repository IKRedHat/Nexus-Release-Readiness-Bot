"""
Nexus Shared Library
Common utilities, schemas, and middleware for the Nexus multi-agent system
"""
from nexus_lib.schemas.agent_contract import (
    # Enums
    AgentType,
    TaskPriority,
    TaskStatus,
    JiraIssueType,
    JiraStatus,
    BuildResult,
    SeverityLevel,
    ReleaseDecision,
    # Jira Models
    JiraUser,
    JiraComment,
    JiraWorklog,
    JiraTransition,
    JiraTicket,
    JiraSearchResult,
    JiraSprintStats,
    # Build/CI Models
    BuildArtifact,
    BuildTestResult,
    BuildStatus,
    PRStatus,
    RepositoryHealth,
    # Security Models
    Vulnerability,
    SecurityScanResult,
    # Release Models
    ReleaseChecklist,
    ReleaseStats,
    ReleaseReport,
    # Agent Protocol
    AgentTaskRequest,
    AgentTaskResponse,
    ReActStep,
    ReActTrace,
    # Slack Models
    SlackUser,
    SlackCommand,
    SlackBlockAction,
    # Utility Models
    HealthCheck,
    PaginatedResponse,
)

from nexus_lib.middleware import (
    JWTConfig,
    JWTHandler,
    JWTBearer,
    MetricsMiddleware,
    AuthMiddleware,
    RequestIdMiddleware,
    RateLimitMiddleware,
)

from nexus_lib.instrumentation import (
    setup_tracing,
    get_tracer,
    instrument_fastapi,
    instrument_httpx,
    track_llm_usage,
    track_tool_usage,
    track_react_loop,
    ReActTracker,
    get_metrics,
    create_metrics_endpoint,
    # Metrics
    LLM_TOKENS_TOTAL,
    LLM_REQUESTS_TOTAL,
    LLM_LATENCY,
    TOOL_USAGE_TOTAL,
    REACT_ITERATIONS,
    RELEASE_DECISIONS,
)

from nexus_lib.utils import (
    AsyncHttpClient,
    AgentRegistry,
    agent_registry,
    SimpleCache,
    cache,
    cached,
    generate_task_id,
    hash_content,
    truncate_string,
    parse_ticket_key,
    format_duration,
    safe_get,
    merge_dicts,
    chunk_list,
    gather_with_concurrency,
    retry_async,
    utc_now,
    parse_iso_datetime,
    format_iso_datetime,
)

__version__ = "1.0.0"
__all__ = [
    # Version
    "__version__",
    # Enums
    "AgentType",
    "TaskPriority", 
    "TaskStatus",
    "JiraIssueType",
    "JiraStatus",
    "BuildResult",
    "SeverityLevel",
    "ReleaseDecision",
    # Jira Models
    "JiraUser",
    "JiraComment",
    "JiraWorklog",
    "JiraTransition",
    "JiraTicket",
    "JiraSearchResult",
    "JiraSprintStats",
    # Build/CI Models
    "BuildArtifact",
    "BuildTestResult",
    "BuildStatus",
    "PRStatus",
    "RepositoryHealth",
    # Security Models
    "Vulnerability",
    "SecurityScanResult",
    # Release Models
    "ReleaseChecklist",
    "ReleaseStats",
    "ReleaseReport",
    # Agent Protocol
    "AgentTaskRequest",
    "AgentTaskResponse",
    "ReActStep",
    "ReActTrace",
    # Slack Models
    "SlackUser",
    "SlackCommand",
    "SlackBlockAction",
    # Utility Models
    "HealthCheck",
    "PaginatedResponse",
    # Middleware
    "JWTConfig",
    "JWTHandler",
    "JWTBearer",
    "MetricsMiddleware",
    "AuthMiddleware",
    "RequestIdMiddleware",
    "RateLimitMiddleware",
    # Instrumentation
    "setup_tracing",
    "get_tracer",
    "instrument_fastapi",
    "instrument_httpx",
    "track_llm_usage",
    "track_tool_usage",
    "track_react_loop",
    "ReActTracker",
    "get_metrics",
    "create_metrics_endpoint",
    # Metrics
    "LLM_TOKENS_TOTAL",
    "LLM_REQUESTS_TOTAL",
    "LLM_LATENCY",
    "TOOL_USAGE_TOTAL",
    "REACT_ITERATIONS",
    "RELEASE_DECISIONS",
    # Utils
    "AsyncHttpClient",
    "AgentRegistry",
    "agent_registry",
    "SimpleCache",
    "cache",
    "cached",
    "generate_task_id",
    "hash_content",
    "truncate_string",
    "parse_ticket_key",
    "format_duration",
    "safe_get",
    "merge_dicts",
    "chunk_list",
    "gather_with_concurrency",
    "retry_async",
    "utc_now",
    "parse_iso_datetime",
    "format_iso_datetime",
]


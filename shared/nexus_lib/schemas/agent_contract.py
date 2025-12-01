"""
Nexus Agent Contract Schemas
Comprehensive Pydantic models for inter-agent communication
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime
import uuid


# ============================================================================
# ENUMERATIONS
# ============================================================================

class AgentType(str, Enum):
    """Types of agents in the Nexus system"""
    JIRA = "jira"
    GIT_CI = "git_ci"
    SLACK = "slack"
    REPORTING = "reporting"
    SCHEDULING = "scheduling"
    ORCHESTRATOR = "orchestrator"
    RCA = "rca"  # Root Cause Analysis agent


class TaskPriority(str, Enum):
    """Priority levels for tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class JiraIssueType(str, Enum):
    """Jira issue types"""
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    SUBTASK = "Sub-task"
    BUG = "Bug"
    SPIKE = "Spike"


class JiraStatus(str, Enum):
    """Common Jira status values"""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class BuildResult(str, Enum):
    """Jenkins/CI build results"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNSTABLE = "UNSTABLE"
    ABORTED = "ABORTED"
    NOT_BUILT = "NOT_BUILT"
    BUILDING = "BUILDING"


class SeverityLevel(str, Enum):
    """Security vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReleaseDecision(str, Enum):
    """Go/No-Go release decision"""
    GO = "GO"
    NO_GO = "NO_GO"
    CONDITIONAL = "CONDITIONAL"
    PENDING = "PENDING"


# ============================================================================
# JIRA DOMAIN MODELS
# ============================================================================

class JiraUser(BaseModel):
    """Jira user representation"""
    account_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    active: bool = True


class JiraComment(BaseModel):
    """Jira comment model"""
    id: str
    author: JiraUser
    body: str
    created: datetime
    updated: Optional[datetime] = None


class JiraWorklog(BaseModel):
    """Jira worklog entry"""
    id: str
    author: JiraUser
    time_spent_seconds: int
    started: datetime
    comment: Optional[str] = None


class JiraTransition(BaseModel):
    """Available Jira status transitions"""
    id: str
    name: str
    to_status: str


class JiraTicket(BaseModel):
    """Comprehensive Jira ticket/issue model"""
    key: str = Field(..., description="Unique ticket key (e.g., PROJ-123)")
    id: Optional[str] = Field(None, description="Internal Jira ID")
    summary: str = Field(..., description="Ticket summary/title")
    description: Optional[str] = Field(None, description="Full ticket description")
    issue_type: JiraIssueType = Field(JiraIssueType.TASK, description="Issue type")
    status: str = Field(..., description="Current status")
    resolution: Optional[str] = Field(None, description="Resolution if resolved")
    priority: Optional[str] = Field("Medium", description="Priority level")
    
    # Hierarchy
    project_key: Optional[str] = Field(None, description="Project key")
    parent_key: Optional[str] = Field(None, description="Parent ticket key (for subtasks)")
    epic_key: Optional[str] = Field(None, description="Epic link")
    subtasks: List['JiraTicket'] = Field(default_factory=list, description="Child subtasks")
    linked_issues: List[str] = Field(default_factory=list, description="Linked issue keys")
    
    # People
    assignee: Optional[JiraUser] = Field(None, description="Assigned user")
    reporter: Optional[JiraUser] = Field(None, description="Reporter user")
    watchers: List[str] = Field(default_factory=list, description="Watcher account IDs")
    
    # Time tracking
    story_points: Optional[float] = Field(None, description="Story points estimate")
    original_estimate_seconds: Optional[int] = Field(None, description="Original time estimate")
    remaining_estimate_seconds: Optional[int] = Field(None, description="Remaining estimate")
    time_spent_seconds: Optional[int] = Field(None, description="Time logged")
    
    # Sprint/Release
    sprint_id: Optional[int] = Field(None, description="Current sprint ID")
    sprint_name: Optional[str] = Field(None, description="Current sprint name")
    fix_versions: List[str] = Field(default_factory=list, description="Fix version(s)")
    
    # Metadata
    labels: List[str] = Field(default_factory=list, description="Labels/tags")
    components: List[str] = Field(default_factory=list, description="Components")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    
    # Comments and worklogs
    comments: List[JiraComment] = Field(default_factory=list, description="Comments")
    worklogs: List[JiraWorklog] = Field(default_factory=list, description="Work logs")
    
    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field values")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class JiraSearchResult(BaseModel):
    """Jira JQL search result"""
    total: int
    start_at: int
    max_results: int
    issues: List[JiraTicket]
    expand: Optional[str] = None


class JiraSprintStats(BaseModel):
    """Sprint statistics for reporting"""
    sprint_id: int
    sprint_name: str
    total_issues: int
    completed_issues: int
    in_progress_issues: int
    blocked_issues: int
    total_story_points: float
    completed_story_points: float
    completion_percentage: float
    blockers: List[str] = Field(default_factory=list)


# ============================================================================
# BUILD/CI DOMAIN MODELS
# ============================================================================

class BuildArtifact(BaseModel):
    """CI build artifact"""
    name: str
    path: str
    url: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None


class BuildTestResult(BaseModel):
    """Test results from a CI build"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    coverage_percentage: Optional[float] = None
    failed_test_names: List[str] = Field(default_factory=list)


class BuildStatus(BaseModel):
    """Comprehensive CI/CD build status model"""
    job_name: str = Field(..., description="Jenkins job name or CI pipeline name")
    build_number: int = Field(..., description="Build number")
    status: BuildResult = Field(..., description="Build result status")
    url: str = Field(..., description="Build URL")
    
    # Timing
    timestamp: datetime = Field(..., description="Build start time")
    duration_seconds: float = Field(..., description="Build duration")
    queued_duration_seconds: Optional[float] = Field(None, description="Time in queue")
    
    # Git context
    branch: Optional[str] = Field(None, description="Git branch")
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    commit_message: Optional[str] = Field(None, description="Commit message")
    commit_author: Optional[str] = Field(None, description="Commit author")
    
    # Build details
    triggered_by: Optional[str] = Field(None, description="User or trigger source")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Build parameters")
    
    # Results
    artifacts: List[BuildArtifact] = Field(default_factory=list, description="Build artifacts")
    test_results: Optional[BuildTestResult] = Field(None, description="Test results")
    console_log_url: Optional[str] = Field(None, description="Console log URL")
    
    # Downstream
    downstream_builds: List[str] = Field(default_factory=list, description="Triggered downstream jobs")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PRStatus(BaseModel):
    """GitHub Pull Request status"""
    pr_number: int
    title: str
    state: str  # open, closed, merged
    author: str
    base_branch: str
    head_branch: str
    url: str
    
    # Review status
    mergeable: Optional[bool] = None
    merged: bool = False
    merged_by: Optional[str] = None
    merged_at: Optional[datetime] = None
    
    # Checks
    ci_status: Optional[str] = None  # pending, success, failure
    required_checks_passed: bool = False
    approvals: int = 0
    changes_requested: bool = False
    
    # Stats
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    comments: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class RepositoryHealth(BaseModel):
    """Repository health metrics"""
    repo_name: str
    default_branch: str
    latest_commit_sha: str
    latest_commit_status: str  # success, failure, pending
    
    # Branch protection
    branch_protection_enabled: bool = False
    required_reviews: int = 0
    
    # Statistics
    open_prs: int = 0
    stale_prs: int = 0  # PRs open > 7 days
    open_issues: int = 0
    
    # CI/CD
    last_successful_build: Optional[datetime] = None
    build_frequency_per_week: float = 0.0
    average_build_duration_minutes: float = 0.0


# ============================================================================
# SECURITY DOMAIN MODELS
# ============================================================================

class Vulnerability(BaseModel):
    """Individual security vulnerability"""
    id: str = Field(..., description="CVE or unique ID")
    title: str
    description: Optional[str] = None
    severity: SeverityLevel
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    # Location
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    
    # Remediation
    fixed_in_version: Optional[str] = None
    remediation: Optional[str] = None
    exploitable: bool = False
    
    # References
    references: List[str] = Field(default_factory=list)
    published_date: Optional[datetime] = None


class SecurityScanResult(BaseModel):
    """Comprehensive security scan result model"""
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_name: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Scanned branch")
    commit_sha: Optional[str] = Field(None, description="Scanned commit")
    
    # Scan metadata
    scanner_name: str = Field("nexus-scanner", description="Scanner tool name")
    scanner_version: Optional[str] = None
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
    scan_duration_seconds: Optional[float] = None
    
    # Risk assessment
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_level: SeverityLevel = Field(SeverityLevel.LOW, description="Risk level")
    
    # Vulnerability counts by severity
    critical_vulnerabilities: int = Field(0, ge=0)
    high_vulnerabilities: int = Field(0, ge=0)
    medium_vulnerabilities: int = Field(0, ge=0)
    low_vulnerabilities: int = Field(0, ge=0)
    info_vulnerabilities: int = Field(0, ge=0)
    
    # Detailed findings
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    
    # Dependency analysis
    total_dependencies: int = 0
    vulnerable_dependencies: int = 0
    outdated_dependencies: int = 0
    
    # Code analysis
    secrets_detected: int = 0
    code_smells: int = 0
    
    # Reports
    report_url: Optional[str] = None
    sarif_report_url: Optional[str] = None
    
    # Compliance
    compliant: bool = True
    policy_violations: List[str] = Field(default_factory=list)
    
    @field_validator('risk_level', mode='before')
    @classmethod
    def compute_risk_level(cls, v, info):
        """Compute risk level from risk score if not provided"""
        if v is not None:
            return v
        score = info.data.get('risk_score', 0)
        if score >= 80:
            return SeverityLevel.CRITICAL
        elif score >= 60:
            return SeverityLevel.HIGH
        elif score >= 40:
            return SeverityLevel.MEDIUM
        elif score >= 20:
            return SeverityLevel.LOW
        return SeverityLevel.INFO


# ============================================================================
# RELEASE & REPORTING MODELS
# ============================================================================

class ReleaseChecklist(BaseModel):
    """Release readiness checklist item"""
    item: str
    passed: bool
    details: Optional[str] = None
    required: bool = True
    checked_at: Optional[datetime] = None


class ReleaseStats(BaseModel):
    """Aggregated release statistics"""
    release_version: str
    release_date: Optional[datetime] = None
    
    # Jira stats
    total_tickets: int = 0
    completed_tickets: int = 0
    in_progress_tickets: int = 0
    blocked_tickets: int = 0
    ticket_completion_rate: float = 0.0
    
    # Story points
    total_story_points: float = 0.0
    completed_story_points: float = 0.0
    
    # Quality metrics
    test_coverage_percentage: float = 0.0
    passing_tests: int = 0
    failing_tests: int = 0
    
    # Security
    security_risk_score: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    
    # Build health
    last_build_status: Optional[BuildResult] = None
    build_success_rate: float = 0.0
    
    # Decision
    go_no_go: ReleaseDecision = ReleaseDecision.PENDING
    decision_rationale: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    
    # Checklist
    checklist: List[ReleaseChecklist] = Field(default_factory=list)


class ReleaseReport(BaseModel):
    """Full release readiness report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field("nexus-reporting-agent")
    
    # Core data
    stats: ReleaseStats
    
    # Detailed breakdowns
    jira_tickets: List[JiraTicket] = Field(default_factory=list)
    builds: List[BuildStatus] = Field(default_factory=list)
    security_scans: List[SecurityScanResult] = Field(default_factory=list)
    
    # Publishing
    confluence_page_id: Optional[str] = None
    confluence_url: Optional[str] = None
    html_content: Optional[str] = None


# ============================================================================
# AGENT COMMUNICATION PROTOCOL
# ============================================================================

class AgentTaskRequest(BaseModel):
    """Request sent to an agent to execute a task"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique trace ID")
    correlation_id: Optional[str] = Field(None, description="Parent request correlation ID")
    
    # Task details
    action: str = Field(..., description="Function/action name to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action arguments")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    
    # Context
    user_context: Optional[Dict[str, str]] = Field(None, description="User context (Slack ID, Team ID)")
    source_agent: Optional[AgentType] = Field(None, description="Requesting agent type")
    
    # Execution control
    timeout_seconds: int = Field(60, description="Execution timeout")
    retry_count: int = Field(0, description="Number of retries attempted")
    max_retries: int = Field(3, description="Maximum retries allowed")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class AgentTaskResponse(BaseModel):
    """Response from an agent after task execution"""
    task_id: str = Field(..., description="Original task ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID if provided")
    
    # Status
    status: TaskStatus = Field(..., description="Execution status")
    
    # Results
    data: Optional[Dict[str, Any]] = Field(None, description="Successful result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    
    # Metrics
    execution_time_ms: float = Field(0.0, description="Execution time in milliseconds")
    retries_used: int = Field(0, description="Number of retries used")
    
    # Metadata
    agent_type: Optional[AgentType] = Field(None, description="Responding agent type")
    agent_version: Optional[str] = Field(None, description="Agent version")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ReActStep(BaseModel):
    """Single step in the ReAct reasoning loop"""
    step_number: int
    thought: str = Field(..., description="Agent's reasoning/thought")
    action: Optional[str] = Field(None, description="Selected action/tool")
    action_input: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    observation: Optional[str] = Field(None, description="Result/observation from action")
    is_final: bool = Field(False, description="Whether this is the final answer")


class ReActTrace(BaseModel):
    """Complete trace of a ReAct execution"""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    steps: List[ReActStep] = Field(default_factory=list)
    final_answer: Optional[str] = None
    total_iterations: int = 0
    success: bool = False
    
    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    model_name: Optional[str] = None
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0.0


# ============================================================================
# ROOT CAUSE ANALYSIS (RCA) MODELS
# ============================================================================

class RcaConfidenceLevel(str, Enum):
    """Confidence level for RCA analysis"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class RcaErrorType(str, Enum):
    """Types of errors that can be identified"""
    COMPILATION_ERROR = "compilation_error"
    TEST_FAILURE = "test_failure"
    DEPENDENCY_ERROR = "dependency_error"
    CONFIGURATION_ERROR = "configuration_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class RcaRequest(BaseModel):
    """Request for Root Cause Analysis of a failed build"""
    # Required identifiers
    job_name: str = Field(..., description="Jenkins job name")
    build_number: int = Field(..., description="Build number to analyze")
    
    # Optional context
    build_url: Optional[str] = Field(None, description="Direct URL to the build")
    repo_name: Optional[str] = Field(None, description="Repository name for git context")
    branch: Optional[str] = Field(None, description="Git branch")
    pr_id: Optional[int] = Field(None, description="Pull request ID if applicable")
    commit_sha: Optional[str] = Field(None, description="Specific commit SHA to analyze")
    
    # Analysis options
    include_git_diff: bool = Field(True, description="Include git diff in analysis")
    include_test_output: bool = Field(True, description="Include test output details")
    max_log_lines: int = Field(5000, description="Maximum log lines to analyze")
    
    # Request metadata
    requested_by: Optional[str] = Field(None, description="User who requested the analysis")
    request_source: Optional[str] = Field(None, description="Source of request (slack, api, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_name": "nexus-main-pipeline",
                "build_number": 142,
                "repo_name": "nexus-backend",
                "branch": "feature/new-api",
                "pr_id": 456,
                "include_git_diff": True
            }
        }


class RcaFileChange(BaseModel):
    """File change that may have caused the issue"""
    file_path: str = Field(..., description="Path to the changed file")
    change_type: str = Field(..., description="Type of change: added, modified, deleted")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    relevant_lines: Optional[List[int]] = Field(None, description="Specific lines related to the error")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/api/handlers.py",
                "change_type": "modified",
                "lines_added": 15,
                "lines_deleted": 3,
                "relevant_lines": [42, 43, 44],
                "code_snippet": "def handle_request(self):\n    return self.invalid_method()"
            }
        }


class RcaTestFailure(BaseModel):
    """Details of a specific test failure"""
    test_name: str = Field(..., description="Full test name/path")
    test_class: Optional[str] = Field(None, description="Test class name")
    error_message: str = Field(..., description="Error message from the test")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    expected: Optional[str] = Field(None, description="Expected value")
    actual: Optional[str] = Field(None, description="Actual value")
    duration_seconds: Optional[float] = Field(None, description="Test duration")


class RcaAnalysis(BaseModel):
    """Complete Root Cause Analysis result"""
    # Analysis identification
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis ID")
    request: RcaRequest = Field(..., description="Original request")
    
    # Core findings
    root_cause_summary: str = Field(..., description="Human-readable summary of the root cause")
    error_type: RcaErrorType = Field(RcaErrorType.UNKNOWN, description="Categorized error type")
    error_message: str = Field(..., description="Primary error message extracted from logs")
    
    # Confidence and reliability
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis (0-1)")
    confidence_level: RcaConfidenceLevel = Field(RcaConfidenceLevel.MEDIUM, description="Confidence category")
    
    # Suspected cause
    suspected_commit: Optional[str] = Field(None, description="SHA of the suspected commit")
    suspected_author: Optional[str] = Field(None, description="Author of the suspected commit")
    suspected_files: List[RcaFileChange] = Field(default_factory=list, description="Files likely causing the issue")
    
    # Detailed findings
    test_failures: List[RcaTestFailure] = Field(default_factory=list, description="Detailed test failure info")
    error_log_excerpt: str = Field("", description="Relevant excerpt from error logs")
    
    # Suggestions
    fix_suggestion: str = Field(..., description="Suggested fix for the issue")
    fix_code_snippet: Optional[str] = Field(None, description="Example code fix if applicable")
    additional_recommendations: List[str] = Field(default_factory=list, description="Additional recommendations")
    
    # Related information
    similar_failures: List[str] = Field(default_factory=list, description="Similar past failures")
    documentation_links: List[str] = Field(default_factory=list, description="Helpful documentation")
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration_seconds: float = Field(0.0, description="Time taken for analysis")
    model_used: Optional[str] = Field(None, description="LLM model used for analysis")
    tokens_used: int = Field(0, description="Total tokens used for analysis")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "analysis_id": "rca-20251130-abc123",
                "root_cause_summary": "Test failure in UserServiceTest due to null pointer exception when accessing user.getEmail() on line 42",
                "error_type": "test_failure",
                "error_message": "NullPointerException: Cannot invoke method getEmail() on null object",
                "confidence_score": 0.85,
                "confidence_level": "high",
                "suspected_commit": "a1b2c3d4e5f6",
                "suspected_author": "developer@example.com",
                "fix_suggestion": "Add null check before accessing user.getEmail() or ensure user object is properly initialized in the test setup.",
                "fix_code_snippet": "if (user != null && user.getEmail() != null) {\n    sendEmail(user.getEmail());\n}"
            }
        }


class RcaBatchRequest(BaseModel):
    """Request to analyze multiple failed builds"""
    requests: List[RcaRequest] = Field(..., min_length=1, max_length=10)
    correlation_id: Optional[str] = Field(None, description="ID to correlate batch results")


class RcaBatchResponse(BaseModel):
    """Response containing multiple RCA analyses"""
    correlation_id: Optional[str] = None
    analyses: List[RcaAnalysis] = Field(default_factory=list)
    failed_analyses: List[Dict[str, str]] = Field(default_factory=list, description="Requests that failed")
    total_duration_seconds: float = 0.0


# ============================================================================
# SLACK MODELS
# ============================================================================

class SlackUser(BaseModel):
    """Slack user context"""
    user_id: str
    username: str
    team_id: str
    channel_id: Optional[str] = None
    is_admin: bool = False


class SlackCommand(BaseModel):
    """Parsed Slack slash command"""
    command: str
    text: str
    user: SlackUser
    response_url: str
    trigger_id: str


class SlackBlockAction(BaseModel):
    """Slack Block Kit action"""
    action_id: str
    block_id: str
    value: Optional[str] = None
    selected_option: Optional[Dict[str, str]] = None


# ============================================================================
# UTILITY MODELS
# ============================================================================

class HealthCheck(BaseModel):
    """Service health check response"""
    status: str = "healthy"
    service: str
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    dependencies: Dict[str, str] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False


# Rebuild models with forward references
JiraTicket.model_rebuild()

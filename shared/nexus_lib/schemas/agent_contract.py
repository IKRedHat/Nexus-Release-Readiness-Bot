from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class AgentType(str, Enum):
    JIRA = "jira"
    GIT_CI = "git_ci"
    SLACK = "slack"
    REPORTING = "reporting"
    ORCHESTRATOR = "orchestrator"

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# --- Domain Specific Models ---

class JiraTicket(BaseModel):
    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    priority: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    parent_key: Optional[str] = None
    subtasks: List['JiraTicket'] = []

class BuildStatus(BaseModel):
    job_name: str
    build_number: int
    status: str = Field(..., description="SUCCESS, FAILURE, ABORTED")
    url: HttpUrl
    timestamp: datetime
    duration_seconds: float
    artifacts: List[Dict[str, str]] = []

class SecurityScanResult(BaseModel):
    repo_name: str
    branch: str
    risk_score: int = Field(..., ge=0, le=100)
    critical_vulnerabilities: int
    high_vulnerabilities: int
    report_url: Optional[str] = None

# --- Agent Communication Protocol ---

class AgentTaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique Trace ID")
    action: str = Field(..., description="Function name to execute")
    payload: Dict[str, Any] = Field(..., description="Arguments")
    user_context: Optional[Dict[str, str]] = Field(None, description="Slack User ID/Team ID")

class AgentTaskResponse(BaseModel):
    task_id: str
    status: str = Field(..., description="success, error")
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

# Circular reference update
JiraTicket.model_rebuild()

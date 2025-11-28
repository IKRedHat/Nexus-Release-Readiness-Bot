from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class AgentType(str, Enum):
    JIRA = "jira"
    GIT_CI = "git_ci"
    SLACK = "slack"
    REPORTING = "reporting"

class AgentTaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique ID for tracing")
    action: str = Field(..., description="The specific function to call")
    payload: Dict[str, Any] = Field(..., description="Arguments for the function")
    user_context: Optional[Dict[str, str]] = Field(None, description="Slack user ID etc")

class AgentTaskResponse(BaseModel):
    task_id: str
    status: str = Field(..., description="success, error, or pending")
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

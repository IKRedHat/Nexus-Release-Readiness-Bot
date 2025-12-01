"""
Nexus Test Configuration
Shared fixtures and configuration for all tests
"""
import os
import sys
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# Add paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/orchestrator")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["JENKINS_MOCK_MODE"] = "true"
os.environ["CONFLUENCE_MOCK_MODE"] = "true"
os.environ["SLACK_MOCK_MODE"] = "true"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["MEMORY_BACKEND"] = "mock"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vector_memory():
    """Mock vector memory for testing"""
    from app.core.memory import VectorMemory
    memory = VectorMemory()
    return memory


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing"""
    from nexus_lib.utils import AsyncHttpClient
    client = AsyncMock(spec=AsyncHttpClient)
    client.get = AsyncMock(return_value={"status": "success", "data": {}})
    client.post = AsyncMock(return_value={"status": "success", "data": {}})
    return client


@pytest.fixture
def sample_jira_ticket():
    """Sample Jira ticket data"""
    return {
        "key": "PROJ-123",
        "summary": "Test ticket",
        "status": "In Progress",
        "issue_type": "Story",
        "priority": "Medium",
        "assignee": {
            "account_id": "user-123",
            "display_name": "Test User"
        },
        "story_points": 5.0,
        "sprint_name": "Sprint 42"
    }


@pytest.fixture
def sample_build_status():
    """Sample build status data"""
    return {
        "job_name": "nexus-main",
        "build_number": 142,
        "status": "SUCCESS",
        "url": "https://jenkins.example.com/job/nexus-main/142/",
        "timestamp": "2025-11-30T10:30:00Z",
        "duration_seconds": 485.5,
        "test_results": {
            "total_tests": 245,
            "passed": 245,
            "failed": 0,
            "skipped": 0
        }
    }


@pytest.fixture
def sample_security_scan():
    """Sample security scan data"""
    return {
        "repo_name": "nexus/backend",
        "branch": "main",
        "risk_score": 25,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 2,
        "medium_vulnerabilities": 5,
        "low_vulnerabilities": 12
    }


@pytest.fixture
def sample_release_stats():
    """Sample release statistics"""
    return {
        "release_version": "v2.0.0",
        "total_tickets": 45,
        "completed_tickets": 42,
        "in_progress_tickets": 2,
        "blocked_tickets": 1,
        "ticket_completion_rate": 93.3,
        "total_story_points": 89.0,
        "completed_story_points": 82.0,
        "test_coverage_percentage": 85.5,
        "passing_tests": 245,
        "failing_tests": 0,
        "security_risk_score": 25,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 2,
        "last_build_status": "SUCCESS",
        "build_success_rate": 95.5,
        "go_no_go": "GO"
    }


@pytest.fixture
def sample_agent_request():
    """Sample agent task request"""
    from nexus_lib.schemas.agent_contract import AgentTaskRequest
    return AgentTaskRequest(
        task_id="test-task-123",
        action="test_action",
        payload={"key": "value"},
        user_context={"user_id": "U123", "team_id": "T456"}
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response"""
    return {
        "content": "Thought: I need to check the ticket status.\nAction: get_jira_ticket\nAction Input: {\"ticket_key\": \"PROJ-123\"}",
        "input_tokens": 100,
        "output_tokens": 50
    }


@pytest.fixture
def mock_final_answer_response():
    """Mock LLM final answer response"""
    return {
        "content": "Thought: I have gathered all necessary information.\nFinal Answer: The release is ready. All criteria are met.",
        "input_tokens": 150,
        "output_tokens": 40
    }


# =============================================================================
# Additional Fixtures for New Services
# =============================================================================

@pytest.fixture
def sample_hygiene_result():
    """Sample hygiene check result"""
    return {
        "check_id": "check-123",
        "timestamp": "2025-12-01T09:00:00Z",
        "project_key": "PROJ",
        "total_tickets_checked": 50,
        "compliant_tickets": 42,
        "non_compliant_tickets": 8,
        "hygiene_score": 84.0,
        "violations_by_assignee": [
            {
                "assignee_email": "alice@example.com",
                "assignee_display_name": "Alice Developer",
                "violations": [
                    {
                        "ticket_key": "PROJ-101",
                        "ticket_summary": "Missing labels ticket",
                        "missing_fields": ["Labels", "Story Points"]
                    }
                ],
                "total_violations": 3
            }
        ],
        "violation_summary": {
            "Labels": 4,
            "Story Points": 3,
            "Fix Version": 1
        }
    }


@pytest.fixture
def sample_rca_result():
    """Sample RCA analysis result"""
    return {
        "analysis_id": "rca-nexus-main-142",
        "job_name": "nexus-main",
        "build_number": 142,
        "root_cause_summary": "NullPointerException in UserService.validateEmail() due to missing null check",
        "error_type": "TEST_FAILURE",
        "error_message": "AttributeError: 'NoneType' object has no attribute 'is_valid'",
        "confidence_score": 0.85,
        "confidence_level": "HIGH",
        "suspected_files": [
            {
                "file_path": "src/api/users.py",
                "change_type": "modified",
                "lines_added": 10,
                "lines_deleted": 3,
                "relevant_lines": [87, 88, 89]
            }
        ],
        "fix_suggestion": "Add null check: if result is None: return default_value",
        "llm_explanation": "The error occurs because validate_user_email returns None when...",
        "model_used": "gemini-1.5-pro",
        "tokens_used": 2500,
        "analysis_duration_seconds": 8.5
    }


@pytest.fixture
def sample_analytics_kpis():
    """Sample analytics KPI data"""
    return {
        "deployment_frequency": 1.2,  # Per day
        "lead_time_hours": 18.5,
        "change_failure_rate": 0.05,  # 5%
        "mttr_hours": 1.2,
        "sprint_velocity": 42.0,
        "ticket_completion_rate": 94.5,
        "code_review_coverage": 98.0,
        "test_automation_rate": 87.5,
        "defect_escape_rate": 1.8,
        "security_risk_score": 22
    }


@pytest.fixture
def sample_webhook_subscription():
    """Sample webhook subscription data"""
    return {
        "id": "sub-123",
        "endpoint_url": "https://example.com/webhook/nexus",
        "event_types": ["release.created", "build.failed", "hygiene.violation"],
        "secret": "webhook-secret-key",
        "active": True,
        "created_at": "2025-12-01T10:00:00Z",
        "last_delivery": "2025-12-01T14:30:00Z",
        "delivery_stats": {
            "total_deliveries": 45,
            "successful_deliveries": 43,
            "failed_deliveries": 2,
            "success_rate": 95.6
        }
    }


@pytest.fixture
def sample_config():
    """Sample system configuration"""
    return {
        "nexus:mode": "mock",
        "nexus:config:jira_url": "https://jira.example.com",
        "nexus:config:github_org": "nexus",
        "nexus:config:jenkins_url": "https://jenkins.example.com",
        "nexus:config:llm_provider": "gemini",
        "nexus:config:llm_model": "gemini-1.5-pro",
        "nexus:config:slack_channel": "#releases"
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client for ConfigManager tests"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.keys = AsyncMock(return_value=[])
    mock.mget = AsyncMock(return_value=[])
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def sample_jenkins_log():
    """Sample Jenkins console log with failure"""
    return """
Started by user admin
Building in workspace /var/jenkins_home/workspace/nexus-main
[Pipeline] stage (Build)
+ python -m pip install -r requirements.txt
Successfully installed all dependencies

[Pipeline] stage (Test)
+ python -m pytest tests/ -v

============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.0
collected 45 items

tests/test_auth.py::TestAuth::test_login PASSED
tests/test_users.py::TestUserService::test_create_user PASSED
tests/test_users.py::TestUserService::test_validate_email FAILED

=================================== FAILURES ===================================
_________________________ TestUserService.test_validate_email __________________________

    def test_validate_email(self):
        user_service = UserService()
        result = user_service.validate_user_email("test@example.com")
>       assert result.is_valid == True
E       AttributeError: 'NoneType' object has no attribute 'is_valid'

tests/test_users.py:42: AttributeError
============================= 1 failed, 44 passed =============================

ERROR: script returned exit code 1
Finished: FAILURE
"""


@pytest.fixture
def sample_git_diff():
    """Sample Git diff"""
    return """
diff --git a/src/api/users.py b/src/api/users.py
index abc1234..def5678 100644
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -84,8 +84,12 @@ class UserService:
     def validate_user_email(self, email: str) -> ValidationResult:
-        if not email:
-            return None
+        if not email or not self._is_valid_format(email):
+            return ValidationResult(is_valid=False, error="Invalid email")
         
         # Check domain
-        return self._check_domain(email)
+        result = self._check_domain(email)
+        if result is None:
+            return ValidationResult(is_valid=False, error="Domain check failed")
+        return result
"""


# =============================================================================
# Pytest Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# =============================================================================
# Test Utilities
# =============================================================================

def create_mock_agent_response(status="success", data=None, error=None):
    """Helper to create standardized agent response."""
    response = {
        "task_id": f"task-{os.urandom(4).hex()}",
        "status": status,
        "data": data or {},
        "execution_time_ms": 50.0
    }
    if error:
        response["error_message"] = error
        response["error_code"] = "MOCK_ERROR"
    return response


def create_mock_health_response(service_name, healthy=True, mock_mode=True):
    """Helper to create standardized health response."""
    return {
        "status": "healthy" if healthy else "unhealthy",
        "service": service_name,
        "mock_mode": mock_mode,
        "timestamp": "2025-12-01T10:00:00Z"
    }

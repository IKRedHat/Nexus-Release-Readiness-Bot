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


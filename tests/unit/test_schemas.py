"""
Unit Tests for Pydantic Schemas
Tests data validation and serialization
"""
import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath("shared"))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    JiraTicket,
    JiraUser,
    BuildStatus,
    BuildResult,
    SecurityScanResult,
    SeverityLevel,
    ReleaseStats,
    ReleaseDecision,
    TaskStatus,
    AgentType,
)


class TestAgentContract:
    """Tests for agent communication schemas"""
    
    def test_agent_task_request_creation(self):
        """Test creating an agent task request"""
        request = AgentTaskRequest(
            action="get_ticket",
            payload={"key": "PROJ-123"}
        )
        
        assert request.action == "get_ticket"
        assert request.payload == {"key": "PROJ-123"}
        assert request.task_id  # Auto-generated
    
    def test_agent_task_request_with_context(self):
        """Test request with user context"""
        request = AgentTaskRequest(
            action="update_ticket",
            payload={"key": "PROJ-123", "status": "Done"},
            user_context={"user_id": "U123", "team_id": "T456"}
        )
        
        assert request.user_context["user_id"] == "U123"
    
    def test_agent_task_response_success(self):
        """Test successful response creation"""
        response = AgentTaskResponse(
            task_id="task-123",
            status=TaskStatus.SUCCESS,
            data={"result": "completed"},
            execution_time_ms=150.5
        )
        
        assert response.status == TaskStatus.SUCCESS
        assert response.data["result"] == "completed"
        assert response.error_message is None
    
    def test_agent_task_response_failure(self):
        """Test failure response creation"""
        response = AgentTaskResponse(
            task_id="task-123",
            status=TaskStatus.FAILED,
            error_message="Ticket not found",
            error_code="NOT_FOUND"
        )
        
        assert response.status == TaskStatus.FAILED
        assert "not found" in response.error_message.lower()


class TestJiraSchemas:
    """Tests for Jira-related schemas"""
    
    def test_jira_user_creation(self):
        """Test creating a Jira user"""
        user = JiraUser(
            account_id="user-123",
            display_name="John Doe",
            email="john@example.com"
        )
        
        assert user.account_id == "user-123"
        assert user.active is True  # Default
    
    def test_jira_ticket_minimal(self):
        """Test creating minimal Jira ticket"""
        ticket = JiraTicket(
            key="PROJ-123",
            summary="Test ticket",
            status="In Progress"
        )
        
        assert ticket.key == "PROJ-123"
        assert ticket.subtasks == []
    
    def test_jira_ticket_full(self):
        """Test creating full Jira ticket"""
        ticket = JiraTicket(
            key="PROJ-123",
            summary="Full ticket",
            status="In Progress",
            description="A detailed description",
            priority="High",
            story_points=8.0,
            labels=["backend", "api"],
            assignee=JiraUser(
                account_id="user-1",
                display_name="Developer"
            ),
            subtasks=[
                JiraTicket(
                    key="PROJ-124",
                    summary="Subtask 1",
                    status="Done"
                )
            ]
        )
        
        assert ticket.story_points == 8.0
        assert len(ticket.labels) == 2
        assert ticket.assignee.display_name == "Developer"
        assert len(ticket.subtasks) == 1
    
    def test_jira_ticket_serialization(self):
        """Test Jira ticket JSON serialization"""
        ticket = JiraTicket(
            key="PROJ-123",
            summary="Test",
            status="Done",
            created_at=datetime.now()
        )
        
        json_data = ticket.model_dump(mode="json")
        
        assert json_data["key"] == "PROJ-123"
        assert isinstance(json_data["created_at"], str)  # Serialized datetime


class TestBuildSchemas:
    """Tests for CI/CD build schemas"""
    
    def test_build_status_creation(self):
        """Test creating build status"""
        build = BuildStatus(
            job_name="nexus-main",
            build_number=142,
            status=BuildResult.SUCCESS,
            url="https://jenkins.example.com/job/142",
            timestamp=datetime.now(),
            duration_seconds=485.5
        )
        
        assert build.job_name == "nexus-main"
        assert build.status == BuildResult.SUCCESS
    
    def test_build_result_enum(self):
        """Test build result enum values"""
        assert BuildResult.SUCCESS.value == "SUCCESS"
        assert BuildResult.FAILURE.value == "FAILURE"
        assert BuildResult.BUILDING.value == "BUILDING"


class TestSecuritySchemas:
    """Tests for security scan schemas"""
    
    def test_security_scan_result(self):
        """Test security scan result creation"""
        scan = SecurityScanResult(
            repo_name="nexus/backend",
            branch="main",
            risk_score=25,
            critical_vulnerabilities=0,
            high_vulnerabilities=2
        )
        
        assert scan.risk_score == 25
        assert scan.compliant is True  # Default
    
    def test_severity_level_enum(self):
        """Test severity level enum"""
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.HIGH.value == "high"


class TestReleaseSchemas:
    """Tests for release-related schemas"""
    
    def test_release_stats_creation(self):
        """Test creating release stats"""
        stats = ReleaseStats(
            release_version="v2.0.0",
            total_tickets=45,
            completed_tickets=42,
            ticket_completion_rate=93.3,
            go_no_go=ReleaseDecision.GO
        )
        
        assert stats.release_version == "v2.0.0"
        assert stats.go_no_go == ReleaseDecision.GO
    
    def test_release_decision_enum(self):
        """Test release decision enum"""
        assert ReleaseDecision.GO.value == "GO"
        assert ReleaseDecision.NO_GO.value == "NO_GO"
        assert ReleaseDecision.CONDITIONAL.value == "CONDITIONAL"


class TestEnums:
    """Tests for all enum types"""
    
    def test_agent_type_enum(self):
        """Test agent type enum"""
        assert AgentType.JIRA.value == "jira"
        assert AgentType.GIT_CI.value == "git_ci"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
    
    def test_task_status_enum(self):
        """Test task status enum"""
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.PENDING.value == "pending"


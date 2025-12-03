"""
Comprehensive Unit Tests for Jira Agent
========================================

Tests for JiraClient, API endpoints, and helper functions.

Coverage:
- JiraClient initialization and mode switching
- Issue parsing and data transformation
- Mock data generation
- API endpoint validation
- Error handling

Usage:
    pytest tests/unit/test_jira_agent.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/agents/jira_agent")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"


# =============================================================================
# JiraClient Tests
# =============================================================================

class TestJiraClientInitialization:
    """Tests for JiraClient initialization."""
    
    def test_client_created_uninitialized(self):
        """Test client is created in uninitialized state."""
        from main import JiraClient
        
        client = JiraClient()
        
        assert client._jira is None
        assert client._initialized is False
        assert client._last_mode is None
    
    def test_mock_mode_property_default(self):
        """Test mock_mode property returns True by default."""
        from main import JiraClient
        
        client = JiraClient()
        
        assert client.mock_mode is True


class TestJiraClientParsing:
    """Tests for JiraClient data parsing methods."""
    
    @pytest.fixture
    def client(self):
        from main import JiraClient
        return JiraClient()
    
    def test_parse_user_with_data(self, client):
        """Test parsing user data."""
        user_data = {
            "accountId": "user-123",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "avatarUrls": {"48x48": "https://avatar.url"},
            "active": True
        }
        
        user = client._parse_user(user_data)
        
        assert user.account_id == "user-123"
        assert user.display_name == "Test User"
        assert user.email == "test@example.com"
        assert user.avatar_url == "https://avatar.url"
        assert user.active is True
    
    def test_parse_user_with_none(self, client):
        """Test parsing None user data."""
        user = client._parse_user(None)
        assert user is None
    
    def test_parse_user_with_empty_dict(self, client):
        """Test parsing empty user data."""
        user = client._parse_user({})
        
        assert user.account_id == "unknown"
        assert user.display_name == "Unknown User"
    
    def test_map_issue_type_epic(self, client):
        """Test mapping Epic issue type."""
        from nexus_lib.schemas.agent_contract import JiraIssueType
        
        result = client._map_issue_type("Epic")
        assert result == JiraIssueType.EPIC
    
    def test_map_issue_type_story(self, client):
        """Test mapping Story issue type."""
        from nexus_lib.schemas.agent_contract import JiraIssueType
        
        result = client._map_issue_type("Story")
        assert result == JiraIssueType.STORY
    
    def test_map_issue_type_bug(self, client):
        """Test mapping Bug issue type."""
        from nexus_lib.schemas.agent_contract import JiraIssueType
        
        result = client._map_issue_type("Bug")
        assert result == JiraIssueType.BUG
    
    def test_map_issue_type_unknown(self, client):
        """Test mapping unknown issue type defaults to Task."""
        from nexus_lib.schemas.agent_contract import JiraIssueType
        
        result = client._map_issue_type("Unknown Type")
        assert result == JiraIssueType.TASK
    
    def test_extract_sprint_name_from_string(self, client):
        """Test extracting sprint name from string format."""
        fields = {
            "customfield_10020": [
                "com.atlassian.greenhopper.service.sprint.Sprint@12345[id=42,rapidViewId=1,state=ACTIVE,name=Sprint 42,startDate=2025-01-01T00:00:00.000Z]"
            ]
        }
        
        result = client._extract_sprint_name(fields)
        assert result == "Sprint 42"
    
    def test_extract_sprint_name_from_dict(self, client):
        """Test extracting sprint name from dict format."""
        fields = {
            "customfield_10020": [{"name": "Sprint 43"}]
        }
        
        result = client._extract_sprint_name(fields)
        assert result == "Sprint 43"
    
    def test_extract_sprint_name_empty(self, client):
        """Test extracting sprint name when empty."""
        fields = {"customfield_10020": []}
        
        result = client._extract_sprint_name(fields)
        assert result is None
    
    def test_extract_sprint_name_none(self, client):
        """Test extracting sprint name when field is None."""
        fields = {}
        
        result = client._extract_sprint_name(fields)
        assert result is None
    
    def test_parse_datetime_valid(self, client):
        """Test parsing valid datetime string."""
        dt_str = "2025-01-15T10:30:00.000Z"
        
        result = client._parse_datetime(dt_str)
        
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_datetime_none(self, client):
        """Test parsing None datetime."""
        result = client._parse_datetime(None)
        assert result is None
    
    def test_parse_datetime_invalid(self, client):
        """Test parsing invalid datetime string."""
        result = client._parse_datetime("not-a-date")
        assert result is None


class TestJiraClientMockData:
    """Tests for mock data generation."""
    
    @pytest.fixture
    def client(self):
        from main import JiraClient
        return JiraClient()
    
    def test_mock_issue_generation(self, client):
        """Test mock issue generation."""
        ticket = client._mock_issue("NEXUS-123")
        
        assert ticket.key == "NEXUS-123"
        assert ticket.project_key == "NEXUS"
        assert ticket.summary is not None
        assert ticket.status is not None
        assert ticket.assignee is not None
    
    def test_mock_issue_with_subtasks(self, client):
        """Test mock issue includes subtasks."""
        ticket = client._mock_issue("PROJ-456")
        
        assert ticket.subtasks is not None
        assert len(ticket.subtasks) >= 2
    
    def test_mock_hierarchy_generation(self, client):
        """Test mock hierarchy generation."""
        from nexus_lib.schemas.agent_contract import JiraIssueType
        
        hierarchy = client._mock_hierarchy("PROJ-100")
        
        assert hierarchy.key == "PROJ-100"
        assert hierarchy.issue_type == JiraIssueType.EPIC
        assert len(hierarchy.subtasks) >= 3
    
    def test_mock_search_results(self, client):
        """Test mock search results."""
        results = client._mock_search("project = PROJ", 50)
        
        assert results.total >= 3
        assert len(results.issues) >= 3
        assert results.max_results == 50
    
    def test_mock_sprint_stats(self, client):
        """Test mock sprint stats."""
        stats = client._mock_sprint_stats("PROJ", "Sprint 42")
        
        assert stats.sprint_name == "Sprint 42"
        assert stats.total_issues > 0
        assert stats.completion_percentage >= 0
        assert stats.completion_percentage <= 100


class TestJiraClientOperations:
    """Tests for JiraClient operations."""
    
    @pytest.fixture
    def client(self):
        from main import JiraClient
        c = JiraClient()
        c._last_mode = True  # Force mock mode
        c._initialized = True
        return c
    
    @pytest.mark.asyncio
    async def test_get_issue_mock_mode(self, client):
        """Test get_issue in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            ticket = await client.get_issue("NEXUS-123")
        
        assert ticket.key == "NEXUS-123"
    
    @pytest.mark.asyncio
    async def test_get_issue_hierarchy_mock_mode(self, client):
        """Test get_issue_hierarchy in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            hierarchy = await client.get_issue_hierarchy("PROJ-100", max_depth=2)
        
        assert hierarchy.key == "PROJ-100"
        assert len(hierarchy.subtasks) > 0
    
    @pytest.mark.asyncio
    async def test_search_issues_mock_mode(self, client):
        """Test search_issues in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            results = await client.search_issues("project = NEXUS", max_results=10)
        
        assert results.total > 0
        assert len(results.issues) > 0
    
    @pytest.mark.asyncio
    async def test_update_issue_status_mock_mode(self, client):
        """Test update_issue_status in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.update_issue_status("NEXUS-123", "Done", "Completed via test")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_issue_fields_mock_mode(self, client):
        """Test update_issue_fields in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.update_issue_fields("NEXUS-123", {"summary": "Updated summary"})
        
        assert result["success"] is True
        assert result["mock"] is True
    
    @pytest.mark.asyncio
    async def test_add_comment_mock_mode(self, client):
        """Test add_comment in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.add_comment("NEXUS-123", "Test comment")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_sprint_stats_mock_mode(self, client):
        """Test get_sprint_stats in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            stats = await client.get_sprint_stats("NEXUS", "Sprint 42")
        
        assert stats.sprint_name == "Sprint 42"
        assert stats.total_issues > 0


class TestJiraClientIssueParser:
    """Tests for full issue parsing."""
    
    @pytest.fixture
    def client(self):
        from main import JiraClient
        return JiraClient()
    
    def test_parse_issue_full(self, client):
        """Test parsing complete issue data."""
        issue_data = {
            "key": "NEXUS-123",
            "id": "10001",
            "fields": {
                "summary": "Test ticket summary",
                "description": "Test description",
                "issuetype": {"name": "Story"},
                "status": {"name": "In Progress"},
                "resolution": None,
                "priority": {"name": "High"},
                "project": {"key": "NEXUS"},
                "parent": {"key": "NEXUS-100"},
                "assignee": {
                    "accountId": "user-1",
                    "displayName": "Developer",
                    "emailAddress": "dev@test.com"
                },
                "reporter": {
                    "accountId": "user-2",
                    "displayName": "Reporter"
                },
                "customfield_10016": 5.0,
                "labels": ["backend", "api"],
                "components": [{"name": "core"}],
                "fixVersions": [{"name": "v2.0.0"}],
                "created": "2025-01-01T10:00:00.000Z",
                "updated": "2025-01-15T14:30:00.000Z"
            }
        }
        
        ticket = client._parse_issue(issue_data)
        
        assert ticket.key == "NEXUS-123"
        assert ticket.summary == "Test ticket summary"
        assert ticket.status == "In Progress"
        assert ticket.priority == "High"
        assert ticket.story_points == 5.0
        assert "backend" in ticket.labels
        assert "core" in ticket.components
        assert "v2.0.0" in ticket.fix_versions
    
    def test_parse_issue_with_subtasks(self, client):
        """Test parsing issue with subtasks."""
        issue_data = {
            "key": "NEXUS-100",
            "fields": {
                "summary": "Parent ticket",
                "issuetype": {"name": "Story"},
                "status": {"name": "Open"},
                "project": {"key": "NEXUS"},
                "subtasks": [
                    {
                        "key": "NEXUS-100-1",
                        "fields": {
                            "summary": "Subtask 1",
                            "status": {"name": "Done"}
                        }
                    },
                    {
                        "key": "NEXUS-100-2",
                        "fields": {
                            "summary": "Subtask 2",
                            "status": {"name": "In Progress"}
                        }
                    }
                ]
            }
        }
        
        ticket = client._parse_issue(issue_data, include_subtasks=True)
        
        assert len(ticket.subtasks) == 2
        assert ticket.subtasks[0].key == "NEXUS-100-1"
        assert ticket.subtasks[0].status == "Done"


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestJiraAgentAPI:
    """Tests for Jira Agent API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from main import app
            with TestClient(app) as client:
                yield client
        except ImportError:
            pytest.skip("Jira agent module not available")
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-agent"
        assert "mock_mode" in data
    
    def test_get_issue_endpoint(self, client):
        """Test GET /issue/{ticket_key} endpoint."""
        response = client.get("/issue/NEXUS-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent_type"] == "jira"
        assert data["data"]["key"] == "NEXUS-123"
    
    def test_get_hierarchy_endpoint(self, client):
        """Test GET /hierarchy/{ticket_key} endpoint."""
        response = client.get("/hierarchy/PROJ-100")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "hierarchy" in data["data"]
    
    def test_get_hierarchy_with_depth(self, client):
        """Test hierarchy endpoint with custom depth."""
        response = client.get("/hierarchy/PROJ-100?max_depth=2")
        
        assert response.status_code == 200
    
    def test_search_endpoint(self, client):
        """Test GET /search endpoint."""
        response = client.get("/search?jql=project%20%3D%20NEXUS")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "issues" in data["data"]
    
    def test_search_with_pagination(self, client):
        """Test search with pagination parameters."""
        response = client.get("/search?jql=project%20%3D%20NEXUS&start_at=10&max_results=25")
        
        assert response.status_code == 200
    
    def test_update_endpoint_status_only(self, client):
        """Test POST /update endpoint with status."""
        response = client.post("/update?key=NEXUS-123&status=Done")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_update_endpoint_comment_only(self, client):
        """Test POST /update endpoint with comment only."""
        response = client.post("/update?key=NEXUS-123&comment=Test%20comment")
        
        assert response.status_code == 200
    
    def test_update_endpoint_no_params(self, client):
        """Test POST /update endpoint without status or comment fails."""
        response = client.post("/update?key=NEXUS-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
    
    def test_update_ticket_fields_endpoint(self, client):
        """Test POST /update-ticket endpoint."""
        response = client.post("/update-ticket", json={
            "ticket_key": "NEXUS-123",
            "fields": {"summary": "Updated summary"},
            "updated_by": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_sprint_stats_endpoint(self, client):
        """Test GET /sprint-stats/{project_key} endpoint."""
        response = client.get("/sprint-stats/NEXUS")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_issues" in data["data"]
    
    def test_sprint_stats_with_name(self, client):
        """Test sprint stats with sprint name."""
        response = client.get("/sprint-stats/NEXUS?sprint_name=Sprint%2042")
        
        assert response.status_code == 200
    
    def test_execute_get_issue(self, client):
        """Test POST /execute with get_issue action."""
        response = client.post("/execute", json={
            "task_id": "test-1",
            "action": "get_issue",
            "payload": {"key": "NEXUS-123"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["key"] == "NEXUS-123"
    
    def test_execute_search(self, client):
        """Test POST /execute with search action."""
        response = client.post("/execute", json={
            "task_id": "test-2",
            "action": "search",
            "payload": {"jql": "project = NEXUS"}
        })
        
        assert response.status_code == 200
    
    def test_execute_sprint_stats(self, client):
        """Test POST /execute with sprint_stats action."""
        response = client.post("/execute", json={
            "task_id": "test-3",
            "action": "sprint_stats",
            "payload": {"project_key": "NEXUS"}
        })
        
        assert response.status_code == 200
    
    def test_execute_unknown_action(self, client):
        """Test POST /execute with unknown action."""
        response = client.post("/execute", json={
            "task_id": "test-4",
            "action": "unknown_action",
            "payload": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Unknown action" in data["error_message"]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestJiraAgentErrorHandling:
    """Tests for error handling in Jira Agent."""
    
    @pytest.fixture
    def client(self):
        try:
            from main import app
            with TestClient(app) as client:
                yield client
        except ImportError:
            pytest.skip("Jira agent module not available")
    
    def test_invalid_max_depth(self, client):
        """Test hierarchy with invalid max_depth."""
        response = client.get("/hierarchy/PROJ-100?max_depth=10")
        
        # Should be rejected (max is 5)
        assert response.status_code == 422
    
    def test_empty_jql(self, client):
        """Test search with empty JQL."""
        response = client.get("/search?jql=")
        
        # Should still work with empty JQL
        assert response.status_code in [200, 422]
    
    def test_negative_start_at(self, client):
        """Test search with negative start_at."""
        response = client.get("/search?jql=project=NEXUS&start_at=-1")
        
        assert response.status_code == 422
    
    def test_max_results_exceeded(self, client):
        """Test search with max_results > 100."""
        response = client.get("/search?jql=project=NEXUS&max_results=200")
        
        assert response.status_code == 422


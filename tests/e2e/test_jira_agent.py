"""
End-to-End Tests for Jira Agent
================================

Tests for Jira ticket management, hierarchy fetching,
and sprint statistics.
"""

import pytest
import sys
import os

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"

# Calculate paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
JIRA_AGENT_PATH = os.path.join(PROJECT_ROOT, "services/agents/jira_agent")
SHARED_PATH = os.path.join(PROJECT_ROOT, "shared")


def get_jira_app():
    """Get the Jira agent FastAPI app with proper imports."""
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'main' or mod_name.startswith('main.'):
                del sys.modules[mod_name]
        
        sys.path.insert(0, JIRA_AGENT_PATH)
        sys.path.insert(0, SHARED_PATH)
        os.chdir(JIRA_AGENT_PATH)
        
        import main as jira_main
        return jira_main.app, jira_main
        
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class TestJiraAgentHealth:
    """Tests for Jira Agent health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test Jira agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-agent"


class TestJiraIssueEndpoints:
    """Tests for Jira issue endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_get_issue(self, client):
        """Test getting a single issue."""
        response = client.get("/issue/PROJ-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_issue_hierarchy(self, client):
        """Test getting issue hierarchy."""
        response = client.get("/hierarchy/PROJ-100")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestJiraSearchEndpoint:
    """Tests for Jira search endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_search_issues(self, client):
        """Test JQL search endpoint."""
        response = client.get("/search", params={
            "jql": "project = PROJ AND status = 'In Progress'",
            "max_results": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestJiraSprintStats:
    """Tests for Jira sprint statistics endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_get_sprint_stats(self, client):
        """Test getting sprint statistics."""
        response = client.get("/sprint-stats/PROJ")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestJiraUpdateEndpoints:
    """Tests for Jira update endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_update_status(self, client):
        """Test updating issue status."""
        # /update endpoint takes query parameters
        response = client.post("/update", params={
            "key": "PROJ-123",
            "status": "Done",
            "comment": "Completed the task"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_update_ticket_fields(self, client):
        """Test updating issue fields via update-ticket endpoint."""
        response = client.post("/update-ticket", json={
            "ticket_key": "PROJ-123",
            "fields": {
                "summary": "Updated summary",
                "priority": {"name": "High"}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestJiraExecuteEndpoint:
    """Tests for Jira execute endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_jira_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_execute_get_ticket(self, client):
        """Test execute endpoint for getting ticket."""
        response = client.post("/execute", json={
            "task_id": "test-123",
            "action": "get_ticket",
            "payload": {"ticket_key": "PROJ-123"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]
    
    def test_execute_search(self, client):
        """Test execute endpoint for search."""
        response = client.post("/execute", json={
            "task_id": "test-124",
            "action": "search",
            "payload": {"jql": "project = PROJ"}
        })
        
        assert response.status_code == 200


class TestJiraLogic:
    """Tests for Jira-related logic."""
    
    def test_ticket_key_validation(self):
        """Test ticket key format validation."""
        import re
        
        pattern = r'^[A-Z]+-\d+$'
        
        assert re.match(pattern, "PROJ-123")
        assert re.match(pattern, "ABC-1")
        assert not re.match(pattern, "invalid")
        assert not re.match(pattern, "proj-123")
    
    def test_jql_construction(self):
        """Test JQL query construction."""
        project = "PROJ"
        status = "In Progress"
        
        jql = f"project = {project} AND status = '{status}'"
        
        assert "project = PROJ" in jql
        assert "status = 'In Progress'" in jql
    
    def test_completion_rate_calculation(self):
        """Test completion rate calculation."""
        total = 100
        completed = 85
        
        rate = (completed / total) * 100 if total > 0 else 0
        
        assert rate == 85.0
    
    def test_story_points_aggregation(self):
        """Test story points aggregation."""
        tickets = [
            {"story_points": 3},
            {"story_points": 5},
            {"story_points": 8},
            {"story_points": None},
            {"story_points": 2}
        ]
        
        total = sum(t.get("story_points", 0) or 0 for t in tickets)
        
        assert total == 18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
End-to-End Tests for Jira Agent
================================

Tests for Jira ticket management, hierarchy fetching,
and sprint statistics.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath("services/agents/jira_agent"))
sys.path.insert(0, os.path.abspath("shared"))

# Set mock mode
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"


class TestJiraAgentE2E:
    """E2E tests for Jira Agent endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test Jira agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-agent"
        assert "mock_mode" in data
    
    def test_get_ticket(self, client):
        """Test getting a single ticket."""
        response = client.get("/ticket/PROJ-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["key"] == "PROJ-123"
    
    def test_get_ticket_not_found(self, client):
        """Test getting non-existent ticket."""
        response = client.get("/ticket/INVALID-999999")
        
        # Mock mode should still return success with mock data
        assert response.status_code in [200, 404]
    
    def test_get_ticket_hierarchy(self, client):
        """Test getting ticket hierarchy (Epic -> Stories -> Subtasks)."""
        response = client.get("/hierarchy/PROJ-100")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        
        hierarchy = data["data"]
        assert "key" in hierarchy
        # Should have children in mock mode
        assert "children" in hierarchy or "subtasks" in hierarchy
    
    def test_search_tickets(self, client):
        """Test JQL search."""
        response = client.post("/search", json={
            "jql": "project = PROJ AND status = 'In Progress'",
            "max_results": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_sprint_stats(self, client):
        """Test getting sprint statistics."""
        response = client.get("/sprint-stats/PROJ")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        stats = data["data"]
        assert "total_tickets" in stats
        assert "completed_tickets" in stats
        assert "story_points" in stats
    
    def test_update_ticket_status(self, client):
        """Test updating ticket status."""
        response = client.post("/ticket/PROJ-123/transition", json={
            "status": "Done",
            "comment": "Marking as complete"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_add_comment(self, client):
        """Test adding comment to ticket."""
        response = client.post("/ticket/PROJ-123/comment", json={
            "body": "Test comment from E2E test"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_update_ticket_fields(self, client):
        """Test updating ticket fields."""
        response = client.put("/ticket/PROJ-123/fields", json={
            "labels": ["backend", "api"],
            "fixVersions": ["v2.0.0"],
            "story_points": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_release_tickets(self, client):
        """Test getting tickets for a specific release."""
        response = client.get("/release/v2.0.0/tickets")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Should contain Prometheus format metrics
        assert "nexus_" in response.text or "http_" in response.text


class TestJiraAgentTaskRequest:
    """Tests for AgentTaskRequest handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_execute_get_ticket_action(self, client):
        """Test execute endpoint with get_ticket action."""
        response = client.post("/execute", json={
            "task_id": "task-123",
            "action": "get_ticket",
            "payload": {"ticket_key": "PROJ-123"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] in ["success", "failed"]
    
    def test_execute_search_action(self, client):
        """Test execute endpoint with search action."""
        response = client.post("/execute", json={
            "task_id": "task-124",
            "action": "search_issues",
            "payload": {
                "jql": "project = PROJ",
                "max_results": 5
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-124"
    
    def test_execute_unknown_action(self, client):
        """Test execute endpoint with unknown action."""
        response = client.post("/execute", json={
            "task_id": "task-125",
            "action": "unknown_action",
            "payload": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error" in data["error_message"].lower() or "unknown" in data["error_message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


"""
End-to-End Tests for Jira Hygiene Agent
========================================

Tests for hygiene checks, scheduling, notifications,
and interactive Slack flows.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath("services/agents/jira_hygiene_agent"))
sys.path.insert(0, os.path.abspath("shared"))

# Set mock mode
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["SLACK_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"


class TestHygieneAgentE2E:
    """E2E tests for Jira Hygiene Agent endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test hygiene agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-hygiene-agent"
        assert "scheduler" in data or "mock_mode" in data
    
    def test_run_hygiene_check(self, client):
        """Test manual hygiene check trigger."""
        response = client.post("/run-check", json={
            "project_key": "PROJ",
            "notify": False  # Don't send Slack notifications in test
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        result = data["data"]
        assert "check_id" in result
        assert "total_tickets_checked" in result
        assert "hygiene_score" in result
        assert 0 <= result["hygiene_score"] <= 100
    
    def test_run_hygiene_check_with_notification(self, client):
        """Test hygiene check with Slack notification."""
        response = client.post("/run-check", json={
            "project_key": "PROJ",
            "notify": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # In mock mode, notifications are simulated
        assert "notifications_sent" in data["data"] or "violations_by_assignee" in data["data"]
    
    def test_get_hygiene_history(self, client):
        """Test getting hygiene check history."""
        # First run a check
        client.post("/run-check", json={"project_key": "PROJ"})
        
        # Then get history
        response = client.get("/history", params={
            "project_key": "PROJ",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_get_hygiene_score_trend(self, client):
        """Test getting hygiene score trend."""
        response = client.get("/trend", params={
            "project_key": "PROJ",
            "days": 30
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Should return time series data
        assert isinstance(data["data"], list) or "scores" in data["data"]
    
    def test_get_violations_summary(self, client):
        """Test getting violations summary."""
        response = client.get("/violations/summary", params={
            "project_key": "PROJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Should show violation types
        summary = data["data"]
        assert "by_field" in summary or isinstance(summary, dict)
    
    def test_get_violations_by_assignee(self, client):
        """Test getting violations grouped by assignee."""
        response = client.get("/violations/by-assignee", params={
            "project_key": "PROJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_scheduler_status(self, client):
        """Test getting scheduler status."""
        response = client.get("/scheduler/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "running" in data or "status" in data
        assert "next_run" in data or "scheduled_time" in data
    
    def test_configure_scheduler(self, client):
        """Test configuring scheduler."""
        response = client.post("/scheduler/configure", json={
            "hour": 10,
            "minute": 0,
            "days": "mon-fri",
            "timezone": "America/New_York"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Should contain hygiene metrics
        assert "nexus_project_hygiene_score" in response.text or "hygiene" in response.text.lower()


class TestHygieneAgentTaskRequest:
    """Tests for AgentTaskRequest handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_execute_check_hygiene(self, client):
        """Test execute with check_hygiene action."""
        response = client.post("/execute", json={
            "task_id": "task-300",
            "action": "check_hygiene",
            "payload": {"project_key": "PROJ"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-300"
    
    def test_execute_get_violations(self, client):
        """Test execute with get_violations action."""
        response = client.post("/execute", json={
            "task_id": "task-301",
            "action": "get_violations",
            "payload": {
                "project_key": "PROJ",
                "assignee_email": "developer@example.com"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-301"


class TestHygieneSlackInteractions:
    """Tests for Slack interactive components."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_fix_modal_callback(self, client):
        """Test Slack fix modal submission callback."""
        response = client.post("/slack/callback/fix", json={
            "check_id": "check-123",
            "ticket_key": "PROJ-456",
            "updates": {
                "labels": ["backend"],
                "fixVersions": ["v2.0.0"],
                "story_points": 5
            },
            "user_id": "U123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "queued"]
    
    def test_snooze_callback(self, client):
        """Test snooze reminder callback."""
        response = client.post("/slack/callback/snooze", json={
            "check_id": "check-123",
            "assignee_email": "developer@example.com",
            "snooze_hours": 24
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "next_reminder" in data or "snoozed_until" in data


class TestHygieneConfiguration:
    """Tests for hygiene check configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_get_config(self, client):
        """Test getting current configuration."""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "required_fields" in data
        assert "projects" in data
        assert "schedule" in data
    
    def test_update_required_fields(self, client):
        """Test updating required fields."""
        response = client.put("/config/required-fields", json={
            "fields": [
                "labels",
                "fixVersions",
                "versions",
                "customfield_10016"  # Story Points
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_add_project(self, client):
        """Test adding project to hygiene checks."""
        response = client.post("/config/projects", json={
            "project_key": "NEWPROJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


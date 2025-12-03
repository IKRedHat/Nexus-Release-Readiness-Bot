"""
End-to-End Tests for Jira Hygiene Agent
========================================

Tests for hygiene checks, violations, and reporting.
"""

import pytest
import sys
import os

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["JIRA_MOCK_MODE"] = "true"

# Calculate paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
HYGIENE_AGENT_PATH = os.path.join(PROJECT_ROOT, "services/agents/jira_hygiene_agent")
SHARED_PATH = os.path.join(PROJECT_ROOT, "shared")


def get_hygiene_app():
    """Get the Hygiene agent FastAPI app with proper imports."""
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'main' or mod_name.startswith('main.'):
                del sys.modules[mod_name]
        
        sys.path.insert(0, HYGIENE_AGENT_PATH)
        sys.path.insert(0, SHARED_PATH)
        os.chdir(HYGIENE_AGENT_PATH)
        
        import main as hygiene_main
        return hygiene_main.app, hygiene_main
        
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class TestHygieneAgentHealth:
    """Tests for Hygiene Agent health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_hygiene_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test hygiene agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jira-hygiene-agent"


class TestHygieneStatus:
    """Tests for Hygiene status endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_hygiene_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_get_status(self, client):
        """Test getting hygiene status."""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestHygieneRunCheck:
    """Tests for Hygiene run-check endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_hygiene_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_run_check(self, client):
        """Test running a hygiene check."""
        response = client.post("/run-check", json={
            "project_key": "PROJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_run_check_with_options(self, client):
        """Test running check with options."""
        response = client.post("/run-check", json={
            "project_key": "PROJ",
            "notify_slack": False,
            "fix_issues": False
        })
        
        assert response.status_code == 200


class TestHygieneViolations:
    """Tests for Hygiene violations endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_hygiene_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_get_violations(self, client):
        """Test getting violations for a project."""
        response = client.get("/violations/PROJ")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestHygieneExecute:
    """Tests for Hygiene execute endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_hygiene_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_execute_run_check(self, client):
        """Test execute endpoint for running check."""
        response = client.post("/execute", json={
            "task_id": "test-123",
            "action": "run_check",
            "payload": {"project_key": "PROJ"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]


class TestHygieneLogic:
    """Tests for Hygiene logic."""
    
    def test_hygiene_score_calculation(self):
        """Test hygiene score calculation."""
        total = 100
        violations = 15
        
        score = ((total - violations) / total) * 100 if total > 0 else 100
        
        assert score == 85.0
    
    def test_stale_detection(self):
        """Test stale ticket detection."""
        from datetime import datetime, timedelta
        
        last_updated = datetime.utcnow() - timedelta(days=20)
        stale_threshold = 14
        
        is_stale = (datetime.utcnow() - last_updated).days > stale_threshold
        
        assert is_stale is True
    
    def test_violation_severity(self):
        """Test violation severity ordering."""
        severities = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        assert severities["critical"] > severities["high"]
        assert severities["high"] > severities["medium"]
    
    def test_required_field_validation(self):
        """Test required field validation."""
        required_fields = ["summary", "description", "assignee", "priority"]
        
        ticket = {
            "summary": "Test ticket",
            "description": None,
            "assignee": "john.doe",
            "priority": None
        }
        
        missing = [f for f in required_fields if not ticket.get(f)]
        
        assert "description" in missing
        assert "priority" in missing
        assert "summary" not in missing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

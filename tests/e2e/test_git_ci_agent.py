"""
End-to-End Tests for Git/CI Agent
==================================

Tests for Git repository management and CI integration.
"""

import pytest
import sys
import os

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["JENKINS_MOCK_MODE"] = "true"

# Calculate paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
GIT_CI_AGENT_PATH = os.path.join(PROJECT_ROOT, "services/agents/git_ci_agent")
SHARED_PATH = os.path.join(PROJECT_ROOT, "shared")


def get_git_ci_app():
    """Get the Git/CI agent FastAPI app with proper imports."""
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'main' or mod_name.startswith('main.'):
                del sys.modules[mod_name]
        
        sys.path.insert(0, GIT_CI_AGENT_PATH)
        sys.path.insert(0, SHARED_PATH)
        os.chdir(GIT_CI_AGENT_PATH)
        
        import main as git_ci_main
        return git_ci_main.app, git_ci_main
        
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class TestGitCIAgentHealth:
    """Tests for Git/CI Agent health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_git_ci_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test Git/CI agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "git-ci-agent"


class TestGitRepoEndpoints:
    """Tests for Git repository endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_git_ci_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_repo_health(self, client):
        """Test getting repository health."""
        response = client.get("/repo/nexus-backend/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_pr_status(self, client):
        """Test getting PR status."""
        response = client.get("/repo/nexus-backend/pr/123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_list_open_prs(self, client):
        """Test listing open PRs."""
        response = client.get("/repo/nexus-backend/prs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestCIBuildEndpoints:
    """Tests for CI build endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_git_ci_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_trigger_build(self, client):
        """Test triggering a build."""
        response = client.post("/build/nexus-main")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_build_status(self, client):
        """Test getting build status."""
        response = client.get("/build/nexus-main/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_build_history(self, client):
        """Test getting build history."""
        response = client.get("/build/nexus-main/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestSecurityEndpoints:
    """Tests for security scan endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_git_ci_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_get_security_scan(self, client):
        """Test getting security scan results."""
        response = client.get("/security/nexus-backend")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestGitCIExecuteEndpoint:
    """Tests for Git/CI execute endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_git_ci_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_execute_get_build_status(self, client):
        """Test execute endpoint for build status."""
        response = client.post("/execute", json={
            "task_id": "test-123",
            "action": "get_build_status",
            "payload": {"job_name": "nexus-main"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]


class TestGitCILogic:
    """Tests for Git/CI related logic."""
    
    def test_build_status_mapping(self):
        """Test build status to result mapping."""
        status_map = {
            "SUCCESS": "passed",
            "FAILURE": "failed",
            "ABORTED": "cancelled",
            "UNSTABLE": "unstable"
        }
        
        assert status_map["SUCCESS"] == "passed"
        assert status_map["FAILURE"] == "failed"
    
    def test_pr_state_detection(self):
        """Test PR state detection."""
        pr = {
            "state": "open",
            "mergeable": True,
            "ci_status": "success"
        }
        
        is_ready = (
            pr["state"] == "open" and
            pr["mergeable"] and
            pr["ci_status"] == "success"
        )
        
        assert is_ready is True
    
    def test_vulnerability_severity_count(self):
        """Test vulnerability severity counting."""
        vulnerabilities = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"}
        ]
        
        severity_counts = {}
        for v in vulnerabilities:
            sev = v["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        assert severity_counts["critical"] == 1
        assert severity_counts["high"] == 2
        assert severity_counts["medium"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

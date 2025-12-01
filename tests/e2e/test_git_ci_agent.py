"""
End-to-End Tests for Git/CI Agent
==================================

Tests for GitHub integration, Jenkins build management,
and repository health checks.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath("services/agents/git_ci_agent"))
sys.path.insert(0, os.path.abspath("shared"))

# Set mock mode
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["JENKINS_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"


class TestGitCIAgentE2E:
    """E2E tests for Git/CI Agent endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test Git/CI agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "git-ci-agent"
        assert "github" in data or "jenkins" in data
    
    # --- GitHub Endpoints ---
    
    def test_get_repo_health(self, client):
        """Test getting repository health."""
        response = client.get("/github/repo/nexus-backend/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        
        health = data["data"]
        assert "open_issues" in health or "stars" in health
    
    def test_get_pr_status(self, client):
        """Test getting PR status."""
        response = client.get("/github/repo/nexus-backend/pr/123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        pr = data["data"]
        assert "number" in pr or "state" in pr
    
    def test_list_open_prs(self, client):
        """Test listing open PRs."""
        response = client.get("/github/repo/nexus-backend/prs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_get_commit_info(self, client):
        """Test getting commit information."""
        response = client.get("/github/repo/nexus-backend/commit/abc123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_file_diff(self, client):
        """Test getting file diff between branches."""
        response = client.get("/github/repo/nexus-backend/diff", params={
            "base": "main",
            "head": "feature/new-api"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    # --- Jenkins Endpoints ---
    
    def test_get_build_status(self, client):
        """Test getting build status."""
        response = client.get("/jenkins/job/nexus-main/build/142")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        build = data["data"]
        assert "status" in build or "result" in build
        assert "build_number" in build or "number" in build
    
    def test_get_latest_build(self, client):
        """Test getting latest build for a job."""
        response = client.get("/jenkins/job/nexus-main/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_trigger_build(self, client):
        """Test triggering a new build."""
        response = client.post("/jenkins/job/nexus-main/build", json={
            "parameters": {
                "BRANCH": "main",
                "DEPLOY_ENV": "staging"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "queue_id" in data["data"] or "build_number" in data["data"]
    
    def test_get_job_history(self, client):
        """Test getting job build history."""
        response = client.get("/jenkins/job/nexus-main/history", params={
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_get_build_logs(self, client):
        """Test getting build console logs."""
        response = client.get("/jenkins/job/nexus-main/build/142/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Logs should be a string
        assert isinstance(data["data"], str) or "logs" in data["data"]
    
    def test_get_build_artifacts(self, client):
        """Test getting build artifacts."""
        response = client.get("/jenkins/job/nexus-main/build/142/artifacts")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    # --- Security Endpoints ---
    
    def test_get_security_scan(self, client):
        """Test getting security scan results."""
        response = client.get("/security/repo/nexus-backend/scan")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        scan = data["data"]
        assert "risk_score" in scan or "vulnerabilities" in scan
    
    def test_get_dependency_vulnerabilities(self, client):
        """Test getting dependency vulnerabilities."""
        response = client.get("/security/repo/nexus-backend/dependencies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestGitCIAgentTaskRequest:
    """Tests for AgentTaskRequest handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_execute_get_build_status(self, client):
        """Test execute with get_build_status action."""
        response = client.post("/execute", json={
            "task_id": "task-200",
            "action": "get_build_status",
            "payload": {
                "job_name": "nexus-main",
                "build_number": 142
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-200"
    
    def test_execute_trigger_build(self, client):
        """Test execute with trigger_build action."""
        response = client.post("/execute", json={
            "task_id": "task-201",
            "action": "trigger_build",
            "payload": {
                "job_name": "nexus-main",
                "parameters": {"BRANCH": "main"}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-201"
    
    def test_execute_get_repo_health(self, client):
        """Test execute with get_repo_health action."""
        response = client.post("/execute", json={
            "task_id": "task-202",
            "action": "get_repo_health",
            "payload": {"repo_name": "nexus-backend"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-202"
    
    def test_execute_get_security_scan(self, client):
        """Test execute with get_security_scan action."""
        response = client.post("/execute", json={
            "task_id": "task-203",
            "action": "get_security_scan",
            "payload": {
                "repo_name": "nexus-backend",
                "branch": "main"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-203"


class TestBuildWebhooks:
    """Tests for Jenkins webhook handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_jenkins_webhook_build_complete(self, client):
        """Test handling Jenkins build completion webhook."""
        webhook_payload = {
            "name": "nexus-main",
            "build": {
                "number": 143,
                "status": "SUCCESS",
                "url": "https://jenkins.example.com/job/nexus-main/143/",
                "duration": 485000
            }
        }
        
        response = client.post("/webhook/jenkins", json=webhook_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
    
    def test_jenkins_webhook_build_failed(self, client):
        """Test handling Jenkins build failure webhook."""
        webhook_payload = {
            "name": "nexus-main",
            "build": {
                "number": 144,
                "status": "FAILURE",
                "url": "https://jenkins.example.com/job/nexus-main/144/"
            }
        }
        
        response = client.post("/webhook/jenkins", json=webhook_payload)
        
        assert response.status_code == 200
        # Failed builds should trigger RCA or notifications


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


"""
End-to-End Tests for RCA Agent
==============================

Tests for Root Cause Analysis, auto-triggering,
and Slack notifications.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import hmac
import hashlib

sys.path.insert(0, os.path.abspath("services/agents/rca_agent"))
sys.path.insert(0, os.path.abspath("shared"))

# Set mock mode
os.environ["JENKINS_MOCK_MODE"] = "true"
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["LLM_MOCK_MODE"] = "true"
os.environ["SLACK_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"
os.environ["RCA_AUTO_ANALYZE"] = "true"
os.environ["RCA_SLACK_NOTIFY"] = "true"


class TestRcaAgentE2E:
    """E2E tests for RCA Agent endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test RCA agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rca-agent"
        assert "mock_mode" in data
    
    def test_analyze_build_failure(self, client):
        """Test analyzing a build failure."""
        response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 142,
            "repo_name": "nexus-backend"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        analysis = data["data"]
        assert "analysis_id" in analysis
        assert "root_cause_summary" in analysis
        assert "confidence_score" in analysis
        assert 0 <= analysis["confidence_score"] <= 1
    
    def test_analyze_with_pr(self, client):
        """Test analysis with PR context."""
        response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 143,
            "repo_name": "nexus-backend",
            "pr_id": 456,
            "include_git_diff": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        analysis = data["data"]
        # Should include git diff context
        assert "suspected_files" in analysis or "git_diff_context" in analysis
    
    def test_analyze_with_commit_sha(self, client):
        """Test analysis with specific commit."""
        response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 144,
            "commit_sha": "abc123def456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_analysis_history(self, client):
        """Test getting analysis history."""
        # First create an analysis
        client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 145
        })
        
        # Then get history
        response = client.get("/history", params={
            "job_name": "nexus-main",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
    
    def test_get_analysis_by_id(self, client):
        """Test getting specific analysis by ID."""
        # First create an analysis
        create_response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 146
        })
        analysis_id = create_response.json()["data"]["analysis_id"]
        
        # Get by ID
        response = client.get(f"/analysis/{analysis_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["analysis_id"] == analysis_id
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Should contain RCA metrics
        assert "nexus_rca_" in response.text


class TestRcaWebhook:
    """Tests for Jenkins webhook auto-triggering."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def generate_signature(self, payload: dict, secret: str) -> str:
        """Generate HMAC signature for webhook."""
        payload_str = json.dumps(payload)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def test_webhook_build_failure_triggers_rca(self, client):
        """Test that build failure webhook triggers RCA."""
        payload = {
            "name": "nexus-main",
            "url": "job/nexus-main/",
            "build": {
                "number": 147,
                "status": "FAILURE",
                "url": "job/nexus-main/147/",
                "phase": "COMPLETED",
                "scm": {
                    "commit": "abc123",
                    "branch": "main"
                }
            }
        }
        
        response = client.post(
            "/webhook/jenkins",
            json=payload,
            headers={
                "X-Jenkins-Signature": self.generate_signature(
                    payload,
                    os.environ.get("JENKINS_WEBHOOK_SECRET", "test-secret")
                )
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["received", "analyzing"]
        # RCA should be triggered
        assert "analysis_id" in data or "queued" in data
    
    def test_webhook_build_success_no_rca(self, client):
        """Test that successful build doesn't trigger RCA."""
        payload = {
            "name": "nexus-main",
            "build": {
                "number": 148,
                "status": "SUCCESS",
                "phase": "COMPLETED"
            }
        }
        
        response = client.post("/webhook/jenkins", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        # No RCA for successful builds
        assert "analysis_id" not in data
    
    def test_webhook_with_pr_info(self, client):
        """Test webhook with PR information."""
        payload = {
            "name": "nexus-main",
            "build": {
                "number": 149,
                "status": "FAILURE",
                "phase": "COMPLETED",
                "scm": {
                    "commit": "def456",
                    "branch": "feature/new-api"
                },
                "parameters": {
                    "ghprbPullId": "789",
                    "ghprbActualCommit": "def456"
                }
            }
        }
        
        response = client.post("/webhook/jenkins", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # Should extract PR info for analysis
        assert data["status"] in ["received", "analyzing"]


class TestRcaSlackNotifications:
    """Tests for Slack notification integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_send_rca_notification(self, client):
        """Test sending RCA notification to Slack."""
        response = client.post("/notify/slack", json={
            "analysis_id": "rca-test-123",
            "channel": "#release-notifications",
            "pr_owner_email": "developer@example.com",
            "root_cause_summary": "Null pointer exception in UserService.validateEmail()",
            "confidence_score": 0.85,
            "fix_suggestion": "Add null check before accessing email property"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message_ts" in data or "notification_sent" in data
    
    def test_notification_includes_pr_owner_tag(self, client):
        """Test that notification tags PR owner."""
        response = client.post("/notify/slack", json={
            "analysis_id": "rca-test-124",
            "channel": "#releases",
            "pr_owner_email": "alice@example.com",
            "root_cause_summary": "Test failure",
            "confidence_score": 0.9,
            "tag_owner": True
        })
        
        assert response.status_code == 200
        # Notification should include user tag
        data = response.json()
        assert data["status"] == "success"
    
    def test_full_rca_flow_with_notification(self, client):
        """Test complete RCA flow: analyze -> notify."""
        # 1. Trigger analysis
        analyze_response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 150,
            "repo_name": "nexus-backend",
            "pr_id": 100
        })
        
        assert analyze_response.status_code == 200
        analysis = analyze_response.json()["data"]
        
        # 2. Send notification (in mock mode)
        notify_response = client.post("/notify/slack", json={
            "analysis_id": analysis["analysis_id"],
            "channel": "#releases",
            "root_cause_summary": analysis["root_cause_summary"],
            "confidence_score": analysis["confidence_score"]
        })
        
        assert notify_response.status_code == 200


class TestRcaAgentTaskRequest:
    """Tests for AgentTaskRequest handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_execute_analyze_build(self, client):
        """Test execute with analyze_build action."""
        response = client.post("/execute", json={
            "task_id": "task-400",
            "action": "analyze_build_failure",
            "payload": {
                "job_name": "nexus-main",
                "build_number": 151
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-400"
        assert data["status"] in ["success", "failed"]
    
    def test_execute_get_analysis(self, client):
        """Test execute with get_analysis action."""
        response = client.post("/execute", json={
            "task_id": "task-401",
            "action": "get_analysis",
            "payload": {
                "analysis_id": "rca-test-123"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-401"


class TestRcaConfiguration:
    """Tests for RCA configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_get_config(self, client):
        """Test getting RCA configuration."""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "auto_analyze_enabled" in data
        assert "slack_notify_enabled" in data
        assert "llm_model" in data
    
    def test_update_config(self, client):
        """Test updating RCA configuration."""
        response = client.put("/config", json={
            "auto_analyze_enabled": True,
            "slack_notify_enabled": True,
            "slack_channel": "#build-alerts",
            "max_log_size": 100000
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


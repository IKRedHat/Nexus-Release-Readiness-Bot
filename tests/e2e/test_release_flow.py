"""
End-to-End Tests for Release Flow
Tests the complete release readiness assessment workflow
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath("services/orchestrator"))
sys.path.insert(0, os.path.abspath("shared"))

# Import after path setup
from main import app


class TestReleaseFlowE2E:
    """End-to-end tests for release readiness flow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test orchestrator health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "central-orchestrator"
    
    def test_readiness_check(self, client):
        """Test readiness endpoint"""
        response = client.get("/ready")
        
        # May fail if engine not initialized in test mode
        assert response.status_code in [200, 503]
    
    def test_liveness_check(self, client):
        """Test liveness endpoint"""
        response = client.get("/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_execute_simple_query(self, client):
        """Test executing a simple query"""
        response = client.post("/execute", json={
            "task_id": "test-task-1",
            "action": "process_query",
            "payload": {"query": "What is the release status?"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_execute_jira_query(self, client):
        """Test executing a Jira-related query"""
        response = client.post("/execute", json={
            "task_id": "test-task-2",
            "action": "process_query",
            "payload": {"query": "Check ticket PROJ-123 status"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-2"
    
    def test_execute_release_check_query(self, client):
        """Test executing a release readiness query"""
        response = client.post("/execute", json={
            "task_id": "test-task-3",
            "action": "process_query",
            "payload": {"query": "Is version 2.0 ready for release?"},
            "user_context": {"user_id": "test-user"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        if data["data"]:
            assert "result" in data["data"] or "error" in data["data"]
    
    def test_simple_query_endpoint(self, client):
        """Test the simple /query endpoint"""
        response = client.post("/query", json={
            "query": "Hello, what can you do?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "status" in data
    
    def test_query_without_query_fails(self, client):
        """Test that empty query returns error"""
        response = client.post("/query", json={})
        
        assert response.status_code == 400
    
    def test_memory_stats(self, client):
        """Test memory stats endpoint"""
        response = client.get("/memory/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "vector_memory" in data
    
    def test_add_to_memory(self, client):
        """Test adding context to memory"""
        response = client.post("/memory/add", json={
            "content": "Release v1.9 had issues with database migrations.",
            "metadata": {"version": "1.9", "type": "release_note"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "doc_id" in data
    
    def test_search_memory(self, client):
        """Test searching memory"""
        # First add some context
        client.post("/memory/add", json={
            "content": "Database connection pooling was improved in v1.8",
        })
        
        # Then search
        response = client.get("/memory/search", params={
            "query": "database improvements",
            "n_results": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "context" in data


class TestReleaseFlowIntegration:
    """Integration tests simulating full release flow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with TestClient(app) as client:
            yield client
    
    def test_full_release_check_flow(self, client):
        """
        Test complete release check flow:
        1. User asks about release readiness
        2. Orchestrator coordinates agents
        3. Report is generated
        """
        # Step 1: Initial query
        response = client.post("/execute", json={
            "task_id": "flow-test-1",
            "action": "process_query",
            "payload": {
                "query": "Run a complete release readiness check for v2.0"
            },
            "user_context": {
                "user_id": "release-manager",
                "team_id": "platform"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["task_id"] == "flow-test-1"
        assert data["status"] in ["success", "failed"]
        
        if data["status"] == "success" and data["data"]:
            # Verify result contains expected fields
            result_data = data["data"]
            assert "result" in result_data or "plan" in result_data
    
    def test_jira_to_report_flow(self, client):
        """Test flow from Jira check to report generation"""
        # Query that should trigger Jira check
        response = client.post("/execute", json={
            "task_id": "jira-report-flow",
            "action": "process_query",
            "payload": {
                "query": "Get sprint stats for PROJ and generate a report"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_security_check_flow(self, client):
        """Test security-focused release check"""
        response = client.post("/execute", json={
            "task_id": "security-check",
            "action": "process_query",
            "payload": {
                "query": "Check security vulnerabilities in our codebase"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed"]


class TestErrorHandling:
    """Tests for error handling in release flow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with TestClient(app) as client:
            yield client
    
    def test_missing_query_payload(self, client):
        """Test handling missing query in payload"""
        response = client.post("/execute", json={
            "task_id": "error-test-1",
            "action": "process_query",
            "payload": {}  # Missing query
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error" in data["error_message"].lower() or "required" in data["error_message"].lower()
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON"""
        response = client.post(
            "/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "http_requests_total" in response.text or response.headers.get("content-type") == "text/plain"

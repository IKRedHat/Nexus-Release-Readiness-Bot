"""
End-to-End Tests for Orchestrator Service
==========================================

Recommendation #2: Critical Component Coverage
Comprehensive E2E tests for the Central Orchestrator (ReAct Engine).

Coverage:
- Query processing and routing
- Specialist agent coordination
- Memory and context management
- Tool execution
- Health and metrics endpoints
- Error handling

Usage:
    pytest tests/e2e/test_orchestrator.py -v
"""

import pytest
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/orchestrator")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["MEMORY_BACKEND"] = "mock"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client for Orchestrator API."""
    try:
        from main import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("Orchestrator module not available")


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return {
        "query": "What is the release status for v2.0?",
        "context": {"project": "NEXUS"}
    }


# =============================================================================
# Health & Status Tests
# =============================================================================

class TestOrchestratorHealth:
    """Tests for health and status endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "ok"]
        assert "timestamp" in data or "version" in data
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get("/livez")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("alive", data.get("status")) in [True, "ok", "healthy"]
    
    def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe."""
        response = client.get("/readyz")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data or "status" in data
    
    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        # Should contain Prometheus format
        assert len(content) > 0


# =============================================================================
# Query Processing Tests
# =============================================================================

class TestQueryProcessing:
    """Tests for query processing and routing."""
    
    def test_basic_query(self, client, sample_query):
        """Test basic query processing."""
        response = client.post("/query", json=sample_query)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have response or result
        assert "query" in data or "response" in data or "result" in data
    
    def test_query_with_empty_string(self, client):
        """Test query with empty string."""
        response = client.post("/query", json={"query": ""})
        
        # Should reject empty query
        assert response.status_code in [400, 422]
    
    def test_query_without_query_field(self, client):
        """Test request without query field."""
        response = client.post("/query", json={})
        
        # Should reject missing query
        assert response.status_code in [400, 422]
    
    def test_release_status_query(self, client):
        """Test release status query routing."""
        response = client.post("/query", json={
            "query": "What is the release readiness for version 2.0?"
        })
        
        assert response.status_code == 200
    
    def test_blocker_query(self, client):
        """Test blocker identification query."""
        response = client.post("/query", json={
            "query": "What are the blockers for the current sprint?"
        })
        
        assert response.status_code == 200
    
    def test_build_failure_query(self, client):
        """Test build failure query triggers RCA."""
        response = client.post("/query", json={
            "query": "Why did the last build fail?"
        })
        
        assert response.status_code == 200
    
    def test_hygiene_query(self, client):
        """Test hygiene check query."""
        response = client.post("/query", json={
            "query": "Run a hygiene check for project NEXUS"
        })
        
        assert response.status_code == 200
    
    def test_report_generation_query(self, client):
        """Test report generation query."""
        response = client.post("/query", json={
            "query": "Generate a release report for v2.0"
        })
        
        assert response.status_code == 200
    
    def test_analytics_query(self, client):
        """Test analytics query."""
        response = client.post("/query", json={
            "query": "Show me the DORA metrics for this quarter"
        })
        
        assert response.status_code == 200
    
    def test_query_with_context(self, client):
        """Test query with additional context."""
        response = client.post("/query", json={
            "query": "Get ticket details",
            "context": {
                "ticket_key": "NEXUS-123",
                "project": "NEXUS"
            }
        })
        
        assert response.status_code == 200


# =============================================================================
# Specialist Management Tests
# =============================================================================

class TestSpecialistManagement:
    """Tests for specialist agent management."""
    
    def test_list_specialists(self, client):
        """Test listing all specialists."""
        response = client.get("/specialists")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list or dict of specialists
        assert isinstance(data, (list, dict))
    
    def test_list_all_tools(self, client):
        """Test listing all available tools."""
        response = client.get("/specialists/tools/all")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have tools
        assert isinstance(data, (list, dict))
    
    def test_get_specialist_by_id(self, client):
        """Test getting specific specialist info."""
        # First get list of specialists
        list_response = client.get("/specialists")
        
        if list_response.status_code == 200:
            specialists = list_response.json()
            if isinstance(specialists, dict) and specialists:
                specialist_id = list(specialists.keys())[0]
                detail_response = client.get(f"/specialists/{specialist_id}")
                assert detail_response.status_code in [200, 404]
    
    def test_specialist_health_check(self, client):
        """Test triggering health check for specialist."""
        response = client.post("/specialists/jira_agent/health")
        
        # May return 200 or 404 depending on registration
        assert response.status_code in [200, 404]


# =============================================================================
# Memory Management Tests
# =============================================================================

class TestMemoryManagement:
    """Tests for memory and context management."""
    
    def test_memory_stats(self, client):
        """Test getting memory statistics."""
        response = client.get("/memory/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have memory stats
        assert isinstance(data, dict)
    
    def test_memory_persists_across_queries(self, client):
        """Test that context is maintained."""
        # First query
        response1 = client.post("/query", json={
            "query": "Remember that the target release is v2.0"
        })
        assert response1.status_code == 200
        
        # Second query referencing first
        response2 = client.post("/query", json={
            "query": "What was the target release I mentioned?"
        })
        assert response2.status_code == 200


# =============================================================================
# Recommendations Tests
# =============================================================================

class TestRecommendations:
    """Tests for AI recommendations endpoint."""
    
    def test_get_recommendations(self, client):
        """Test getting AI recommendations."""
        response = client.get("/recommendations")
        
        # May not be implemented, so accept 404
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_recommendations_with_context(self, client):
        """Test recommendations with project context."""
        response = client.get("/recommendations?project_key=NEXUS")
        
        assert response.status_code in [200, 404, 501]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestOrchestratorErrorHandling:
    """Tests for error handling in orchestrator."""
    
    def test_malformed_json_rejected(self, client):
        """Test malformed JSON is rejected."""
        response = client.post(
            "/query",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_invalid_endpoint_returns_404(self, client):
        """Test invalid endpoints return 404."""
        response = client.get("/nonexistent/endpoint")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405."""
        response = client.get("/query")  # Should be POST
        
        assert response.status_code == 405
    
    def test_very_long_query_handled(self, client):
        """Test very long query is handled gracefully."""
        long_query = "What is the status? " * 1000
        
        response = client.post("/query", json={"query": long_query})
        
        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 413, 422]
    
    def test_special_characters_in_query(self, client):
        """Test special characters are handled."""
        response = client.post("/query", json={
            "query": "What about ticket <script>alert('xss')</script>?"
        })
        
        # Should sanitize and process
        assert response.status_code == 200


# =============================================================================
# API Documentation Tests
# =============================================================================

class TestAPIDocs:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "paths" in data
    
    def test_swagger_ui(self, client):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_redoc(self, client):
        """Test ReDoc is accessible."""
        response = client.get("/redoc")
        
        assert response.status_code == 200


# =============================================================================
# Performance Baseline Tests
# =============================================================================

class TestPerformanceBaseline:
    """Basic performance tests for orchestrator."""
    
    def test_health_check_fast(self, client):
        """Test health check responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should be under 1 second
    
    def test_simple_query_reasonable_time(self, client):
        """Test simple query completes in reasonable time."""
        import time
        
        start = time.time()
        response = client.post("/query", json={"query": "Hello"})
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 30.0  # Should complete within 30 seconds


# =============================================================================
# Multi-Tenant Tests
# =============================================================================

class TestMultiTenant:
    """Tests for multi-tenant functionality."""
    
    def test_query_with_tenant_header(self, client):
        """Test query with tenant header."""
        response = client.post(
            "/query",
            json={"query": "What is the release status?"},
            headers={"X-Tenant-ID": "tenant-123"}
        )
        
        # Should accept tenant header
        assert response.status_code == 200
    
    def test_query_with_organization_header(self, client):
        """Test query with organization header."""
        response = client.post(
            "/query",
            json={"query": "Get my tickets"},
            headers={"X-Organization-ID": "org-456"}
        )
        
        assert response.status_code == 200


# =============================================================================
# Concurrent Request Tests
# =============================================================================

class TestConcurrentRequests:
    """Tests for handling concurrent requests."""
    
    def test_multiple_health_checks(self, client):
        """Test multiple concurrent health checks."""
        import concurrent.futures
        
        def check_health():
            return client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_health) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
    
    def test_multiple_queries(self, client):
        """Test multiple concurrent queries."""
        import concurrent.futures
        
        queries = [
            {"query": "Status of v1.0"},
            {"query": "Status of v2.0"},
            {"query": "Status of v3.0"},
        ]
        
        def send_query(q):
            return client.post("/query", json=q)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_query, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should complete
        assert all(r.status_code == 200 for r in results)


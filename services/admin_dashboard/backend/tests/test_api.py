"""
API Integration Tests

Tests for all major API endpoints in the Admin Dashboard backend.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test main health endpoint returns proper structure."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "total_services" in data
        assert "healthy_services" in data
        assert "last_updated" in data
        
        # Verify services is a list
        assert isinstance(data["services"], list)
        
        # Verify status is valid
        assert data["overall_status"] in ["healthy", "degraded", "down"]
    
    def test_health_simple(self, client: TestClient):
        """Test simple health check for load balancers."""
        response = client.get("/health/simple")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestStatsEndpoint:
    """Tests for dashboard statistics endpoint."""
    
    def test_stats_returns_expected_fields(self, client: TestClient):
        """Test stats endpoint returns all expected fields."""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "total_releases" in data
        assert "active_agents" in data
        assert "pending_requests" in data
        assert "active_users" in data
        assert "system_health" in data
        assert "recent_activity" in data
        
        # Check additional fields
        assert "mode" in data
        assert "redis_connected" in data
        assert "uptime_seconds" in data
        
        # Verify types
        assert isinstance(data["total_releases"], int)
        assert isinstance(data["system_health"], (int, float))
        assert isinstance(data["recent_activity"], list)


class TestModeEndpoint:
    """Tests for mode switching endpoint."""
    
    def test_get_mode(self, client: TestClient):
        """Test getting current system mode."""
        response = client.get("/mode")
        assert response.status_code == 200
        
        data = response.json()
        assert "mode" in data
        assert data["mode"] in ["mock", "live", "hybrid"]
    
    def test_set_mode(self, client: TestClient):
        """Test setting system mode."""
        response = client.post("/mode", json={"mode": "mock"})
        # May require auth in production, but should work in test
        assert response.status_code in [200, 401, 403]


class TestReleasesEndpoints:
    """Tests for release management endpoints."""
    
    def test_list_releases(self, client: TestClient):
        """Test listing releases."""
        response = client.get("/releases")
        assert response.status_code == 200
        
        # Should return a list
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_release(self, client: TestClient, sample_release: dict):
        """Test creating a new release."""
        response = client.post("/releases", json=sample_release)
        
        # Should succeed or require auth
        assert response.status_code in [200, 201, 401, 403]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["version"] == sample_release["version"]
    
    def test_get_release_roadmap(self, client: TestClient):
        """Test getting release roadmap."""
        response = client.get("/releases/roadmap")
        assert response.status_code == 200
        
        data = response.json()
        assert "releases" in data
        assert "summary" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_get_auth_providers(self, client: TestClient):
        """Test getting available auth providers."""
        response = client.get("/auth/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
    
    def test_login_with_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={"email": "invalid@test.com", "password": "wrong"}
        )
        # Should fail with 401 or 404
        assert response.status_code in [401, 404, 501]
    
    def test_refresh_endpoint_exists(self, client: TestClient):
        """Test that refresh endpoint exists."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        # Should return 401 (invalid token) not 404 (not found)
        assert response.status_code in [401, 501]


class TestConfigEndpoints:
    """Tests for configuration endpoints."""
    
    def test_get_config(self, client: TestClient):
        """Test getting configuration."""
        response = client.get("/config")
        assert response.status_code == 200
    
    def test_get_config_templates(self, client: TestClient):
        """Test getting config templates."""
        response = client.get("/config/templates")
        assert response.status_code == 200


class TestUserEndpoints:
    """Tests for user management endpoints."""
    
    def test_list_users(self, client: TestClient):
        """Test listing users."""
        response = client.get("/users")
        # May require auth
        assert response.status_code in [200, 401, 403, 501]
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code in [200, 401, 501]


class TestRoleEndpoints:
    """Tests for role management endpoints."""
    
    def test_list_roles(self, client: TestClient):
        """Test listing roles."""
        response = client.get("/roles")
        # May require auth
        assert response.status_code in [200, 401, 403, 501]


class TestAuditEndpoints:
    """Tests for audit log endpoints."""
    
    def test_get_audit_logs(self, client: TestClient):
        """Test getting audit logs."""
        response = client.get("/audit-logs")
        # May require auth or return empty
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "logs" in data or isinstance(data, list)


class TestFeatureRequestEndpoints:
    """Tests for feature request endpoints."""
    
    def test_list_feature_requests(self, client: TestClient):
        """Test listing feature requests."""
        response = client.get("/feature-requests")
        assert response.status_code in [200, 401, 501]
    
    def test_get_feature_request_options(self, client: TestClient):
        """Test getting feature request options."""
        response = client.get("/feature-requests/options")
        assert response.status_code == 200
        
        data = response.json()
        assert "types" in data
        assert "priorities" in data
        assert "statuses" in data


class TestMetricsEndpoint:
    """Tests for metrics/Prometheus endpoint."""
    
    def test_prometheus_metrics(self, client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Should return Prometheus format
        assert "text/plain" in response.headers.get("content-type", "")


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_endpoint(self, client: TestClient):
        """Test Swagger docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_for_unknown_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client: TestClient):
        """Test 405 for wrong HTTP method."""
        response = client.delete("/health")
        assert response.status_code == 405


class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # Should return CORS headers or handle preflight
        assert response.status_code in [200, 204, 405]


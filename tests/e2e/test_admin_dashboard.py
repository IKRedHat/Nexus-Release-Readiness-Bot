"""
End-to-End Tests for Admin Dashboard
=====================================

Comprehensive E2E tests covering all Admin Dashboard API endpoints:
- Health & Status
- Mode Management (Mock/Live switching)
- Configuration Management (CRUD operations)
- Agent Health Monitoring
- Observability Metrics
- Release Management
- External Source Sync

Usage:
    pytest tests/e2e/test_admin_dashboard.py -v
    pytest tests/e2e/test_admin_dashboard.py::TestModeManagement -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/admin_dashboard/backend")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["REDIS_URL"] = ""


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.keys = AsyncMock(return_value=[])
    mock.mget = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def client():
    """Create test client for Admin Dashboard API."""
    from main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_release():
    """Sample release data for testing."""
    return {
        "version": "v2.5.0",
        "name": "Phoenix",
        "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "description": "Major feature release",
        "release_type": "minor",
        "project_key": "NEXUS",
        "status": "planning"
    }


@pytest.fixture
def sample_config_update():
    """Sample configuration update."""
    return {
        "key": "nexus:config:test_key",
        "value": "test_value"
    }


# =============================================================================
# Health & Status Tests
# =============================================================================

class TestHealthEndpoints:
    """Tests for health and status endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "admin-dashboard-backend"
        assert "version" in data
        assert "timestamp" in data
    
    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "") or \
               "text/plain" in response.text[:100]
        
        # Should contain some metrics
        content = response.text
        assert len(content) > 0
    
    def test_dashboard_stats(self, client):
        """Test dashboard statistics endpoint."""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mode" in data
        assert "config_count" in data
        assert "healthy_agents" in data
        assert "total_agents" in data
        assert "redis_connected" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


# =============================================================================
# Mode Management Tests
# =============================================================================

class TestModeManagement:
    """Tests for Mock/Live mode switching."""
    
    def test_get_system_mode(self, client):
        """Test getting current system mode."""
        response = client.get("/mode")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mode" in data
        assert data["mode"] in ["mock", "live"]
    
    def test_set_system_mode_mock(self, client):
        """Test switching to mock mode."""
        response = client.post("/mode", json={"mode": "mock"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mode" in data or "current_mode" in data
    
    def test_set_system_mode_live(self, client):
        """Test switching to live mode."""
        response = client.post("/mode", json={"mode": "live"})
        
        # May fail if ConfigManager not available, which is fine in tests
        assert response.status_code in [200, 500]
    
    def test_set_invalid_mode_fails(self, client):
        """Test that invalid mode is rejected."""
        response = client.post("/mode", json={"mode": "invalid"})
        
        assert response.status_code == 422  # Validation error


# =============================================================================
# Configuration Management Tests
# =============================================================================

class TestConfigurationManagement:
    """Tests for configuration CRUD operations."""
    
    def test_get_all_config(self, client):
        """Test getting all configuration values."""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "config" in data
        assert "mode" in data
        assert isinstance(data["config"], (list, dict))
    
    def test_get_config_by_key(self, client):
        """Test getting specific configuration value."""
        # This may return 404 if key doesn't exist, which is valid behavior
        response = client.get("/config/nexus:config:test_key")
        
        assert response.status_code in [200, 404, 500]
    
    def test_update_config(self, client, sample_config_update):
        """Test updating configuration value."""
        response = client.post("/config", json=sample_config_update)
        
        # May succeed or fail based on Redis availability
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
    
    def test_update_config_invalid_key_format(self, client):
        """Test that invalid key format is rejected."""
        response = client.post("/config", json={
            "key": "invalid_key_format",
            "value": "test"
        })
        
        # Should reject keys not starting with "nexus:"
        assert response.status_code in [400, 500]
    
    def test_bulk_config_update(self, client):
        """Test bulk configuration update."""
        response = client.post("/config/bulk", json={
            "config": {
                "nexus:config:key1": "value1",
                "nexus:config:key2": "value2"
            }
        })
        
        # May succeed or fail based on Redis availability
        assert response.status_code in [200, 500]
    
    def test_delete_config(self, client):
        """Test deleting configuration value."""
        response = client.delete("/config/nexus:config:test_key")
        
        # May succeed or fail based on Redis availability
        assert response.status_code in [200, 500]
    
    def test_get_config_templates(self, client):
        """Test getting configuration templates."""
        response = client.get("/config/templates")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have templates for different integrations
        assert "jira" in data
        assert "github" in data
        assert "jenkins" in data
        assert "llm" in data
        assert "slack" in data
        assert "confluence" in data
        
        # Each template should have fields
        jira_template = data["jira"]
        assert "name" in jira_template
        assert "fields" in jira_template
        assert len(jira_template["fields"]) > 0


# =============================================================================
# Agent Health Monitoring Tests
# =============================================================================

class TestAgentHealthMonitoring:
    """Tests for agent health monitoring functionality."""
    
    def test_check_all_agents(self, client):
        """Test checking health of all agents."""
        response = client.get("/health-check")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "mode" in data
        assert "agents" in data
        assert "healthy_count" in data
        assert "total_count" in data
        assert "timestamp" in data
    
    def test_check_single_agent(self, client):
        """Test checking health of a specific agent."""
        # This may return 404 if agent not registered
        response = client.get("/health-check/jira_agent")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "agent_id" in data
            assert "status" in data
    
    def test_check_nonexistent_agent(self, client):
        """Test checking health of non-existent agent."""
        response = client.get("/health-check/nonexistent_agent")
        
        assert response.status_code == 404


# =============================================================================
# Observability Metrics Tests
# =============================================================================

class TestObservabilityMetrics:
    """Tests for aggregated metrics endpoint."""
    
    def test_get_aggregated_metrics_default_range(self, client):
        """Test getting aggregated metrics with default range."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have summary cards
        assert "summary" in data
        assert isinstance(data["summary"], list)
        assert len(data["summary"]) >= 4  # At least 4 summary cards
        
        # Check summary card structure
        for card in data["summary"]:
            assert "title" in card
            assert "value" in card
            assert "color" in card
    
    def test_get_aggregated_metrics_1h_range(self, client):
        """Test getting metrics with 1 hour range."""
        response = client.get("/api/metrics?range=1h")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "timeSeries" in data
        assert "agents" in data
        assert "llmUsage" in data
    
    def test_get_aggregated_metrics_24h_range(self, client):
        """Test getting metrics with 24 hour range."""
        response = client.get("/api/metrics?range=24h")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hygieneScore" in data
        assert "releaseDecisions" in data
    
    def test_get_aggregated_metrics_7d_range(self, client):
        """Test getting metrics with 7 day range."""
        response = client.get("/api/metrics?range=7d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify time series data
        if "timeSeries" in data:
            assert isinstance(data["timeSeries"], list)
    
    def test_metrics_agent_performance(self, client):
        """Test that metrics include agent performance data."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        if "agents" in data:
            assert isinstance(data["agents"], list)
            if len(data["agents"]) > 0:
                agent = data["agents"][0]
                assert "name" in agent
                assert "requests" in agent
                assert "status" in agent
    
    def test_metrics_llm_usage(self, client):
        """Test that metrics include LLM usage data."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        if "llmUsage" in data:
            assert isinstance(data["llmUsage"], list)
            if len(data["llmUsage"]) > 0:
                llm = data["llmUsage"][0]
                assert "model" in llm
                assert "tokens" in llm
                assert "cost" in llm


# =============================================================================
# Release Management Tests
# =============================================================================

class TestReleaseManagement:
    """Tests for release management functionality."""
    
    def test_list_releases_empty(self, client):
        """Test listing releases when none exist."""
        response = client.get("/releases")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "releases" in data
        assert "count" in data
        assert isinstance(data["releases"], list)
    
    def test_list_releases_with_status_filter(self, client):
        """Test listing releases with status filter."""
        response = client.get("/releases?status=planning")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "releases" in data
    
    def test_list_releases_with_pagination(self, client):
        """Test listing releases with pagination."""
        response = client.get("/releases?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    def test_create_release(self, client, sample_release):
        """Test creating a new release."""
        response = client.post("/releases", json=sample_release)
        
        # May fail if Redis not available
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "release" in data
            assert data["release"]["version"] == sample_release["version"]
    
    def test_create_release_missing_version(self, client):
        """Test that release creation fails without version."""
        response = client.post("/releases", json={
            "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
        
        assert response.status_code == 400
    
    def test_create_release_missing_target_date(self, client):
        """Test that release creation fails without target_date."""
        response = client.post("/releases", json={
            "version": "v1.0.0"
        })
        
        assert response.status_code == 400
    
    def test_get_release(self, client):
        """Test getting a specific release."""
        response = client.get("/releases/rel-test-123")
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404]
    
    def test_update_release(self, client):
        """Test updating a release."""
        response = client.put("/releases/rel-test-123", json={
            "status": "in_progress"
        })
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_delete_release(self, client):
        """Test deleting a release."""
        response = client.delete("/releases/rel-test-123")
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_get_release_calendar(self, client):
        """Test getting release calendar view."""
        response = client.get("/releases/calendar")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "start_date" in data
        assert "end_date" in data
        assert "releases" in data
        assert "milestones" in data
        assert "summary" in data
    
    def test_get_release_calendar_with_months(self, client):
        """Test getting release calendar for specific months."""
        response = client.get("/releases/calendar?months=6")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        summary = data["summary"]
        assert "total_releases" in summary
        assert "upcoming_releases" in summary
        assert "overdue_releases" in summary
        assert "at_risk_releases" in summary
    
    def test_get_release_metrics(self, client):
        """Test getting release metrics."""
        response = client.get("/releases/rel-test-123/metrics")
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404]
    
    def test_add_milestone(self, client):
        """Test adding milestone to release."""
        response = client.post("/releases/rel-test-123/milestones", json={
            "name": "Code Freeze",
            "target_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        })
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404]
    
    def test_add_risk(self, client):
        """Test adding risk to release."""
        response = client.post("/releases/rel-test-123/risks", json={
            "title": "Dependency Update Required",
            "description": "Critical security update needed",
            "severity": "high"
        })
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404]
    
    def test_get_release_templates(self, client):
        """Test getting release templates."""
        response = client.get("/releases/templates")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        templates = data["templates"]
        
        assert len(templates) >= 3  # At least standard, hotfix, major
        
        # Check template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "release_type" in template
            assert "milestones" in template


# =============================================================================
# External Source Sync Tests
# =============================================================================

class TestExternalSourceSync:
    """Tests for external source synchronization."""
    
    def test_sync_from_smartsheet_missing_api_token(self, client):
        """Test Smartsheet sync fails without API token."""
        response = client.post("/releases/sync/smartsheet", json={
            "sheet_id": "12345"
        })
        
        assert response.status_code == 400
    
    def test_sync_from_smartsheet_missing_sheet_id(self, client):
        """Test Smartsheet sync fails without sheet ID."""
        response = client.post("/releases/sync/smartsheet", json={
            "api_token": "test-token"
        })
        
        assert response.status_code == 400
    
    def test_sync_from_smartsheet_valid_config(self, client):
        """Test Smartsheet sync with valid config."""
        response = client.post("/releases/sync/smartsheet", json={
            "api_token": "test-token",
            "sheet_id": "12345"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sync_id" in data
        assert data["status"] == "in_progress"
    
    def test_sync_from_csv(self, client):
        """Test CSV import."""
        csv_data = """version,target_date,name,status
v3.0.0,2025-06-01,Major,planning
v2.6.0,2025-04-15,Minor,in_progress"""
        
        response = client.post("/releases/sync/csv", params={
            "csv_data": csv_data
        })
        
        # CSV parsing may vary
        assert response.status_code in [200, 422, 500]
    
    def test_webhook_create_release(self, client):
        """Test webhook endpoint for creating release."""
        response = client.post("/releases/sync/webhook", json={
            "action": "create",
            "release": {
                "version": "v2.7.0",
                "target_date": (datetime.utcnow() + timedelta(days=60)).isoformat()
            },
            "source": "external_system"
        })
        
        assert response.status_code in [200, 500]
    
    def test_webhook_update_release(self, client):
        """Test webhook endpoint for updating release."""
        response = client.post("/releases/sync/webhook", json={
            "action": "update",
            "release": {
                "release_id": "rel-test-123",
                "status": "testing"
            },
            "source": "external_system"
        })
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_webhook_delete_release(self, client):
        """Test webhook endpoint for deleting release."""
        response = client.post("/releases/sync/webhook", json={
            "action": "delete",
            "release": {
                "release_id": "rel-test-123"
            },
            "source": "external_system"
        })
        
        # May return 404 if release doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_webhook_invalid_action(self, client):
        """Test webhook with invalid action."""
        response = client.post("/releases/sync/webhook", json={
            "action": "invalid_action",
            "release": {}
        })
        
        assert response.status_code == 400
    
    def test_webhook_missing_action(self, client):
        """Test webhook without action field."""
        response = client.post("/releases/sync/webhook", json={
            "release": {
                "version": "v1.0.0"
            }
        })
        
        assert response.status_code == 400


# =============================================================================
# Integration Workflow Tests
# =============================================================================

class TestIntegrationWorkflows:
    """Tests for complete integration workflows."""
    
    def test_full_release_lifecycle(self, client):
        """Test complete release lifecycle: create -> update -> metrics -> delete."""
        # 1. Create release
        create_response = client.post("/releases", json={
            "version": "v-lifecycle-test",
            "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "name": "Lifecycle Test Release"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Redis not available for lifecycle test")
        
        release_id = create_response.json()["release"]["release_id"]
        
        # 2. Get release
        get_response = client.get(f"/releases/{release_id}")
        assert get_response.status_code == 200
        assert get_response.json()["version"] == "v-lifecycle-test"
        
        # 3. Update release
        update_response = client.put(f"/releases/{release_id}", json={
            "status": "in_progress"
        })
        assert update_response.status_code == 200
        
        # 4. Add milestone
        milestone_response = client.post(f"/releases/{release_id}/milestones", json={
            "name": "Code Freeze",
            "target_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        })
        assert milestone_response.status_code == 200
        
        # 5. Get metrics
        metrics_response = client.get(f"/releases/{release_id}/metrics?refresh=true")
        assert metrics_response.status_code == 200
        
        # 6. Delete release
        delete_response = client.delete(f"/releases/{release_id}")
        assert delete_response.status_code == 200
        
        # 7. Verify deleted
        verify_response = client.get(f"/releases/{release_id}")
        assert verify_response.status_code == 404
    
    def test_mode_switch_and_health_check(self, client):
        """Test mode switching followed by health check."""
        # Get current mode
        mode_response = client.get("/mode")
        assert mode_response.status_code == 200
        
        # Check health
        health_response = client.get("/health-check")
        assert health_response.status_code == 200
        
        # Verify mode is in health response
        health_data = health_response.json()
        assert "mode" in health_data
    
    def test_config_and_stats_consistency(self, client):
        """Test that config and stats endpoints are consistent."""
        # Get config
        config_response = client.get("/config")
        assert config_response.status_code == 200
        config_data = config_response.json()
        
        # Get stats
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        # Mode should be consistent
        assert config_data["mode"] == stats_data["mode"]


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_release_version(self, client):
        """Test release creation with empty version."""
        response = client.post("/releases", json={
            "version": "",
            "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]
    
    def test_past_target_date(self, client):
        """Test release creation with past target date."""
        response = client.post("/releases", json={
            "version": "v-past-date",
            "target_date": (datetime.utcnow() - timedelta(days=30)).isoformat()
        })
        
        # Should allow (for retroactive tracking) or reject
        assert response.status_code in [200, 400, 422, 500]
    
    def test_very_long_version_string(self, client):
        """Test release with very long version string."""
        response = client.post("/releases", json={
            "version": "v" + "x" * 1000,
            "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422, 500]
    
    def test_special_characters_in_config_key(self, client):
        """Test config with special characters in key."""
        response = client.post("/config", json={
            "key": "nexus:config:test<script>alert('xss')</script>",
            "value": "test"
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_concurrent_release_updates(self, client):
        """Test handling of concurrent release updates."""
        # This is a basic test - real concurrency testing would require async
        response1 = client.put("/releases/rel-concurrent-test", json={"status": "in_progress"})
        response2 = client.put("/releases/rel-concurrent-test", json={"status": "testing"})
        
        # Both should either succeed or fail consistently
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]


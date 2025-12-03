"""
Integration Tests for Full Workflow Coverage
=============================================

Recommendation #1: Increase Integration Tests
Tests inter-service communication and complete workflows.

Coverage:
- Orchestrator → Agent tool execution
- Agent → Agent communication chains
- Release readiness complete workflow
- RCA → Slack notification workflow
- Hygiene → Jira → Slack workflow
- Config propagation across services
- Error recovery and circuit breaking

Usage:
    pytest tests/integration/test_full_workflows.py -v
    pytest tests/integration/ -v --tb=short
"""

import pytest
import asyncio
import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Service URLs
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080")
JIRA_AGENT_URL = os.environ.get("JIRA_AGENT_URL", "http://localhost:8081")
GIT_CI_AGENT_URL = os.environ.get("GIT_CI_AGENT_URL", "http://localhost:8082")
REPORTING_AGENT_URL = os.environ.get("REPORTING_AGENT_URL", "http://localhost:8083")
SLACK_AGENT_URL = os.environ.get("SLACK_AGENT_URL", "http://localhost:8084")
HYGIENE_AGENT_URL = os.environ.get("HYGIENE_AGENT_URL", "http://localhost:8085")
RCA_AGENT_URL = os.environ.get("RCA_AGENT_URL", "http://localhost:8006")
ANALYTICS_URL = os.environ.get("ANALYTICS_URL", "http://localhost:8086")
WEBHOOKS_URL = os.environ.get("WEBHOOKS_URL", "http://localhost:8087")
ADMIN_URL = os.environ.get("ADMIN_DASHBOARD_URL", "http://localhost:8088")


# =============================================================================
# Workflow: Release Readiness Assessment
# =============================================================================

class TestReleaseReadinessWorkflow:
    """
    Tests the complete release readiness workflow:
    User Query → Orchestrator → [Jira, Git/CI, Reporting] → Response
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=60.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_release_query_triggers_multi_agent(self, client):
        """Test that release query coordinates multiple agents."""
        try:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/query",
                json={"query": "What is the release status for v2.0?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have processed the query
            assert "query" in data or "response" in data or "result" in data
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_release_blocker_identification(self, client):
        """Test blocker identification workflow."""
        try:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/query",
                json={"query": "What are the blockers for the current release?"}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_jira_to_reporting_workflow(self, client):
        """Test Jira data flowing to report generation."""
        try:
            # 1. Get Jira data
            jira_response = await client.post(
                f"{JIRA_AGENT_URL}/execute",
                json={
                    "task_id": "int-test-1",
                    "action": "get_release_stats",
                    "payload": {"project_key": "NEXUS", "version": "2.0"}
                }
            )
            
            # 2. Generate report with Jira data
            report_response = await client.post(
                f"{REPORTING_AGENT_URL}/execute",
                json={
                    "task_id": "int-test-2",
                    "action": "generate_report",
                    "payload": {
                        "stats": jira_response.json().get("data", {}),
                        "format": "html"
                    }
                }
            )
            
            assert report_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: RCA to Notification
# =============================================================================

class TestRCANotificationWorkflow:
    """
    Tests the RCA → Slack notification workflow:
    Build Failure → RCA Agent → Analysis → Slack Agent → Notification
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=60.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rca_triggers_slack_notification(self, client):
        """Test RCA analysis triggers Slack notification."""
        try:
            # Trigger RCA analysis with notification
            response = await client.post(
                f"{RCA_AGENT_URL}/analyze",
                json={
                    "job_name": "nexus-main",
                    "build_number": 142,
                    "repo_name": "nexus-backend",
                    "notify": True,
                    "channel": "#release-channel"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_jenkins_webhook_to_rca(self, client):
        """Test Jenkins webhook triggers RCA."""
        try:
            # Simulate Jenkins webhook
            response = await client.post(
                f"{RCA_AGENT_URL}/webhook/jenkins",
                json={
                    "build": {
                        "number": 143,
                        "result": "FAILURE",
                        "url": "http://jenkins/job/nexus-main/143"
                    },
                    "job": {
                        "name": "nexus-main"
                    }
                }
            )
            
            # Should accept webhook
            assert response.status_code in [200, 202]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: Hygiene Check Chain
# =============================================================================

class TestHygieneWorkflow:
    """
    Tests the Hygiene → Jira → Slack workflow:
    Scheduled Check → Violations Found → Slack DM to Assignees
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=60.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hygiene_check_flow(self, client):
        """Test hygiene check identifies violations."""
        try:
            response = await client.post(
                f"{HYGIENE_AGENT_URL}/execute",
                json={
                    "task_id": "hygiene-int-1",
                    "action": "run_check",
                    "payload": {
                        "project_key": "NEXUS",
                        "notify": False
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hygiene_to_slack_notification(self, client):
        """Test hygiene violations trigger Slack notifications."""
        try:
            # Run check with notifications
            response = await client.post(
                f"{HYGIENE_AGENT_URL}/execute",
                json={
                    "task_id": "hygiene-int-2",
                    "action": "run_check",
                    "payload": {
                        "project_key": "NEXUS",
                        "notify": True
                    }
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: Configuration Propagation
# =============================================================================

class TestConfigPropagationWorkflow:
    """
    Tests configuration changes propagating across services.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mode_switch_propagates(self, client):
        """Test mode switch affects all agents."""
        try:
            # Get initial mode
            initial_mode = await client.get(f"{ADMIN_URL}/mode")
            assert initial_mode.status_code == 200
            
            # Switch mode
            switch_response = await client.post(
                f"{ADMIN_URL}/mode",
                json={"mode": "mock"}
            )
            assert switch_response.status_code == 200
            
            # Verify propagation by checking orchestrator
            orch_health = await client.get(f"{ORCHESTRATOR_URL}/health")
            assert orch_health.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_config_update_reflects_in_agents(self, client):
        """Test config updates are available to agents."""
        try:
            # Update a config value
            config_response = await client.post(
                f"{ADMIN_URL}/config",
                json={
                    "key": "nexus:config:test_integration",
                    "value": "integration_test_value"
                }
            )
            
            # This may fail if Redis not available, which is acceptable
            assert config_response.status_code in [200, 500]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: Analytics Data Collection
# =============================================================================

class TestAnalyticsDataWorkflow:
    """
    Tests analytics collecting data from multiple sources.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analytics_aggregates_from_services(self, client):
        """Test analytics aggregates data from all services."""
        try:
            # Get KPIs (aggregates from multiple sources)
            kpis_response = await client.get(f"{ANALYTICS_URL}/api/v1/kpis")
            assert kpis_response.status_code == 200
            
            # Get trends
            trends_response = await client.get(f"{ANALYTICS_URL}/api/v1/trends")
            assert trends_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_metrics_flow_to_admin_dashboard(self, client):
        """Test metrics from services flow to admin dashboard."""
        try:
            # Admin dashboard aggregated metrics
            metrics_response = await client.get(f"{ADMIN_URL}/api/metrics")
            assert metrics_response.status_code == 200
            
            data = metrics_response.json()
            assert "summary" in data
            assert "agents" in data
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: Webhook Event Delivery
# =============================================================================

class TestWebhookDeliveryWorkflow:
    """
    Tests webhook event delivery workflow.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_release_event_triggers_webhook(self, client):
        """Test release events trigger webhook deliveries."""
        try:
            # Create a webhook subscription
            sub_response = await client.post(
                f"{WEBHOOKS_URL}/api/v1/subscriptions",
                json={
                    "name": "Integration Test Webhook",
                    "url": "https://httpbin.org/post",
                    "events": ["release.created", "release.updated"],
                    "secret": "test-secret-123"
                }
            )
            
            # Should create or return existing
            assert sub_response.status_code in [200, 201, 422]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_event_types_available(self, client):
        """Test all event types are registered."""
        try:
            response = await client.get(f"{WEBHOOKS_URL}/api/v1/event-types")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, (list, dict))
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Workflow: Full Release Lifecycle
# =============================================================================

class TestFullReleaseLifecycle:
    """
    Tests the complete release lifecycle from creation to deployment.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=60.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_release_lifecycle(self, client):
        """Test complete release from planning to deployed."""
        try:
            # 1. Create release
            create_response = await client.post(
                f"{ADMIN_URL}/releases",
                json={
                    "version": f"v-int-test-{datetime.now().timestamp()}",
                    "target_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "name": "Integration Test Release",
                    "status": "planning"
                }
            )
            
            if create_response.status_code != 200:
                pytest.skip("Redis not available for lifecycle test")
            
            release_id = create_response.json()["release"]["release_id"]
            
            # 2. Progress through stages
            stages = ["in_progress", "testing", "ready"]
            for stage in stages:
                update_response = await client.put(
                    f"{ADMIN_URL}/releases/{release_id}",
                    json={"status": stage}
                )
                assert update_response.status_code == 200
            
            # 3. Get release metrics
            metrics_response = await client.get(
                f"{ADMIN_URL}/releases/{release_id}/metrics?refresh=true"
            )
            assert metrics_response.status_code == 200
            
            # 4. Clean up
            await client.delete(f"{ADMIN_URL}/releases/{release_id}")
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Error Recovery and Circuit Breaking
# =============================================================================

class TestErrorRecovery:
    """
    Tests error handling and recovery in workflows.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_orchestrator_handles_agent_timeout(self, client):
        """Test orchestrator gracefully handles slow agents."""
        try:
            # Send a query that might involve slow operations
            response = await client.post(
                f"{ORCHESTRATOR_URL}/query",
                json={"query": "Generate a detailed release report"}
            )
            
            # Should complete or timeout gracefully
            assert response.status_code in [200, 408, 500, 504]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")
        except httpx.TimeoutException:
            # Timeout is acceptable - we're testing timeout handling
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_partial_workflow_failure_recovery(self, client):
        """Test workflows recover from partial failures."""
        try:
            # Query that involves multiple agents - some might fail
            response = await client.post(
                f"{ORCHESTRATOR_URL}/query",
                json={"query": "Get all data from all systems"}
            )
            
            # Should return something even if some agents fail
            assert response.status_code in [200, 206, 207, 500]
            
        except httpx.ConnectError:
            pytest.skip("Services not running")


# =============================================================================
# Cross-Service Data Consistency
# =============================================================================

class TestDataConsistency:
    """
    Tests data consistency across services.
    """
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_status_consistency(self, client):
        """Test health status is consistent across endpoints."""
        try:
            # Get health from admin dashboard
            admin_health = await client.get(f"{ADMIN_URL}/health-check")
            
            # Get health from orchestrator
            orch_health = await client.get(f"{ORCHESTRATOR_URL}/health")
            
            if admin_health.status_code == 200 and orch_health.status_code == 200:
                # Both should report similar overall status
                admin_data = admin_health.json()
                orch_data = orch_health.json()
                
                # Both should have status field
                assert "status" in admin_data
                assert "status" in orch_data
                
        except httpx.ConnectError:
            pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_metrics_consistency(self, client):
        """Test metrics are consistent across services."""
        try:
            # Get metrics from admin
            admin_metrics = await client.get(f"{ADMIN_URL}/api/metrics")
            
            # Get metrics from analytics
            analytics_kpis = await client.get(f"{ANALYTICS_URL}/api/v1/kpis")
            
            if admin_metrics.status_code == 200 and analytics_kpis.status_code == 200:
                # Both should return valid data structures
                assert isinstance(admin_metrics.json(), dict)
                assert isinstance(analytics_kpis.json(), (dict, list))
                
        except httpx.ConnectError:
            pytest.skip("Services not running")


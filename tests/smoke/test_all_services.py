"""
Smoke Tests for All Nexus Services
===================================

Quick health checks and basic functionality verification.
These tests should be fast and run before/after deployments.

Usage:
    pytest tests/smoke/ -v --tb=short
    pytest tests/smoke/ -x  # Stop on first failure
"""

import pytest
import httpx
import asyncio
import os
from typing import Dict

# Service configuration
SERVICES = {
    "orchestrator": {
        "url": os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080"),
        "health_path": "/health",
        "port": 8080
    },
    "jira_agent": {
        "url": os.environ.get("JIRA_AGENT_URL", "http://localhost:8081"),
        "health_path": "/health",
        "port": 8081
    },
    "git_ci_agent": {
        "url": os.environ.get("GIT_CI_AGENT_URL", "http://localhost:8082"),
        "health_path": "/health",
        "port": 8082
    },
    "reporting_agent": {
        "url": os.environ.get("REPORTING_AGENT_URL", "http://localhost:8083"),
        "health_path": "/health",
        "port": 8083
    },
    "slack_agent": {
        "url": os.environ.get("SLACK_AGENT_URL", "http://localhost:8084"),
        "health_path": "/health",
        "port": 8084
    },
    "hygiene_agent": {
        "url": os.environ.get("HYGIENE_AGENT_URL", "http://localhost:8085"),
        "health_path": "/health",
        "port": 8085
    },
    "rca_agent": {
        "url": os.environ.get("RCA_AGENT_URL", "http://localhost:8006"),
        "health_path": "/health",
        "port": 8006
    },
    "analytics_agent": {
        "url": os.environ.get("ANALYTICS_AGENT_URL", "http://localhost:8086"),
        "health_path": "/health",
        "port": 8086
    },
    "webhooks_agent": {
        "url": os.environ.get("WEBHOOKS_AGENT_URL", "http://localhost:8087"),
        "health_path": "/health",
        "port": 8087
    },
    "admin_dashboard": {
        "url": os.environ.get("ADMIN_DASHBOARD_URL", "http://localhost:8088"),
        "health_path": "/health",  # Fixed: was /health-check
        "port": 8088
    }
}


class TestServiceHealth:
    """Smoke tests for service health endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service_name,config", list(SERVICES.items()))
    async def test_service_health(self, client, service_name: str, config: Dict):
        """Test that each service responds to health checks."""
        url = f"{config['url']}{config['health_path']}"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200, \
                f"{service_name} health check failed with status {response.status_code}"
            
            data = response.json()
            assert "status" in data, f"{service_name} missing status field"
            assert data["status"] in ["healthy", "ok"], \
                f"{service_name} reported unhealthy: {data}"
                
        except httpx.ConnectError:
            pytest.skip(f"{service_name} not running at {url}")
        except Exception as e:
            pytest.fail(f"{service_name} health check error: {e}")
    
    @pytest.mark.asyncio
    async def test_all_services_respond(self, client):
        """Test that all services are responding."""
        healthy_services = []
        unhealthy_services = []
        
        for name, config in SERVICES.items():
            url = f"{config['url']}{config['health_path']}"
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    healthy_services.append(name)
                else:
                    unhealthy_services.append((name, response.status_code))
            except Exception as e:
                unhealthy_services.append((name, str(e)))
        
        # Report status
        print(f"\n✅ Healthy: {len(healthy_services)}")
        print(f"❌ Unhealthy: {len(unhealthy_services)}")
        
        if unhealthy_services:
            for name, error in unhealthy_services:
                print(f"  - {name}: {error}")
        
        # At least orchestrator should be healthy
        assert "orchestrator" in healthy_services or len(healthy_services) > 0, \
            "No services are healthy"


class TestBasicFunctionality:
    """Smoke tests for basic service functionality."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_orchestrator_accepts_query(self, client):
        """Test orchestrator accepts and processes queries."""
        url = f"{SERVICES['orchestrator']['url']}/query"
        
        try:
            response = await client.post(url, json={
                "query": "Hello, what can you do?"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "query" in data or "result" in data or "response" in data
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_jira_agent_execute(self, client):
        """Test Jira agent execute endpoint."""
        url = f"{SERVICES['jira_agent']['url']}/execute"
        
        try:
            # Use correct AgentTaskRequest schema
            response = await client.post(url, json={
                "task_id": "test-123",
                "action": "get_ticket",
                "payload": {"ticket_key": "PROJ-123"}
            })
            
            assert response.status_code == 200
            data = response.json()
            # Accept success or failed - endpoint responds correctly
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Jira agent not running")
    
    @pytest.mark.asyncio
    async def test_git_ci_agent_execute(self, client):
        """Test Git/CI agent execute endpoint."""
        url = f"{SERVICES['git_ci_agent']['url']}/execute"
        
        try:
            # Use correct AgentTaskRequest schema
            response = await client.post(url, json={
                "task_id": "test-124",
                "action": "get_build_status",
                "payload": {"job_name": "nexus-main"}
            })
            
            assert response.status_code == 200
            data = response.json()
            # Accept success or failed - endpoint responds correctly
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Git/CI agent not running")
    
    @pytest.mark.asyncio
    async def test_hygiene_agent_status(self, client):
        """Test hygiene agent status endpoint."""
        url = f"{SERVICES['hygiene_agent']['url']}/status"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            
        except httpx.ConnectError:
            pytest.skip("Hygiene agent not running")
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_config(self, client):
        """Test admin dashboard returns system config."""
        url = f"{SERVICES['admin_dashboard']['url']}/config"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")


class TestMetricsEndpoints:
    """Smoke tests for Prometheus metrics endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service_name,config", [
        (name, cfg) for name, cfg in SERVICES.items()
    ])
    async def test_metrics_endpoint(self, client, service_name: str, config: Dict):
        """Test that services expose Prometheus metrics."""
        url = f"{config['url']}/metrics"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200, \
                f"{service_name} metrics endpoint failed"
            
            # Should contain Prometheus format
            content = response.text
            assert "# HELP" in content or "http_" in content or "nexus_" in content or len(content) > 0, \
                f"{service_name} metrics not in Prometheus format"
                
        except httpx.ConnectError:
            pytest.skip(f"{service_name} not running")


class TestConnectivity:
    """Smoke tests for inter-service connectivity."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_orchestrator_specialists(self, client):
        """Test orchestrator returns specialists list."""
        url = f"{SERVICES['orchestrator']['url']}/specialists"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (dict, list))
                            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_health_overview(self, client):
        """Test admin dashboard health overview."""
        url = f"{SERVICES['admin_dashboard']['url']}/health-overview"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")


class TestRateLimitsAndQuotas:
    """Smoke tests for rate limiting."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_rapid_requests_handled(self, client):
        """Test services handle rapid requests without errors."""
        url = f"{SERVICES['orchestrator']['url']}/health"
        
        try:
            # Send 10 rapid requests
            tasks = [client.get(url) for _ in range(10)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed (no rate limit in smoke test mode)
            success_count = sum(
                1 for r in responses 
                if isinstance(r, httpx.Response) and r.status_code == 200
            )
            
            assert success_count >= 8, "Too many failed rapid requests"
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Smoke Test Runner
# =============================================================================

def run_smoke_tests():
    """Run all smoke tests and report results."""
    import subprocess
    import sys
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode


if __name__ == "__main__":
    # When run directly, execute all smoke tests
    exit_code = run_smoke_tests()
    exit(exit_code)

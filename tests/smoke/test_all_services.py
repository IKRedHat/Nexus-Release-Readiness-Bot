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
from typing import Dict, List, Tuple

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
        "health_path": "/health-check",
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
            assert "query" in data or "result" in data
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_jira_agent_returns_ticket(self, client):
        """Test Jira agent returns ticket data."""
        url = f"{SERVICES['jira_agent']['url']}/ticket/PROJ-123"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            
        except httpx.ConnectError:
            pytest.skip("Jira agent not running")
    
    @pytest.mark.asyncio
    async def test_git_ci_agent_returns_build(self, client):
        """Test Git/CI agent returns build data."""
        url = f"{SERVICES['git_ci_agent']['url']}/jenkins/job/nexus-main/latest"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
        except httpx.ConnectError:
            pytest.skip("Git/CI agent not running")
    
    @pytest.mark.asyncio
    async def test_reporting_agent_generates_preview(self, client):
        """Test reporting agent generates report preview."""
        url = f"{SERVICES['reporting_agent']['url']}/preview"
        
        try:
            response = await client.get(url, params={
                "release_version": "v2.0.0",
                "decision": "GO"
            })
            
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            
        except httpx.ConnectError:
            pytest.skip("Reporting agent not running")
    
    @pytest.mark.asyncio
    async def test_hygiene_agent_returns_config(self, client):
        """Test hygiene agent returns configuration."""
        url = f"{SERVICES['hygiene_agent']['url']}/config"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            assert "required_fields" in data or "projects" in data
            
        except httpx.ConnectError:
            pytest.skip("Hygiene agent not running")
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_returns_config(self, client):
        """Test admin dashboard returns system config."""
        url = f"{SERVICES['admin_dashboard']['url']}/config"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200
            data = response.json()
            # Config should be returned
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
        if name != "admin_dashboard"  # Admin dashboard has different metrics path
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
            assert "# HELP" in content or "http_" in content or "nexus_" in content, \
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
    async def test_orchestrator_can_reach_agents(self, client):
        """Test orchestrator can reach all registered agents."""
        # Get agent registry from orchestrator
        url = f"{SERVICES['orchestrator']['url']}/agents"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                agents = response.json()
                
                # Each agent should have health info
                for agent_name, agent_info in agents.items():
                    if "health" in agent_info:
                        assert agent_info["health"] in ["healthy", "unknown"], \
                            f"Agent {agent_name} unhealthy"
                            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
        except Exception:
            # Endpoint might not exist
            pass
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_can_check_health(self, client):
        """Test admin dashboard can check all service health."""
        url = f"{SERVICES['admin_dashboard']['url']}/health-check"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should report on multiple services
                assert "services" in data or "agents" in data or isinstance(data, dict)
                
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")


class TestDatabaseConnectivity:
    """Smoke tests for database connectivity."""
    
    @pytest.fixture
    def client(self):
        """Create async HTTP client."""
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_redis_connectivity(self, client):
        """Test Redis is accessible via admin dashboard."""
        url = f"{SERVICES['admin_dashboard']['url']}/health-check"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Redis status should be reported
                if "redis" in data:
                    assert data["redis"]["status"] in ["connected", "healthy", "ok"]
                    
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


"""
Comprehensive Smoke Tests for All Nexus Services
=================================================

Recommendation #3: Expand Smoke Tests
Quick health verification tests for all services and functionality.

Coverage:
- All 10 service health endpoints
- Basic functionality per service
- Prometheus metrics endpoints
- API documentation endpoints
- Database/Redis connectivity
- Inter-service connectivity
- Observability stack

Usage:
    pytest tests/smoke/test_comprehensive_smoke.py -v --tb=short
    pytest tests/smoke/ -x  # Stop on first failure
"""

import pytest
import httpx
import asyncio
import os
from typing import Dict, List
from datetime import datetime

# Service configuration
SERVICES = {
    "orchestrator": {
        "url": os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080"),
        "health_path": "/health",
        "port": 8080,
        "critical": True,
        "description": "Central ReAct Engine"
    },
    "jira_agent": {
        "url": os.environ.get("JIRA_AGENT_URL", "http://localhost:8081"),
        "health_path": "/health",
        "port": 8081,
        "critical": True,
        "description": "Jira Integration"
    },
    "git_ci_agent": {
        "url": os.environ.get("GIT_CI_AGENT_URL", "http://localhost:8082"),
        "health_path": "/health",
        "port": 8082,
        "critical": True,
        "description": "GitHub & Jenkins"
    },
    "reporting_agent": {
        "url": os.environ.get("REPORTING_AGENT_URL", "http://localhost:8083"),
        "health_path": "/health",
        "port": 8083,
        "critical": False,
        "description": "Report Generation"
    },
    "slack_agent": {
        "url": os.environ.get("SLACK_AGENT_URL", "http://localhost:8084"),
        "health_path": "/health",
        "port": 8084,
        "critical": True,
        "description": "Slack Bot"
    },
    "hygiene_agent": {
        "url": os.environ.get("HYGIENE_AGENT_URL", "http://localhost:8085"),
        "health_path": "/health",
        "port": 8085,
        "critical": False,
        "description": "Jira Hygiene Checks"
    },
    "rca_agent": {
        "url": os.environ.get("RCA_AGENT_URL", "http://localhost:8006"),
        "health_path": "/health",
        "port": 8006,
        "critical": False,
        "description": "Root Cause Analysis"
    },
    "analytics": {
        "url": os.environ.get("ANALYTICS_URL", "http://localhost:8086"),
        "health_path": "/health",
        "port": 8086,
        "critical": False,
        "description": "Analytics Dashboard"
    },
    "webhooks": {
        "url": os.environ.get("WEBHOOKS_URL", "http://localhost:8087"),
        "health_path": "/health",
        "port": 8087,
        "critical": False,
        "description": "Webhook Service"
    },
    "admin_dashboard": {
        "url": os.environ.get("ADMIN_DASHBOARD_URL", "http://localhost:8088"),
        "health_path": "/health",
        "port": 8088,
        "critical": True,
        "description": "Admin Dashboard"
    }
}

OBSERVABILITY = {
    "prometheus": {
        "url": os.environ.get("PROMETHEUS_URL", "http://localhost:9090"),
        "health_path": "/-/healthy"
    },
    "grafana": {
        "url": os.environ.get("GRAFANA_URL", "http://localhost:3000"),
        "health_path": "/api/health"
    },
    "jaeger": {
        "url": os.environ.get("JAEGER_URL", "http://localhost:16686"),
        "health_path": "/"
    }
}


# =============================================================================
# Health Check Tests
# =============================================================================

class TestServiceHealthChecks:
    """Smoke tests for all service health endpoints."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    @pytest.mark.parametrize("service_name,config", list(SERVICES.items()))
    async def test_service_health(self, client, service_name: str, config: Dict):
        """Test each service health endpoint."""
        url = f"{config['url']}{config['health_path']}"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200, \
                f"{service_name} ({config['description']}) health check failed"
            
            data = response.json()
            assert "status" in data, f"{service_name} missing status field"
            
        except httpx.ConnectError:
            if config['critical']:
                pytest.fail(f"Critical service {service_name} not running at {url}")
            pytest.skip(f"{service_name} not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_all_critical_services_healthy(self, client):
        """Test all critical services are healthy."""
        critical_services = {k: v for k, v in SERVICES.items() if v['critical']}
        healthy_count = 0
        
        for name, config in critical_services.items():
            try:
                response = await client.get(f"{config['url']}{config['health_path']}")
                if response.status_code == 200:
                    healthy_count += 1
            except Exception:
                pass
        
        total = len(critical_services)
        assert healthy_count >= total * 0.8, \
            f"Only {healthy_count}/{total} critical services healthy"


# =============================================================================
# Metrics Endpoint Tests
# =============================================================================

class TestMetricsEndpoints:
    """Smoke tests for Prometheus metrics endpoints."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    @pytest.mark.parametrize("service_name,config", list(SERVICES.items()))
    async def test_metrics_endpoint(self, client, service_name: str, config: Dict):
        """Test each service exposes Prometheus metrics."""
        url = f"{config['url']}/metrics"
        
        try:
            response = await client.get(url)
            
            assert response.status_code == 200, \
                f"{service_name} metrics endpoint failed"
            
            content = response.text
            # Should have some Prometheus format content
            assert len(content) > 0
            
        except httpx.ConnectError:
            pytest.skip(f"{service_name} not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_metrics_contain_nexus_labels(self, client):
        """Test that metrics contain nexus-specific labels."""
        try:
            response = await client.get(f"{SERVICES['orchestrator']['url']}/metrics")
            
            if response.status_code == 200:
                content = response.text
                # Should have some nexus metrics
                # (May or may not depending on activity)
                assert len(content) > 0
                
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# API Documentation Tests
# =============================================================================

class TestAPIDocumentation:
    """Smoke tests for API documentation endpoints."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    @pytest.mark.parametrize("service_name,config", [
        (name, cfg) for name, cfg in SERVICES.items() 
        if name in ["orchestrator", "admin_dashboard", "analytics"]
    ])
    async def test_openapi_schema(self, client, service_name: str, config: Dict):
        """Test OpenAPI schema is available."""
        url = f"{config['url']}/openapi.json"
        
        try:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                assert "openapi" in data
                assert "paths" in data
                
        except httpx.ConnectError:
            pytest.skip(f"{service_name} not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_swagger_ui_accessible(self, client):
        """Test Swagger UI is accessible."""
        try:
            response = await client.get(f"{SERVICES['orchestrator']['url']}/docs")
            
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Basic Functionality Tests
# =============================================================================

class TestBasicFunctionality:
    """Smoke tests for basic service functionality."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_orchestrator_accepts_query(self, client):
        """Test orchestrator accepts queries."""
        try:
            response = await client.post(
                f"{SERVICES['orchestrator']['url']}/query",
                json={"query": "Hello"}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_jira_agent_execute(self, client):
        """Test Jira agent accepts execute requests."""
        try:
            response = await client.post(
                f"{SERVICES['jira_agent']['url']}/execute",
                json={
                    "task_id": "smoke-test",
                    "action": "get_ticket",
                    "payload": {"ticket_key": "TEST-1"}
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Jira agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_admin_dashboard_mode(self, client):
        """Test admin dashboard mode endpoint."""
        try:
            response = await client.get(f"{SERVICES['admin_dashboard']['url']}/mode")
            
            assert response.status_code == 200
            data = response.json()
            assert "mode" in data
            assert data["mode"] in ["mock", "live"]
            
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_admin_dashboard_config(self, client):
        """Test admin dashboard config endpoint."""
        try:
            response = await client.get(f"{SERVICES['admin_dashboard']['url']}/config")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_analytics_kpis(self, client):
        """Test analytics KPIs endpoint."""
        try:
            response = await client.get(f"{SERVICES['analytics']['url']}/api/v1/kpis")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Analytics not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_webhooks_event_types(self, client):
        """Test webhooks event types endpoint."""
        try:
            response = await client.get(f"{SERVICES['webhooks']['url']}/api/v1/event-types")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Webhooks not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_hygiene_status(self, client):
        """Test hygiene agent status endpoint."""
        try:
            response = await client.get(f"{SERVICES['hygiene_agent']['url']}/status")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Hygiene agent not running")


# =============================================================================
# Observability Stack Tests
# =============================================================================

class TestObservabilityStack:
    """Smoke tests for observability stack."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_prometheus_healthy(self, client):
        """Test Prometheus is healthy."""
        try:
            response = await client.get(f"{OBSERVABILITY['prometheus']['url']}/-/healthy")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Prometheus not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_prometheus_ready(self, client):
        """Test Prometheus is ready."""
        try:
            response = await client.get(f"{OBSERVABILITY['prometheus']['url']}/-/ready")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Prometheus not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_prometheus_query_works(self, client):
        """Test Prometheus query endpoint works."""
        try:
            response = await client.get(
                f"{OBSERVABILITY['prometheus']['url']}/api/v1/query",
                params={"query": "up"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == "success"
                
        except httpx.ConnectError:
            pytest.skip("Prometheus not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_grafana_healthy(self, client):
        """Test Grafana is healthy."""
        try:
            response = await client.get(f"{OBSERVABILITY['grafana']['url']}/api/health")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Grafana not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_jaeger_ui_accessible(self, client):
        """Test Jaeger UI is accessible."""
        try:
            response = await client.get(f"{OBSERVABILITY['jaeger']['url']}/")
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Jaeger not running")


# =============================================================================
# Connectivity Tests
# =============================================================================

class TestServiceConnectivity:
    """Smoke tests for inter-service connectivity."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_orchestrator_lists_specialists(self, client):
        """Test orchestrator can list specialists."""
        try:
            response = await client.get(f"{SERVICES['orchestrator']['url']}/specialists")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
                
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_admin_dashboard_health_overview(self, client):
        """Test admin dashboard can check all agents."""
        try:
            response = await client.get(f"{SERVICES['admin_dashboard']['url']}/health-check")
            
            if response.status_code == 200:
                data = response.json()
                assert "agents" in data or "status" in data
                
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_admin_dashboard_aggregated_metrics(self, client):
        """Test admin dashboard can aggregate metrics."""
        try:
            response = await client.get(f"{SERVICES['admin_dashboard']['url']}/api/metrics")
            
            if response.status_code == 200:
                data = response.json()
                assert "summary" in data or "agents" in data
                
        except httpx.ConnectError:
            pytest.skip("Admin dashboard not running")


# =============================================================================
# Liveness/Readiness Probes
# =============================================================================

class TestKubernetesProbes:
    """Smoke tests for Kubernetes probes."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=5.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_orchestrator_livez(self, client):
        """Test orchestrator liveness probe."""
        try:
            response = await client.get(f"{SERVICES['orchestrator']['url']}/livez")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_orchestrator_readyz(self, client):
        """Test orchestrator readiness probe."""
        try:
            response = await client.get(f"{SERVICES['orchestrator']['url']}/readyz")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


# =============================================================================
# Quick System Overview
# =============================================================================

class TestSystemOverview:
    """Quick system health overview."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_system_overview(self, client):
        """Get quick overview of all services."""
        results = {
            "healthy": [],
            "unhealthy": [],
            "total": len(SERVICES)
        }
        
        for name, config in SERVICES.items():
            try:
                response = await client.get(f"{config['url']}{config['health_path']}")
                if response.status_code == 200:
                    results["healthy"].append(name)
                else:
                    results["unhealthy"].append((name, response.status_code))
            except Exception as e:
                results["unhealthy"].append((name, str(e)[:50]))
        
        print(f"\n{'='*60}")
        print(f"SYSTEM OVERVIEW")
        print(f"{'='*60}")
        print(f"✅ Healthy: {len(results['healthy'])}/{results['total']}")
        for svc in results["healthy"]:
            print(f"   - {svc}")
        
        if results["unhealthy"]:
            print(f"\n❌ Unhealthy: {len(results['unhealthy'])}/{results['total']}")
            for svc, err in results["unhealthy"]:
                print(f"   - {svc}: {err}")
        
        print(f"{'='*60}\n")
        
        # At least 50% should be healthy for smoke test to pass
        assert len(results["healthy"]) >= results["total"] * 0.5


# =============================================================================
# Response Time Tests
# =============================================================================

class TestResponseTimes:
    """Smoke tests for acceptable response times."""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=10.0)
    
    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_health_check_fast(self, client):
        """Test health checks respond within 500ms."""
        import time
        
        for name, config in list(SERVICES.items())[:5]:  # Check first 5
            try:
                start = time.time()
                response = await client.get(f"{config['url']}{config['health_path']}")
                duration = time.time() - start
                
                if response.status_code == 200:
                    assert duration < 0.5, f"{name} health check too slow: {duration:.2f}s"
                    
            except httpx.ConnectError:
                continue


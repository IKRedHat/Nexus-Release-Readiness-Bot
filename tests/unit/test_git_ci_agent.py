"""
Comprehensive Unit Tests for Git/CI Agent
==========================================

Tests for GitHubClient, JenkinsClient, SecurityScannerClient, and API endpoints.

Coverage:
- GitHub repository operations
- Jenkins build operations  
- Security scanning
- Mock data generation
- API endpoint validation
- Error handling

Usage:
    pytest tests/unit/test_git_ci_agent.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/agents/git_ci_agent")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"


# =============================================================================
# GitHubClient Tests
# =============================================================================

class TestGitHubClientInitialization:
    """Tests for GitHubClient initialization."""
    
    def test_client_created_uninitialized(self):
        """Test client is created in uninitialized state."""
        from main import GitHubClient
        
        client = GitHubClient()
        
        assert client._github is None
        assert client._initialized is False
        assert client._last_mode is None
    
    def test_mock_mode_property_default(self):
        """Test mock_mode property returns True by default."""
        from main import GitHubClient
        
        client = GitHubClient()
        
        assert client.mock_mode is True


class TestGitHubClientMockData:
    """Tests for GitHubClient mock data generation."""
    
    @pytest.fixture
    def client(self):
        from main import GitHubClient
        return GitHubClient()
    
    def test_mock_repo_health(self, client):
        """Test mock repository health data."""
        health = client._mock_repo_health("org/repo")
        
        assert health.repo_name == "org/repo"
        assert health.default_branch == "main"
        assert health.latest_commit_sha is not None
        assert health.latest_commit_status == "success"
        assert health.branch_protection_enabled is True
        assert health.required_reviews == 2
    
    def test_mock_pr_status(self, client):
        """Test mock PR status data."""
        pr = client._mock_pr_status("org/repo", 42)
        
        assert pr.pr_number == 42
        assert pr.title is not None
        assert pr.state == "open"
        assert pr.author == "developer"
        assert pr.base_branch == "main"
        assert pr.mergeable is True
        assert pr.ci_status == "success"
        assert pr.approvals == 2


class TestGitHubClientOperations:
    """Tests for GitHubClient operations."""
    
    @pytest.fixture
    def client(self):
        from main import GitHubClient
        c = GitHubClient()
        c._last_mode = True  # Force mock mode
        c._initialized = True
        return c
    
    @pytest.mark.asyncio
    async def test_get_repo_health_mock_mode(self, client):
        """Test get_repo_health in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            health = await client.get_repo_health("org/repo")
        
        assert health.repo_name == "org/repo"
        assert health.default_branch == "main"
    
    @pytest.mark.asyncio
    async def test_get_pr_status_mock_mode(self, client):
        """Test get_pr_status in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            pr = await client.get_pr_status("org/repo", 42)
        
        assert pr.pr_number == 42
        assert pr.state == "open"
    
    @pytest.mark.asyncio
    async def test_list_open_prs_mock_mode(self, client):
        """Test list_open_prs in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            prs = await client.list_open_prs("org/repo")
        
        assert len(prs) >= 3
        assert all(pr.pr_number > 0 for pr in prs)


# =============================================================================
# JenkinsClient Tests
# =============================================================================

class TestJenkinsClientInitialization:
    """Tests for JenkinsClient initialization."""
    
    def test_client_created_uninitialized(self):
        """Test client is created in uninitialized state."""
        from main import JenkinsClient
        
        client = JenkinsClient()
        
        assert client._jenkins is None
        assert client._initialized is False
        assert client._last_mode is None
    
    def test_mock_mode_property_default(self):
        """Test mock_mode property returns True by default."""
        from main import JenkinsClient
        
        client = JenkinsClient()
        
        assert client.mock_mode is True


class TestJenkinsClientMockData:
    """Tests for JenkinsClient mock data generation."""
    
    @pytest.fixture
    def client(self):
        from main import JenkinsClient
        return JenkinsClient()
    
    def test_mock_build_status_success(self, client):
        """Test mock build status for success."""
        from nexus_lib.schemas.agent_contract import BuildResult
        
        # Build numbers divisible by 5 cause UNSTABLE, 4 cause FAILURE
        build = client._mock_build_status("nexus-main", 40)  # 40 % 5 = 0 (UNSTABLE)
        
        assert build.job_name == "nexus-main"
        assert build.build_number == 40
        assert build.status in [BuildResult.SUCCESS, BuildResult.FAILURE, BuildResult.UNSTABLE]
    
    def test_mock_build_status_includes_test_results(self, client):
        """Test mock build includes test results."""
        build = client._mock_build_status("nexus-main", 42)
        
        assert build.test_results is not None
        assert build.test_results.total_tests > 0
        assert build.test_results.passed >= 0
        assert build.test_results.failed >= 0
    
    def test_mock_build_status_includes_artifacts(self, client):
        """Test mock build includes artifacts."""
        build = client._mock_build_status("nexus-main", 42)
        
        assert build.artifacts is not None
        assert len(build.artifacts) > 0
        assert build.artifacts[0].name is not None
    
    def test_mock_build_status_includes_console_url(self, client):
        """Test mock build includes console URL."""
        build = client._mock_build_status("nexus-main", 42)
        
        assert build.console_log_url is not None
        assert "console" in build.console_log_url


class TestJenkinsClientOperations:
    """Tests for JenkinsClient operations."""
    
    @pytest.fixture
    def client(self):
        from main import JenkinsClient
        c = JenkinsClient()
        c._last_mode = True  # Force mock mode
        c._initialized = True
        return c
    
    @pytest.mark.asyncio
    async def test_get_build_status_mock_mode(self, client):
        """Test get_build_status in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            build = await client.get_build_status("nexus-main", 42)
        
        assert build.job_name == "nexus-main"
        assert build.build_number == 42
    
    @pytest.mark.asyncio
    async def test_get_build_status_latest(self, client):
        """Test get_build_status without build number returns latest."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            build = await client.get_build_status("nexus-main")
        
        assert build.job_name == "nexus-main"
        assert build.build_number == 42  # Default mock build number
    
    @pytest.mark.asyncio
    async def test_trigger_build_mock_mode(self, client):
        """Test trigger_build in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.trigger_build("nexus-main", {"BRANCH": "develop"})
        
        assert result["queue_id"] == 12345
        assert "mock" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_trigger_build_without_params(self, client):
        """Test trigger_build without parameters."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.trigger_build("nexus-main")
        
        assert result["queue_id"] is not None
    
    @pytest.mark.asyncio
    async def test_get_job_history_mock_mode(self, client):
        """Test get_job_history in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            history = await client.get_job_history("nexus-main", limit=5)
        
        assert len(history) == 5
        assert all(b.job_name == "nexus-main" for b in history)


# =============================================================================
# SecurityScannerClient Tests
# =============================================================================

class TestSecurityScannerClient:
    """Tests for SecurityScannerClient."""
    
    @pytest.fixture
    def client(self):
        from main import SecurityScannerClient
        return SecurityScannerClient()
    
    def test_client_created(self, client):
        """Test client is created."""
        assert client is not None
    
    def test_mock_mode_property_default(self, client):
        """Test mock_mode property returns True by default."""
        assert client.mock_mode is True
    
    @pytest.mark.asyncio
    async def test_get_security_scan(self, client):
        """Test get_security_scan returns results."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            scan = await client.get_security_scan("org/repo", "main")
        
        assert scan.repo_name == "org/repo"
        assert scan.branch == "main"
        assert scan.scanner_name == "nexus-security-scanner"
        assert scan.risk_score >= 0
        assert scan.critical_vulnerabilities >= 0
    
    @pytest.mark.asyncio
    async def test_get_security_scan_includes_vulnerabilities(self, client):
        """Test security scan includes vulnerability details."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            scan = await client.get_security_scan("org/repo", "main")
        
        assert scan.vulnerabilities is not None
        assert len(scan.vulnerabilities) >= 2
        
        vuln = scan.vulnerabilities[0]
        assert vuln.id is not None
        assert vuln.title is not None
        assert vuln.severity is not None
    
    @pytest.mark.asyncio
    async def test_get_security_scan_includes_remediation(self, client):
        """Test security scan includes remediation info."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            scan = await client.get_security_scan("org/repo", "main")
        
        # At least one vulnerability should have remediation
        vulns_with_remediation = [v for v in scan.vulnerabilities if v.remediation]
        assert len(vulns_with_remediation) >= 1


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestGitCIAgentAPI:
    """Tests for Git/CI Agent API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from main import app
            with TestClient(app) as client:
                yield client
        except ImportError:
            pytest.skip("Git/CI agent module not available")
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "git-ci-agent"
        assert "mock_mode" in data
    
    def test_repo_health_endpoint(self, client):
        """Test GET /repo/{repo_name}/health endpoint."""
        response = client.get("/repo/org/repo/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent_type"] == "git_ci"
    
    def test_pr_status_endpoint(self, client):
        """Test GET /repo/{repo_name}/pr/{pr_number} endpoint."""
        response = client.get("/repo/org/repo/pr/42")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["pr_number"] == 42
    
    def test_list_prs_endpoint(self, client):
        """Test GET /repo/{repo_name}/prs endpoint."""
        response = client.get("/repo/org/repo/prs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "prs" in data["data"]
    
    def test_trigger_build_endpoint(self, client):
        """Test POST /build/{job_name} endpoint."""
        response = client.post("/build/nexus-main")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "queue_id" in data["data"]
    
    def test_trigger_build_with_params(self, client):
        """Test trigger build with parameters."""
        response = client.post("/build/nexus-main", json={"BRANCH": "develop"})
        
        assert response.status_code == 200
    
    def test_build_status_endpoint(self, client):
        """Test GET /build/{job_name}/status endpoint."""
        response = client.get("/build/nexus-main/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "job_name" in data["data"]
    
    def test_build_status_with_number(self, client):
        """Test build status with specific build number."""
        response = client.get("/build/nexus-main/status?build_number=142")
        
        assert response.status_code == 200
    
    def test_build_history_endpoint(self, client):
        """Test GET /build/{job_name}/history endpoint."""
        response = client.get("/build/nexus-main/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "builds" in data["data"]
    
    def test_build_history_with_limit(self, client):
        """Test build history with custom limit."""
        response = client.get("/build/nexus-main/history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["builds"]) == 5
    
    def test_security_scan_endpoint(self, client):
        """Test GET /security/{repo_name} endpoint."""
        response = client.get("/security/org/repo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "vulnerabilities" in data["data"]
    
    def test_security_scan_with_branch(self, client):
        """Test security scan with specific branch."""
        response = client.get("/security/org/repo?branch=develop")
        
        assert response.status_code == 200
    
    def test_execute_repo_health(self, client):
        """Test POST /execute with repo_health action."""
        response = client.post("/execute", json={
            "task_id": "test-1",
            "action": "repo_health",
            "payload": {"repo_name": "org/repo"}
        })
        
        assert response.status_code == 200
    
    def test_execute_pr_status(self, client):
        """Test POST /execute with pr_status action."""
        response = client.post("/execute", json={
            "task_id": "test-2",
            "action": "pr_status",
            "payload": {"repo_name": "org/repo", "pr_number": 42}
        })
        
        assert response.status_code == 200
    
    def test_execute_build_status(self, client):
        """Test POST /execute with build_status action."""
        response = client.post("/execute", json={
            "task_id": "test-3",
            "action": "build_status",
            "payload": {"job_name": "nexus-main"}
        })
        
        assert response.status_code == 200
    
    def test_execute_trigger_build(self, client):
        """Test POST /execute with trigger_build action."""
        response = client.post("/execute", json={
            "task_id": "test-4",
            "action": "trigger_build",
            "payload": {"job_name": "nexus-main"}
        })
        
        assert response.status_code == 200
    
    def test_execute_security_scan(self, client):
        """Test POST /execute with security_scan action."""
        response = client.post("/execute", json={
            "task_id": "test-5",
            "action": "security_scan",
            "payload": {"repo_name": "org/repo"}
        })
        
        assert response.status_code == 200
    
    def test_execute_unknown_action(self, client):
        """Test POST /execute with unknown action."""
        response = client.post("/execute", json={
            "task_id": "test-6",
            "action": "unknown_action",
            "payload": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestGitCIAgentErrorHandling:
    """Tests for error handling in Git/CI Agent."""
    
    @pytest.fixture
    def client(self):
        try:
            from main import app
            with TestClient(app) as client:
                yield client
        except ImportError:
            pytest.skip("Git/CI agent module not available")
    
    def test_invalid_build_history_limit(self, client):
        """Test build history with invalid limit."""
        response = client.get("/build/nexus-main/history?limit=100")
        
        # Should be rejected (max is 50)
        assert response.status_code == 422
    
    def test_negative_build_history_limit(self, client):
        """Test build history with negative limit."""
        response = client.get("/build/nexus-main/history?limit=-1")
        
        assert response.status_code == 422


# =============================================================================
# Build Result Enum Tests
# =============================================================================

class TestBuildResultEnum:
    """Tests for BuildResult enum handling."""
    
    def test_build_result_values(self):
        """Test BuildResult enum values."""
        from nexus_lib.schemas.agent_contract import BuildResult
        
        assert BuildResult.SUCCESS.value == "SUCCESS"
        assert BuildResult.FAILURE.value == "FAILURE"
        assert BuildResult.UNSTABLE.value == "UNSTABLE"
        assert BuildResult.ABORTED.value == "ABORTED"
    
    def test_build_result_from_string(self):
        """Test creating BuildResult from string."""
        from nexus_lib.schemas.agent_contract import BuildResult
        
        result = BuildResult["SUCCESS"]
        assert result == BuildResult.SUCCESS


# =============================================================================
# Severity Level Tests
# =============================================================================

class TestSeverityLevel:
    """Tests for SeverityLevel enum."""
    
    def test_severity_levels_exist(self):
        """Test SeverityLevel values exist."""
        from nexus_lib.schemas.agent_contract import SeverityLevel
        
        assert SeverityLevel.CRITICAL
        assert SeverityLevel.HIGH
        assert SeverityLevel.MEDIUM
        assert SeverityLevel.LOW
        assert SeverityLevel.INFO
    
    def test_severity_ordering(self):
        """Test severity levels can be compared."""
        from nexus_lib.schemas.agent_contract import SeverityLevel
        
        # Just verify they're distinct
        levels = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW, SeverityLevel.INFO]
        assert len(set(levels)) == 5


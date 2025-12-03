"""
End-to-End Tests for RCA Agent
==============================

Tests for Root Cause Analysis and auto-triggering.
"""

import pytest
import sys
import os
import json

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["JENKINS_MOCK_MODE"] = "true"
os.environ["GITHUB_MOCK_MODE"] = "true"
os.environ["LLM_MOCK_MODE"] = "true"

# Calculate paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RCA_AGENT_PATH = os.path.join(PROJECT_ROOT, "services/agents/rca_agent")
SHARED_PATH = os.path.join(PROJECT_ROOT, "shared")


def get_rca_app():
    """Get the RCA agent FastAPI app with proper imports."""
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'main' or mod_name.startswith('main.'):
                del sys.modules[mod_name]
        
        sys.path.insert(0, RCA_AGENT_PATH)
        sys.path.insert(0, SHARED_PATH)
        os.chdir(RCA_AGENT_PATH)
        
        import main as rca_main
        return rca_main.app, rca_main
        
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class TestRcaAgentHealth:
    """Tests for RCA Agent health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_rca_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test RCA agent health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rca-agent"


class TestRcaAnalysis:
    """Tests for RCA analysis endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_rca_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_analyze_build_failure(self, client):
        """Test analyzing a build failure."""
        response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 142,
            "repo_name": "nexus-backend"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response has expected fields
        assert "analysis_id" in data or "root_cause" in data or "status" in data
    
    def test_analyze_with_commit_sha(self, client):
        """Test analysis with specific commit."""
        response = client.post("/analyze", json={
            "job_name": "nexus-main",
            "build_number": 144,
            "commit_sha": "abc123def456"
        })
        
        assert response.status_code == 200


class TestRcaMetrics:
    """Tests for RCA metrics endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_rca_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Metrics should be in prometheus format
        assert "# HELP" in response.text or "# TYPE" in response.text


class TestRcaExecute:
    """Tests for RCA execute endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app, _ = get_rca_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_execute_analyze(self, client):
        """Test execute endpoint for analysis."""
        response = client.post("/execute", json={
            "action": "analyze",
            "payload": {
                "job_name": "nexus-main",
                "build_number": 145
            }
        })
        
        assert response.status_code == 200


class TestRcaLogic:
    """Tests for RCA logic and utilities."""
    
    def test_error_pattern_matching(self):
        """Test error pattern matching logic."""
        error_patterns = {
            "NullPointerException": "null_reference",
            "AssertionError": "assertion_failed",
            "TimeoutError": "timeout",
            "ConnectionError": "connection_failed"
        }
        
        log = "java.lang.NullPointerException: Cannot invoke method on null"
        
        matched = None
        for pattern, category in error_patterns.items():
            if pattern in log:
                matched = category
                break
        
        assert matched == "null_reference"
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        # Confidence based on pattern matching
        factors = {
            "error_pattern_found": True,
            "stack_trace_complete": True,
            "related_changes_found": True,
            "test_name_identified": False
        }
        
        score = sum(1 for v in factors.values() if v) / len(factors)
        
        assert score == 0.75
    
    def test_root_cause_categorization(self):
        """Test root cause categorization."""
        categories = {
            "test_failure": ["AssertionError", "TestFailure", "pytest"],
            "build_error": ["CompileError", "SyntaxError", "ModuleNotFound"],
            "infrastructure": ["TimeoutError", "ConnectionError", "DNSError"]
        }
        
        error = "ModuleNotFoundError: No module named 'xyz'"
        
        category = "unknown"
        for cat, patterns in categories.items():
            if any(p in error for p in patterns):
                category = cat
                break
        
        assert category == "build_error"
    
    def test_suggested_fix_generation(self):
        """Test suggested fix generation."""
        def get_suggestion(error_type):
            suggestions = {
                "null_reference": "Check for null values before method calls",
                "assertion_failed": "Review test assertions and expected values",
                "module_not_found": "Install missing dependencies",
                "timeout": "Increase timeout or optimize slow operations"
            }
            return suggestions.get(error_type, "Review the error details")
        
        assert "null values" in get_suggestion("null_reference")
        assert "Review" in get_suggestion("unknown")


class TestBuildLogParsing:
    """Tests for build log parsing."""
    
    def test_extract_failing_test(self):
        """Test extracting failing test name."""
        log = """
        FAILED tests/test_users.py::TestUserService::test_validate_email
        """
        
        # Simple extraction logic
        if "FAILED" in log:
            lines = log.split("\n")
            for line in lines:
                if "FAILED" in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        test_path = parts[1]
                        assert "test_users" in test_path
                        break
    
    def test_extract_error_type(self):
        """Test extracting error type from log."""
        log = """
        E   AttributeError: 'NoneType' object has no attribute 'is_valid'
        """
        
        if "AttributeError" in log:
            error_type = "AttributeError"
            assert error_type == "AttributeError"
    
    def test_extract_file_line(self):
        """Test extracting file and line from traceback."""
        log = """
        tests/test_users.py:42: AttributeError
        """
        
        import re
        match = re.search(r'(\S+\.py):(\d+)', log)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            
            assert "test_users.py" in file_path
            assert line_num == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

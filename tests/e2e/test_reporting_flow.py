"""
End-to-End Tests for Reporting Flow
Tests report generation and publishing
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath("services/agents/reporting_agent"))
sys.path.insert(0, os.path.abspath("shared"))


class TestReportingAgent:
    """E2E tests for the Reporting Agent"""
    
    @pytest.fixture
    def client(self):
        """Create test client for reporting agent"""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test reporting agent health"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reporting-agent"
    
    def test_generate_report(self, client, sample_release_stats):
        """Test generating a release report"""
        response = client.post("/generate", json={
            "stats": sample_release_stats,
            "builds": [
                {
                    "job_name": "nexus-main",
                    "build_number": 142,
                    "status": "SUCCESS",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "duration_seconds": 485
                }
            ],
            "security_scans": [
                {
                    "repo_name": "nexus/backend",
                    "risk_score": 25,
                    "critical_vulnerabilities": 0,
                    "high_vulnerabilities": 2
                }
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "html" in data["data"]
        assert "Release Readiness" in data["data"]["html"]
    
    def test_preview_report(self, client):
        """Test report preview endpoint"""
        response = client.get("/preview", params={
            "release_version": "v2.0.0",
            "decision": "GO"
        })
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "GO" in response.text
        assert "v2.0.0" in response.text
    
    def test_preview_report_no_go(self, client):
        """Test report preview with NO_GO decision"""
        response = client.get("/preview", params={
            "release_version": "v1.9.0",
            "decision": "NO_GO"
        })
        
        assert response.status_code == 200
        assert "NO-GO" in response.text
    
    def test_analyze_readiness_go(self, client):
        """Test analyze endpoint with passing criteria"""
        response = client.post("/analyze", json={
            "stats": {
                "ticket_completion_rate": 95.0,
                "blocked_tickets": 0,
                "test_coverage_percentage": 85.0,
                "failing_tests": 0,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 1,
                "last_build_status": "SUCCESS"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["decision"] == "GO"
        assert data["data"]["required_criteria_passed"] is True
    
    def test_analyze_readiness_no_go(self, client):
        """Test analyze endpoint with failing criteria"""
        response = client.post("/analyze", json={
            "stats": {
                "ticket_completion_rate": 70.0,  # Below 90%
                "blocked_tickets": 3,  # Blockers present
                "test_coverage_percentage": 60.0,  # Below 80%
                "failing_tests": 5,  # Tests failing
                "critical_vulnerabilities": 2,  # Critical vulns!
                "last_build_status": "FAILURE"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["decision"] == "NO_GO"
        assert len(data["data"]["blockers"]) > 0
    
    def test_publish_report_mock(self, client, sample_release_stats):
        """Test publishing report (mock mode)"""
        response = client.post("/publish", params={
            "space_key": "REL",
            "title": "Release v2.0.0 Readiness Report"
        }, json={
            "stats": sample_release_stats
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "url" in data["data"]


class TestReportContent:
    """Tests for report content quality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_report_contains_all_sections(self, client):
        """Verify report contains all expected sections"""
        response = client.get("/preview", params={
            "release_version": "v2.0.0",
            "decision": "GO"
        })
        
        html = response.text
        
        # Check for required sections
        assert "Release Readiness Report" in html
        assert "Ticket Completion" in html
        assert "Test Coverage" in html
        assert "Security" in html
        assert "Checklist" in html
    
    def test_report_styling(self, client):
        """Verify report has proper CSS styling"""
        response = client.get("/preview")
        
        html = response.text
        
        # Check for CSS
        assert "<style>" in html
        assert "font-family" in html
        assert "#28a745" in html or "green" in html  # Success color


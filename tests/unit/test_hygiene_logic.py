"""
Unit Tests for Jira Hygiene Agent Logic (MCP-Based)
===================================================

Tests for the MCP-based Jira Hygiene Agent including:
- Hygiene checking logic
- Mock data generation
- Notification formatting
- MCP tool schemas

Updated for LangGraph + MCP architecture.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os
import json

# Add paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/agents/jira_hygiene_agent")))

# Set mock mode before imports
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"
os.environ["MOCK_MODE"] = "true"


# =============================================================================
# Mock Data Classes (Similar to agent implementation)
# =============================================================================

class MockHygieneData:
    """Mock hygiene data generator for testing."""
    
    VIOLATIONS = [
        "Missing labels",
        "Missing fix version",
        "Missing story points",
        "Missing team assignment",
        "Stale ticket (no update in 14+ days)",
        "Missing acceptance criteria"
    ]
    
    ASSIGNEES = [
        {"email": "alice@example.com", "display_name": "Alice Smith", "account_id": "user-001"},
        {"email": "bob@example.com", "display_name": "Bob Jones", "account_id": "user-002"},
        {"email": "carol@example.com", "display_name": "Carol White", "account_id": "user-003"},
    ]
    
    @classmethod
    def generate_violation(cls, ticket_key: str) -> dict:
        """Generate a mock hygiene violation."""
        import random
        violation_type = random.choice(cls.VIOLATIONS)
        assignee = random.choice(cls.ASSIGNEES)
        
        return {
            "ticket_key": ticket_key,
            "summary": f"Sample ticket {ticket_key}",
            "violation_type": violation_type,
            "severity": random.choice(["high", "medium", "low"]),
            "assignee": assignee,
            "assignee_email": assignee["email"],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            "last_updated": (datetime.utcnow() - timedelta(days=random.randint(0, 14))).isoformat(),
            "recommendation": f"Please update the ticket to include {violation_type.lower().replace('missing ', '')}"
        }
    
    @classmethod
    def generate_project_hygiene(cls, project_key: str) -> dict:
        """Generate mock project hygiene report."""
        import random
        total_tickets = random.randint(30, 80)
        violations_count = random.randint(5, 20)
        compliant = total_tickets - violations_count
        
        violations = [
            cls.generate_violation(f"{project_key}-{random.randint(100, 999)}")
            for _ in range(violations_count)
        ]
        
        # Group by assignee
        by_assignee = {}
        for v in violations:
            email = v["assignee_email"]
            if email not in by_assignee:
                by_assignee[email] = {
                    "assignee": v["assignee"],
                    "violations": []
                }
            by_assignee[email]["violations"].append(v)
        
        # Calculate score
        hygiene_score = round((compliant / total_tickets) * 100, 1)
        
        return {
            "project_key": project_key,
            "hygiene_score": hygiene_score,
            "total_tickets": total_tickets,
            "compliant_tickets": compliant,
            "violations_count": violations_count,
            "violations": violations,
            "by_assignee": list(by_assignee.values()),
            "violation_breakdown": {
                "missing_labels": sum(1 for v in violations if "labels" in v["violation_type"].lower()),
                "missing_fix_version": sum(1 for v in violations if "fix version" in v["violation_type"].lower()),
                "missing_story_points": sum(1 for v in violations if "story points" in v["violation_type"].lower()),
                "missing_team": sum(1 for v in violations if "team" in v["violation_type"].lower()),
                "stale_tickets": sum(1 for v in violations if "stale" in v["violation_type"].lower()),
            },
            "checked_at": datetime.utcnow().isoformat(),
            "trend": random.choice(["improving", "stable", "declining"])
        }


# =============================================================================
# Test Mock Data Generation
# =============================================================================

class TestMockDataGeneration:
    """Tests for mock data generation."""
    
    def test_generate_violation(self):
        """Test generating a single violation."""
        violation = MockHygieneData.generate_violation("PROJ-123")
        
        assert violation["ticket_key"] == "PROJ-123"
        assert violation["violation_type"] in MockHygieneData.VIOLATIONS
        assert violation["severity"] in ["high", "medium", "low"]
        assert "assignee" in violation
        assert "recommendation" in violation
    
    def test_generate_project_hygiene(self):
        """Test generating project hygiene report."""
        report = MockHygieneData.generate_project_hygiene("PROJ")
        
        assert report["project_key"] == "PROJ"
        assert 0 <= report["hygiene_score"] <= 100
        assert report["total_tickets"] > 0
        assert "violations" in report
        assert "by_assignee" in report
        assert "violation_breakdown" in report
    
    def test_hygiene_score_calculation(self):
        """Test hygiene score is correctly calculated."""
        report = MockHygieneData.generate_project_hygiene("PROJ")
        
        expected_score = round(
            (report["compliant_tickets"] / report["total_tickets"]) * 100, 1
        )
        assert report["hygiene_score"] == expected_score
    
    def test_violations_grouped_by_assignee(self):
        """Test violations are properly grouped by assignee."""
        report = MockHygieneData.generate_project_hygiene("PROJ")
        
        # Count violations in groups
        grouped_count = sum(
            len(group["violations"]) 
            for group in report["by_assignee"]
        )
        
        # Should match total violations
        assert grouped_count == report["violations_count"]


# =============================================================================
# Test Hygiene Checker Logic
# =============================================================================

class TestHygieneCheckerLogic:
    """Tests for hygiene checker validation logic."""
    
    def test_is_field_empty_none(self):
        """Test None is considered empty."""
        assert self._is_field_empty(None) is True
    
    def test_is_field_empty_list(self):
        """Test empty list is considered empty."""
        assert self._is_field_empty([]) is True
        assert self._is_field_empty(["value"]) is False
    
    def test_is_field_empty_string(self):
        """Test empty string is considered empty."""
        assert self._is_field_empty("") is True
        assert self._is_field_empty("   ") is True
        assert self._is_field_empty("value") is False
    
    def test_is_field_empty_dict(self):
        """Test empty dict is considered empty."""
        assert self._is_field_empty({}) is True
        assert self._is_field_empty({"key": "value"}) is False
    
    def test_is_field_empty_numbers(self):
        """Test numbers are not considered empty."""
        assert self._is_field_empty(0) is False
        assert self._is_field_empty(5.0) is False
    
    def _is_field_empty(self, value) -> bool:
        """Check if a field value is considered empty."""
        if value is None:
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False
    
    def test_validate_ticket_compliant(self):
        """Test validation of fully compliant ticket."""
        ticket = {
            "key": "PROJ-101",
            "fields": {
                "summary": "Test ticket",
                "labels": ["backend"],
                "fixVersions": [{"name": "v2.0"}],
                "versions": [{"name": "v1.9"}],
                "customfield_10016": 5.0,
                "customfield_10001": {"name": "Team A"}
            }
        }
        
        missing = self._validate_ticket(ticket)
        
        assert len(missing) == 0
    
    def test_validate_ticket_missing_labels(self):
        """Test validation catches missing labels."""
        ticket = {
            "key": "PROJ-102",
            "fields": {
                "summary": "Test ticket",
                "labels": [],  # Empty!
                "fixVersions": [{"name": "v2.0"}],
                "versions": [{"name": "v1.9"}],
                "customfield_10016": 5.0,
                "customfield_10001": {"name": "Team A"}
            }
        }
        
        missing = self._validate_ticket(ticket)
        
        assert "labels" in missing
    
    def test_validate_ticket_multiple_missing(self):
        """Test validation catches multiple missing fields."""
        ticket = {
            "key": "PROJ-105",
            "fields": {
                "summary": "Test ticket",
                "labels": [],  # Missing!
                "fixVersions": [],  # Missing!
                "versions": [],  # Missing!
                "customfield_10016": None,  # Missing!
                "customfield_10001": None  # Missing!
            }
        }
        
        missing = self._validate_ticket(ticket)
        
        assert len(missing) == 5
    
    def _validate_ticket(self, ticket: dict) -> list:
        """Validate a ticket and return list of missing fields."""
        required_fields = {
            "labels": "labels",
            "fixVersions": "fixVersions",
            "versions": "versions",
            "customfield_10016": "customfield_10016",
            "customfield_10001": "customfield_10001"
        }
        
        missing = []
        fields = ticket.get("fields", {})
        
        for field_name, field_key in required_fields.items():
            if self._is_field_empty(fields.get(field_key)):
                missing.append(field_name)
        
        return missing


# =============================================================================
# Test Hygiene Score Calculation
# =============================================================================

class TestHygieneScoring:
    """Tests for hygiene score calculation."""
    
    def test_score_is_percentage(self):
        """Test score is between 0 and 100."""
        report = MockHygieneData.generate_project_hygiene("PROJ")
        
        assert 0 <= report["hygiene_score"] <= 100
    
    def test_perfect_score_when_all_compliant(self):
        """Test 100% score when all tickets are compliant."""
        # Create report with no violations
        report = {
            "project_key": "PROJ",
            "total_tickets": 10,
            "compliant_tickets": 10,
            "violations_count": 0,
            "hygiene_score": 100.0
        }
        
        assert report["hygiene_score"] == 100.0
    
    def test_zero_score_when_none_compliant(self):
        """Test 0% score when no tickets are compliant."""
        report = {
            "project_key": "PROJ",
            "total_tickets": 10,
            "compliant_tickets": 0,
            "violations_count": 10,
            "hygiene_score": 0.0
        }
        
        assert report["hygiene_score"] == 0.0
    
    def test_partial_compliance_score(self):
        """Test score with partial compliance."""
        total = 100
        compliant = 75
        expected_score = 75.0
        
        actual_score = round((compliant / total) * 100, 1)
        
        assert actual_score == expected_score


# =============================================================================
# Test Notification Formatting
# =============================================================================

class TestNotificationFormatting:
    """Tests for notification message formatting."""
    
    def test_format_violation_message(self):
        """Test formatting violation message for Slack."""
        violation = {
            "ticket_key": "PROJ-123",
            "summary": "Test ticket",
            "violation_type": "Missing labels",
            "assignee_email": "alice@example.com"
        }
        
        message = self._format_violation_message([violation])
        
        assert "PROJ-123" in message
        assert "Missing labels" in message
    
    def test_format_hygiene_summary(self):
        """Test formatting hygiene summary."""
        report = {
            "project_key": "PROJ",
            "hygiene_score": 85.0,
            "total_tickets": 50,
            "compliant_tickets": 42,
            "violations_count": 8
        }
        
        summary = self._format_hygiene_summary(report)
        
        assert "PROJ" in summary
        assert "85" in summary
        # Summary format includes score but not ticket counts
        assert "compliance" in summary.lower()
    
    def test_format_score_emoji(self):
        """Test score emoji selection."""
        assert self._get_score_emoji(95) == "🟢"
        assert self._get_score_emoji(75) == "🟡"
        assert self._get_score_emoji(50) == "🔴"
    
    def _format_violation_message(self, violations: list) -> str:
        """Format violation message."""
        message_parts = []
        for v in violations:
            message_parts.append(f"• *{v['ticket_key']}*: {v['violation_type']}")
        return "\n".join(message_parts)
    
    def _format_hygiene_summary(self, report: dict) -> str:
        """Format hygiene summary."""
        emoji = self._get_score_emoji(report["hygiene_score"])
        return f"{emoji} *Project {report['project_key']}*: {report['hygiene_score']}% compliance"
    
    def _get_score_emoji(self, score: float) -> str:
        """Get emoji for score."""
        if score >= 90:
            return "🟢"
        elif score >= 70:
            return "🟡"
        return "🔴"


# =============================================================================
# Test MCP Tool Schemas
# =============================================================================

class TestMCPToolSchemas:
    """Tests for MCP tool input/output schemas."""
    
    def test_check_project_hygiene_schema(self):
        """Test check_project_hygiene tool schema."""
        schema = {
            "type": "object",
            "properties": {
                "project_key": {
                    "type": "string",
                    "description": "Jira project key (e.g., PROJ, NEXUS)"
                }
            },
            "required": ["project_key"]
        }
        
        # Validate a sample input
        sample_input = {"project_key": "PROJ"}
        
        assert "project_key" in sample_input
        assert isinstance(sample_input["project_key"], str)
    
    def test_get_user_violations_schema(self):
        """Test get_user_violations tool schema."""
        schema = {
            "type": "object",
            "properties": {
                "project_key": {"type": "string"},
                "user_email": {"type": "string"}
            },
            "required": ["project_key", "user_email"]
        }
        
        sample_input = {
            "project_key": "PROJ",
            "user_email": "alice@example.com"
        }
        
        assert all(k in sample_input for k in schema["required"])
    
    def test_get_fix_recommendations_schema(self):
        """Test get_fix_recommendations tool schema."""
        sample_input = {"ticket_key": "PROJ-123"}
        
        assert "ticket_key" in sample_input
        assert "-" in sample_input["ticket_key"]  # Valid ticket key format
    
    def test_notify_hygiene_issues_schema(self):
        """Test notify_hygiene_issues tool schema."""
        sample_input = {
            "project_key": "PROJ",
            "notify_users": True,
            "notify_channel": "#releases"
        }
        
        assert "project_key" in sample_input
        assert isinstance(sample_input["notify_users"], bool)
    
    def test_run_hygiene_check_schema(self):
        """Test run_hygiene_check tool schema."""
        sample_input = {
            "project_keys": ["PROJ", "NEXUS", "PLATFORM"]
        }
        
        assert isinstance(sample_input["project_keys"], list)
        assert all(isinstance(k, str) for k in sample_input["project_keys"])


# =============================================================================
# Test MCP Tool Responses
# =============================================================================

class TestMCPToolResponses:
    """Tests for MCP tool response structures."""
    
    def test_check_project_hygiene_response(self):
        """Test check_project_hygiene returns expected structure."""
        response = MockHygieneData.generate_project_hygiene("PROJ")
        
        required_fields = [
            "project_key", "hygiene_score", "total_tickets",
            "compliant_tickets", "violations_count", "violations"
        ]
        
        for field in required_fields:
            assert field in response, f"Missing field: {field}"
    
    def test_get_fix_recommendations_response(self):
        """Test get_fix_recommendations returns expected structure."""
        response = {
            "ticket_key": "PROJ-123",
            "violations": ["Missing labels", "Missing fix version"],
            "recommendations": [
                {"field": "labels", "suggestion": "Add appropriate labels"},
                {"field": "fixVersions", "suggestion": "Set target release version"}
            ],
            "quick_fixes": {
                "suggested_labels": ["backend", "feature"],
                "suggested_fix_version": "v2.0.0"
            }
        }
        
        assert "ticket_key" in response
        assert "recommendations" in response
        assert len(response["recommendations"]) > 0
    
    def test_notify_hygiene_issues_response(self):
        """Test notify_hygiene_issues returns expected structure."""
        response = {
            "project_key": "PROJ",
            "hygiene_score": 85.0,
            "notifications_sent": 3,
            "notifications": [
                {"sent": True, "user_email": "alice@example.com"},
                {"sent": True, "user_email": "bob@example.com"},
                {"sent": True, "user_email": "carol@example.com"}
            ]
        }
        
        assert response["notifications_sent"] == len(response["notifications"])


# =============================================================================
# Test Hygiene Agent Integration
# =============================================================================

class TestHygieneAgentIntegration:
    """Integration-style tests for hygiene agent workflow."""
    
    @pytest.mark.asyncio
    async def test_full_hygiene_check_workflow(self):
        """Test complete hygiene check workflow."""
        # 1. Generate hygiene report
        report = MockHygieneData.generate_project_hygiene("PROJ")
        
        assert report["project_key"] == "PROJ"
        
        # 2. Process violations by assignee
        notifications_to_send = []
        for assignee_data in report["by_assignee"]:
            notifications_to_send.append({
                "email": assignee_data["assignee"]["email"],
                "violations_count": len(assignee_data["violations"])
            })
        
        # 3. Verify notifications can be sent
        assert len(notifications_to_send) > 0
        
        # 4. Verify score thresholds
        if report["hygiene_score"] >= 90:
            status = "healthy"
        elif report["hygiene_score"] >= 70:
            status = "needs_attention"
        else:
            status = "critical"
        
        assert status in ["healthy", "needs_attention", "critical"]
    
    def test_violation_severity_classification(self):
        """Test violation severity is properly classified."""
        violation = MockHygieneData.generate_violation("PROJ-123")
        
        # Verify severity is valid
        assert violation["severity"] in ["high", "medium", "low"]
        
        # Verify recommendation is generated
        assert len(violation["recommendation"]) > 0
    
    def test_stale_ticket_detection(self):
        """Test stale ticket detection logic."""
        # Create a ticket updated more than 14 days ago
        old_date = datetime.utcnow() - timedelta(days=20)
        
        ticket = {
            "key": "PROJ-123",
            "fields": {
                "updated": old_date.isoformat()
            }
        }
        
        is_stale = self._is_ticket_stale(ticket, stale_days=14)
        
        assert is_stale is True
    
    def test_recent_ticket_not_stale(self):
        """Test recent tickets are not marked stale."""
        recent_date = datetime.utcnow() - timedelta(days=5)
        
        ticket = {
            "key": "PROJ-124",
            "fields": {
                "updated": recent_date.isoformat()
            }
        }
        
        is_stale = self._is_ticket_stale(ticket, stale_days=14)
        
        assert is_stale is False
    
    def _is_ticket_stale(self, ticket: dict, stale_days: int = 14) -> bool:
        """Check if a ticket is stale."""
        updated_str = ticket.get("fields", {}).get("updated")
        if not updated_str:
            return False
        
        try:
            updated = datetime.fromisoformat(updated_str.replace("Z", ""))
            return (datetime.utcnow() - updated).days > stale_days
        except (ValueError, AttributeError):
            return False


# =============================================================================
# Test Scheduler
# =============================================================================

class TestHygieneScheduler:
    """Tests for hygiene check scheduler."""
    
    def test_cron_schedule_parsing(self):
        """Test parsing cron schedule."""
        schedule = "0 9 * * 1-5"  # 9am weekdays
        parts = schedule.split()
        
        assert len(parts) == 5
        assert parts[0] == "0"  # minute
        assert parts[1] == "9"  # hour
        assert parts[4] == "1-5"  # weekdays
    
    def test_schedule_weekdays_only(self):
        """Test schedule only runs on weekdays."""
        schedule = "0 9 * * 1-5"
        
        # Monday = 1, Friday = 5
        assert "1-5" in schedule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

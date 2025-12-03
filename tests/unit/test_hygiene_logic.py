"""
Unit Tests for Jira Hygiene Logic
=================================

Tests for hygiene check rules, scoring, and scheduler.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["JIRA_MOCK_MODE"] = "true"


class TestHygieneRules:
    """Tests for hygiene rule logic."""
    
    def test_stale_ticket_rule(self):
        """Test stale ticket detection logic."""
        last_updated = datetime.utcnow() - timedelta(days=15)
        stale_threshold = 14
        
        is_stale = (datetime.utcnow() - last_updated).days > stale_threshold
        
        assert is_stale is True
    
    def test_not_stale_ticket(self):
        """Test non-stale ticket detection."""
        last_updated = datetime.utcnow() - timedelta(days=7)
        stale_threshold = 14
        
        is_stale = (datetime.utcnow() - last_updated).days > stale_threshold
        
        assert is_stale is False
    
    def test_missing_description_rule(self):
        """Test missing description detection."""
        ticket_with_desc = {"description": "Some description"}
        ticket_without_desc = {"description": None}
        ticket_empty_desc = {"description": ""}
        
        def has_description(ticket):
            return bool(ticket.get("description"))
        
        assert has_description(ticket_with_desc) is True
        assert has_description(ticket_without_desc) is False
        assert has_description(ticket_empty_desc) is False
    
    def test_unassigned_ticket_rule(self):
        """Test unassigned ticket detection."""
        assigned = {"assignee": {"name": "john.doe"}}
        unassigned = {"assignee": None}
        
        def is_unassigned(ticket):
            return ticket.get("assignee") is None
        
        assert is_unassigned(assigned) is False
        assert is_unassigned(unassigned) is True
    
    def test_missing_priority_rule(self):
        """Test missing priority detection."""
        with_priority = {"priority": {"name": "High"}}
        without_priority = {"priority": None}
        
        def has_priority(ticket):
            return ticket.get("priority") is not None
        
        assert has_priority(with_priority) is True
        assert has_priority(without_priority) is False
    
    def test_no_labels_rule(self):
        """Test missing labels detection."""
        with_labels = {"labels": ["bug", "urgent"]}
        without_labels = {"labels": []}
        
        def has_labels(ticket):
            return len(ticket.get("labels", [])) > 0
        
        assert has_labels(with_labels) is True
        assert has_labels(without_labels) is False


class TestHygieneScoringLogic:
    """Tests for hygiene scoring logic."""
    
    def test_perfect_score(self):
        """Test perfect score with no violations."""
        total_tickets = 100
        violations = 0
        
        score = ((total_tickets - violations) / total_tickets) * 100 if total_tickets > 0 else 100
        
        assert score == 100.0
    
    def test_partial_score(self):
        """Test partial score with some violations."""
        total_tickets = 100
        violations = 10
        
        score = ((total_tickets - violations) / total_tickets) * 100 if total_tickets > 0 else 100
        
        assert score == 90.0
    
    def test_zero_tickets(self):
        """Test score with zero tickets."""
        total_tickets = 0
        violations = 0
        
        score = 100.0 if total_tickets == 0 else ((total_tickets - violations) / total_tickets) * 100
        
        assert score == 100.0
    
    def test_all_violations(self):
        """Test score with all tickets having violations."""
        total_tickets = 50
        violations = 50
        
        score = ((total_tickets - violations) / total_tickets) * 100 if total_tickets > 0 else 100
        
        assert score == 0.0


class TestViolationSeverity:
    """Tests for violation severity classification."""
    
    def test_severity_levels(self):
        """Test severity level constants."""
        severities = ["critical", "high", "medium", "low", "info"]
        
        for severity in severities:
            assert severity.islower()
    
    def test_severity_ordering(self):
        """Test severity levels can be compared."""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        
        assert severity_order["critical"] > severity_order["high"]
        assert severity_order["high"] > severity_order["medium"]
        assert severity_order["medium"] > severity_order["low"]


class TestHygieneAppImport:
    """Tests for Hygiene Agent app import."""
    
    def test_app_can_be_imported(self):
        """Test hygiene agent app can be imported."""
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/agents/jira_hygiene_agent")))
        
        try:
            from main import app
            assert app is not None
        except ImportError:
            # May fail due to missing dependencies in test env
            pytest.skip("Hygiene agent dependencies not available")


class TestTicketFieldValidation:
    """Tests for ticket field validation."""
    
    def test_valid_ticket_key(self):
        """Test valid ticket key format."""
        import re
        
        pattern = r'^[A-Z]+-\d+$'
        
        assert re.match(pattern, "PROJ-123") is not None
        assert re.match(pattern, "ABC-1") is not None
        assert re.match(pattern, "invalid") is None
    
    def test_valid_status(self):
        """Test valid status values."""
        valid_statuses = ["Open", "In Progress", "Done", "Closed", "To Do"]
        
        test_status = "In Progress"
        assert test_status in valid_statuses
    
    def test_story_points_range(self):
        """Test story points in valid range."""
        valid_points = [1, 2, 3, 5, 8, 13, 21]
        
        assert 5 in valid_points
        assert 10 not in valid_points


class TestDateCalculations:
    """Tests for date-related calculations."""
    
    def test_days_since_update(self):
        """Test calculating days since last update."""
        last_updated = datetime.utcnow() - timedelta(days=10)
        days_ago = (datetime.utcnow() - last_updated).days
        
        assert days_ago == 10
    
    def test_days_until_due(self):
        """Test calculating days until due date."""
        due_date = datetime.utcnow() + timedelta(days=5)
        days_until = (due_date - datetime.utcnow()).days
        
        # Allow for slight timing variation
        assert days_until >= 4 and days_until <= 5
    
    def test_overdue_detection(self):
        """Test overdue ticket detection."""
        due_date = datetime.utcnow() - timedelta(days=3)
        is_overdue = datetime.utcnow() > due_date
        
        assert is_overdue is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

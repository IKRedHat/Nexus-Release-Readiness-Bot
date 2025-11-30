"""
Unit Tests for Jira Hygiene Agent Logic
Tests validation rules and scoring against mock Jira ticket data
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath("services/agents/jira_hygiene_agent"))
sys.path.insert(0, os.path.abspath("shared"))

# Set mock mode before imports
os.environ["JIRA_MOCK_MODE"] = "true"
os.environ["NEXUS_REQUIRE_AUTH"] = "false"


class TestHygieneConfig:
    """Tests for HygieneConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        from main import HygieneConfig
        
        config = HygieneConfig()
        
        assert "labels" in config.required_fields
        assert "fixVersions" in config.required_fields
        assert "versions" in config.required_fields
        assert config.schedule_hour == 9
        assert config.schedule_minute == 0
        assert config.schedule_days == "mon-fri"
        assert config.timezone == "UTC"
    
    def test_custom_config(self):
        """Test custom configuration"""
        from main import HygieneConfig
        
        config = HygieneConfig(
            projects=["PROJ", "TEST"],
            schedule_hour=14,
            schedule_days="daily",
            timezone="America/New_York"
        )
        
        assert config.projects == ["PROJ", "TEST"]
        assert config.schedule_hour == 14
        assert config.schedule_days == "daily"
        assert config.timezone == "America/New_York"
    
    def test_field_names_mapping(self):
        """Test human-readable field names"""
        from main import HygieneConfig
        
        config = HygieneConfig()
        
        assert config.field_names["labels"] == "Labels"
        assert config.field_names["fixVersions"] == "Fix Version"
        assert config.field_names["versions"] == "Affected Version"
        assert config.field_names["customfield_10016"] == "Story Points"


class TestJiraHygieneClient:
    """Tests for JiraHygieneClient"""
    
    @pytest.fixture
    def client(self):
        """Create client instance"""
        from main import JiraHygieneClient, HygieneConfig
        return JiraHygieneClient(HygieneConfig())
    
    def test_mock_mode_enabled(self, client):
        """Test client is in mock mode"""
        assert client.mock_mode is True
    
    def test_get_mock_tickets(self, client):
        """Test mock ticket generation"""
        tickets = client.get_active_sprint_tickets("PROJ")
        
        assert len(tickets) > 0
        assert all("key" in t for t in tickets)
        assert all("fields" in t for t in tickets)
    
    def test_mock_tickets_have_required_structure(self, client):
        """Test mock tickets have proper structure"""
        tickets = client.get_active_sprint_tickets("TEST")
        
        for ticket in tickets:
            fields = ticket["fields"]
            assert "summary" in fields
            assert "status" in fields
            assert "issuetype" in fields


class TestHygieneChecker:
    """Tests for HygieneChecker validation logic"""
    
    @pytest.fixture
    def checker(self):
        """Create checker instance"""
        from main import HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        
        return HygieneChecker(jira_client, slack_client, config)
    
    def test_is_field_empty_none(self, checker):
        """Test None is considered empty"""
        assert checker._is_field_empty(None) is True
    
    def test_is_field_empty_list(self, checker):
        """Test empty list is considered empty"""
        assert checker._is_field_empty([]) is True
        assert checker._is_field_empty(["value"]) is False
    
    def test_is_field_empty_string(self, checker):
        """Test empty string is considered empty"""
        assert checker._is_field_empty("") is True
        assert checker._is_field_empty("   ") is True
        assert checker._is_field_empty("value") is False
    
    def test_is_field_empty_dict(self, checker):
        """Test empty dict is considered empty"""
        assert checker._is_field_empty({}) is True
        assert checker._is_field_empty({"key": "value"}) is False
    
    def test_is_field_empty_numbers(self, checker):
        """Test numbers are not considered empty"""
        assert checker._is_field_empty(0) is False
        assert checker._is_field_empty(5.0) is False
    
    def test_validate_ticket_compliant(self, checker):
        """Test validation of fully compliant ticket"""
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
        
        missing = checker._validate_ticket(ticket)
        
        assert len(missing) == 0
    
    def test_validate_ticket_missing_labels(self, checker):
        """Test validation catches missing labels"""
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
        
        missing = checker._validate_ticket(ticket)
        
        assert "Labels" in missing
        assert len(missing) == 1
    
    def test_validate_ticket_missing_fix_version(self, checker):
        """Test validation catches missing fix version"""
        ticket = {
            "key": "PROJ-103",
            "fields": {
                "summary": "Test ticket",
                "labels": ["api"],
                "fixVersions": [],  # Empty!
                "versions": [{"name": "v1.9"}],
                "customfield_10016": 5.0,
                "customfield_10001": {"name": "Team A"}
            }
        }
        
        missing = checker._validate_ticket(ticket)
        
        assert "Fix Version" in missing
    
    def test_validate_ticket_missing_story_points(self, checker):
        """Test validation catches missing story points"""
        ticket = {
            "key": "PROJ-104",
            "fields": {
                "summary": "Test ticket",
                "labels": ["api"],
                "fixVersions": [{"name": "v2.0"}],
                "versions": [{"name": "v1.9"}],
                "customfield_10016": None,  # Missing!
                "customfield_10001": {"name": "Team A"}
            }
        }
        
        missing = checker._validate_ticket(ticket)
        
        assert "Story Points" in missing
    
    def test_validate_ticket_multiple_missing(self, checker):
        """Test validation catches multiple missing fields"""
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
        
        missing = checker._validate_ticket(ticket)
        
        assert len(missing) == 5
        assert "Labels" in missing
        assert "Fix Version" in missing
        assert "Affected Version" in missing
        assert "Story Points" in missing
        assert "Team/Contributors" in missing
    
    def test_get_assignee_info_assigned(self, checker):
        """Test extracting assigned user info"""
        ticket = {
            "fields": {
                "assignee": {
                    "emailAddress": "alice@example.com",
                    "displayName": "Alice Developer"
                }
            }
        }
        
        email, name = checker._get_assignee_info(ticket)
        
        assert email == "alice@example.com"
        assert name == "Alice Developer"
    
    def test_get_assignee_info_unassigned(self, checker):
        """Test handling unassigned tickets"""
        ticket = {
            "fields": {
                "assignee": None
            }
        }
        
        email, name = checker._get_assignee_info(ticket)
        
        assert email == "unassigned@example.com"
        assert name == "Unassigned"
    
    def test_build_ticket_url(self, checker):
        """Test ticket URL generation"""
        url = checker._build_ticket_url("PROJ-123")
        
        assert "PROJ-123" in url
        assert url.startswith("http")
    
    @pytest.mark.asyncio
    async def test_check_hygiene_calculates_score(self, checker):
        """Test hygiene check calculates score correctly"""
        result = await checker.check_hygiene(project_key="PROJ")
        
        assert result.total_tickets_checked > 0
        assert 0 <= result.hygiene_score <= 100
        assert result.compliant_tickets + result.non_compliant_tickets == result.total_tickets_checked
    
    @pytest.mark.asyncio
    async def test_check_hygiene_groups_by_assignee(self, checker):
        """Test violations are grouped by assignee"""
        result = await checker.check_hygiene(project_key="PROJ")
        
        # Check that violations are grouped
        for assignee in result.violations_by_assignee:
            assert assignee.assignee_email is not None
            assert len(assignee.violations) > 0
            assert all(v.assignee_email == assignee.assignee_email for v in assignee.violations)
    
    @pytest.mark.asyncio
    async def test_check_hygiene_tracks_violation_types(self, checker):
        """Test violation summary tracks field types"""
        result = await checker.check_hygiene(project_key="PROJ")
        
        # Mock data should have violations
        if result.non_compliant_tickets > 0:
            assert len(result.violation_summary) > 0
            # All values should be positive integers
            assert all(v > 0 for v in result.violation_summary.values())


class TestHygieneCheckResult:
    """Tests for HygieneCheckResult model"""
    
    def test_create_result(self):
        """Test creating a hygiene check result"""
        from main import HygieneCheckResult, AssigneeViolations, TicketViolation
        
        result = HygieneCheckResult(
            check_id="test-123",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=10,
            compliant_tickets=7,
            non_compliant_tickets=3,
            hygiene_score=70.0,
            violations_by_assignee=[],
            violation_summary={"Labels": 2, "Story Points": 1}
        )
        
        assert result.check_id == "test-123"
        assert result.hygiene_score == 70.0
        assert result.total_tickets_checked == 10


class TestHygieneScoring:
    """Tests for hygiene score calculation"""
    
    @pytest.fixture
    def checker(self):
        """Create checker with mock data"""
        from main import HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        
        return HygieneChecker(jira_client, slack_client, config)
    
    @pytest.mark.asyncio
    async def test_score_is_percentage(self, checker):
        """Test score is between 0 and 100"""
        result = await checker.check_hygiene()
        
        assert 0 <= result.hygiene_score <= 100
    
    @pytest.mark.asyncio
    async def test_score_calculation(self, checker):
        """Test score is correctly calculated"""
        result = await checker.check_hygiene()
        
        expected_score = (result.compliant_tickets / result.total_tickets_checked * 100)
        assert abs(result.hygiene_score - expected_score) < 0.1
    
    @pytest.mark.asyncio
    async def test_empty_project_has_full_score(self):
        """Test empty project gets 100% score"""
        from main import HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = MagicMock()
        jira_client.mock_mode = True
        jira_client.jira_url = "https://jira.example.com"
        jira_client.get_active_sprint_tickets = MagicMock(return_value=[])
        
        slack_client = AsyncMock(spec=AsyncHttpClient)
        checker = HygieneChecker(jira_client, slack_client, config)
        
        result = await checker.check_hygiene()
        
        assert result.hygiene_score == 100.0
        assert result.total_tickets_checked == 0


class TestNotificationFormatting:
    """Tests for notification message formatting"""
    
    @pytest.fixture
    def checker(self):
        """Create checker instance"""
        from main import HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        
        return HygieneChecker(jira_client, slack_client, config)
    
    def test_format_message_has_blocks(self, checker):
        """Test formatted message includes Block Kit blocks"""
        from main import AssigneeViolations, TicketViolation, HygieneCheckResult
        
        assignee = AssigneeViolations(
            assignee_email="test@example.com",
            assignee_display_name="Test User",
            violations=[
                TicketViolation(
                    ticket_key="PROJ-123",
                    ticket_summary="Test ticket",
                    ticket_url="https://jira.example.com/browse/PROJ-123",
                    missing_fields=["Labels", "Story Points"]
                )
            ],
            total_violations=2
        )
        
        result = HygieneCheckResult(
            check_id="test-123",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=10,
            compliant_tickets=7,
            non_compliant_tickets=3,
            hygiene_score=70.0,
            violations_by_assignee=[assignee],
            violation_summary={"Labels": 1, "Story Points": 1}
        )
        
        message = checker._format_violation_message(assignee, result)
        
        assert "text" in message
        assert "blocks" in message
        assert len(message["blocks"]) > 0
    
    def test_format_message_includes_score(self, checker):
        """Test message includes hygiene score"""
        from main import AssigneeViolations, TicketViolation, HygieneCheckResult
        
        assignee = AssigneeViolations(
            assignee_email="test@example.com",
            assignee_display_name="Test User",
            violations=[
                TicketViolation(
                    ticket_key="PROJ-123",
                    ticket_summary="Test ticket",
                    ticket_url="https://jira.example.com/browse/PROJ-123",
                    missing_fields=["Labels"]
                )
            ],
            total_violations=1
        )
        
        result = HygieneCheckResult(
            check_id="test-123",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=10,
            compliant_tickets=7,
            non_compliant_tickets=3,
            hygiene_score=70.0,
            violations_by_assignee=[assignee],
            violation_summary={"Labels": 1}
        )
        
        message = checker._format_violation_message(assignee, result)
        
        # Score should be in the text
        assert "70" in str(message)


class TestScheduler:
    """Tests for HygieneScheduler"""
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes correctly"""
        from main import HygieneScheduler, HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        checker = HygieneChecker(jira_client, slack_client, config)
        
        scheduler = HygieneScheduler(checker, config)
        
        assert scheduler.scheduler is not None
        assert not scheduler.scheduler.running
    
    def test_scheduler_job_registered(self):
        """Test hygiene check job is registered"""
        from main import HygieneScheduler, HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        checker = HygieneChecker(jira_client, slack_client, config)
        
        scheduler = HygieneScheduler(checker, config)
        
        job = scheduler.scheduler.get_job("hygiene_check")
        assert job is not None
        assert job.name == "Scheduled Hygiene Check"


class TestInteractiveNotification:
    """Tests for interactive notification messages with modal buttons"""
    
    @pytest.fixture
    def checker(self):
        """Create checker instance"""
        from main import HygieneChecker, JiraHygieneClient, HygieneConfig
        from nexus_lib.utils import AsyncHttpClient
        
        config = HygieneConfig()
        jira_client = JiraHygieneClient(config)
        slack_client = AsyncMock(spec=AsyncHttpClient)
        
        return HygieneChecker(jira_client, slack_client, config)
    
    def test_notification_includes_fix_button(self, checker):
        """Test notification message includes interactive fix button"""
        import json
        from main import AssigneeViolations, TicketViolation, HygieneCheckResult
        
        assignee = AssigneeViolations(
            assignee_email="test@example.com",
            assignee_display_name="Test User",
            violations=[
                TicketViolation(
                    ticket_key="PROJ-123",
                    ticket_summary="Test ticket with violations",
                    ticket_url="https://jira.example.com/browse/PROJ-123",
                    missing_fields=["Labels", "Story Points"]
                )
            ],
            total_violations=2
        )
        
        result = HygieneCheckResult(
            check_id="test-123",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=10,
            compliant_tickets=7,
            non_compliant_tickets=3,
            hygiene_score=70.0,
            violations_by_assignee=[assignee],
            violation_summary={"Labels": 1, "Story Points": 1}
        )
        
        message = checker._format_violation_message(assignee, result)
        
        # Check for actions block with fix button
        actions_block = None
        for block in message["blocks"]:
            if block.get("type") == "actions":
                actions_block = block
                break
        
        assert actions_block is not None, "Message should have an actions block"
        
        # Find the fix button
        fix_button = None
        for element in actions_block.get("elements", []):
            if element.get("action_id") == "open_hygiene_fix_modal":
                fix_button = element
                break
        
        assert fix_button is not None, "Message should have a fix button"
        assert fix_button.get("style") == "primary"
    
    def test_notification_button_contains_violation_data(self, checker):
        """Test fix button value contains violation data for modal"""
        import json
        from main import AssigneeViolations, TicketViolation, HygieneCheckResult
        
        assignee = AssigneeViolations(
            assignee_email="test@example.com",
            assignee_display_name="Test User",
            violations=[
                TicketViolation(
                    ticket_key="PROJ-456",
                    ticket_summary="Another test ticket",
                    ticket_url="https://jira.example.com/browse/PROJ-456",
                    missing_fields=["Fix Version"]
                )
            ],
            total_violations=1
        )
        
        result = HygieneCheckResult(
            check_id="test-456",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=5,
            compliant_tickets=4,
            non_compliant_tickets=1,
            hygiene_score=80.0,
            violations_by_assignee=[assignee],
            violation_summary={"Fix Version": 1}
        )
        
        message = checker._format_violation_message(assignee, result)
        
        # Find the fix button and parse its value
        fix_button = None
        for block in message["blocks"]:
            if block.get("type") == "actions":
                for element in block.get("elements", []):
                    if element.get("action_id") == "open_hygiene_fix_modal":
                        fix_button = element
                        break
        
        assert fix_button is not None
        
        # Parse the button value (JSON payload)
        violation_payload = json.loads(fix_button.get("value", "{}"))
        
        assert "check_id" in violation_payload
        assert "tickets" in violation_payload
        assert len(violation_payload["tickets"]) == 1
        assert violation_payload["tickets"][0]["key"] == "PROJ-456"
        assert "Fix Version" in violation_payload["tickets"][0]["missing_fields"]
    
    def test_notification_includes_snooze_button(self, checker):
        """Test notification includes snooze reminder button"""
        import json
        from main import AssigneeViolations, TicketViolation, HygieneCheckResult
        
        assignee = AssigneeViolations(
            assignee_email="test@example.com",
            assignee_display_name="Test User",
            violations=[
                TicketViolation(
                    ticket_key="PROJ-789",
                    ticket_summary="Test ticket",
                    ticket_url="https://jira.example.com/browse/PROJ-789",
                    missing_fields=["Labels"]
                )
            ],
            total_violations=1
        )
        
        result = HygieneCheckResult(
            check_id="test-789",
            timestamp=datetime.utcnow(),
            project_key="PROJ",
            total_tickets_checked=10,
            compliant_tickets=9,
            non_compliant_tickets=1,
            hygiene_score=90.0,
            violations_by_assignee=[assignee],
            violation_summary={"Labels": 1}
        )
        
        message = checker._format_violation_message(assignee, result)
        
        # Find snooze button
        snooze_button = None
        for block in message["blocks"]:
            if block.get("type") == "actions":
                for element in block.get("elements", []):
                    if element.get("action_id") == "snooze_hygiene_reminder":
                        snooze_button = element
                        break
        
        assert snooze_button is not None, "Message should have a snooze button"
        
        # Parse snooze button value
        snooze_data = json.loads(snooze_button.get("value", "{}"))
        assert snooze_data.get("check_id") == "test-789"
        assert snooze_data.get("assignee_email") == "test@example.com"


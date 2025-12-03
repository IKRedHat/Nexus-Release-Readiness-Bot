"""
Comprehensive Unit Tests for Slack Agent
=========================================

Tests for SlackClient, BlockKitBuilder, Modals, and API endpoints.

Coverage:
- SlackClient initialization and operations
- BlockKitBuilder helper methods
- Modal building functions
- Hygiene fix modal handling
- API endpoint validation
- Error handling

Usage:
    pytest tests/unit/test_slack_agent.py -v
"""

import pytest
import sys
import os
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/agents/slack_agent")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"


# =============================================================================
# SlackClient Tests
# =============================================================================

class TestSlackClientInitialization:
    """Tests for SlackClient initialization."""
    
    def test_client_created_uninitialized(self):
        """Test client is created in uninitialized state."""
        from main import SlackClient
        
        client = SlackClient()
        
        assert client._last_mode is None
        assert client._bot_token is None
        assert client._initialized is False
    
    def test_mock_mode_property_default(self):
        """Test mock_mode property returns True by default."""
        from main import SlackClient
        
        client = SlackClient()
        
        assert client.mock_mode is True


class TestSlackClientOperations:
    """Tests for SlackClient operations."""
    
    @pytest.fixture
    def client(self):
        from main import SlackClient
        c = SlackClient()
        c._last_mode = True  # Force mock mode
        c._initialized = True
        return c
    
    @pytest.mark.asyncio
    async def test_post_message_mock_mode(self, client):
        """Test post_message in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.post_message(
                channel="#release",
                text="Test message"
            )
        
        assert result["ok"] is True
        assert result["ts"] == "mock.ts"
        assert result["channel"] == "#release"
    
    @pytest.mark.asyncio
    async def test_post_message_with_blocks(self, client):
        """Test post_message with Block Kit blocks."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.post_message(
                channel="#release",
                text="Test message",
                blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]
            )
        
        assert result["ok"] is True
    
    @pytest.mark.asyncio
    async def test_post_message_in_thread(self, client):
        """Test post_message in thread."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.post_message(
                channel="#release",
                text="Reply message",
                thread_ts="parent.ts"
            )
        
        assert result["ok"] is True
    
    @pytest.mark.asyncio
    async def test_update_message_mock_mode(self, client):
        """Test update_message in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.update_message(
                channel="#release",
                ts="message.ts",
                text="Updated message"
            )
        
        assert result["ok"] is True
        assert result["ts"] == "message.ts"
    
    @pytest.mark.asyncio
    async def test_open_modal_mock_mode(self, client):
        """Test open_modal in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.open_modal(
                trigger_id="trigger-123",
                view={"type": "modal", "title": {"type": "plain_text", "text": "Test"}}
            )
        
        assert result["ok"] is True
        assert result["view"]["id"] == "mock-view-id"
    
    @pytest.mark.asyncio
    async def test_update_modal_mock_mode(self, client):
        """Test update_modal in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.update_modal(
                view_id="view-123",
                view={"type": "modal", "title": {"type": "plain_text", "text": "Updated"}}
            )
        
        assert result["ok"] is True
        assert result["view"]["id"] == "view-123"
    
    @pytest.mark.asyncio
    async def test_respond_to_slash_command_mock_mode(self, client):
        """Test respond_to_slash_command in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.respond_to_slash_command(
                response_url="https://hooks.slack.com/response",
                text="Processing..."
            )
        
        assert result["ok"] is True
    
    @pytest.mark.asyncio
    async def test_lookup_user_by_email_mock_mode(self, client):
        """Test lookup_user_by_email in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            user_id = await client.lookup_user_by_email("test@example.com")
        
        assert user_id == "U_MOCK_TEST"
    
    @pytest.mark.asyncio
    async def test_open_dm_channel_mock_mode(self, client):
        """Test open_dm_channel in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            channel_id = await client.open_dm_channel("U123")
        
        assert channel_id == "D_MOCK_U123"
    
    @pytest.mark.asyncio
    async def test_send_dm_mock_mode(self, client):
        """Test send_dm in mock mode."""
        with patch.object(client, '_ensure_initialized', new=AsyncMock()):
            result = await client.send_dm(
                email="test@example.com",
                text="Hello!"
            )
        
        assert result["ok"] is True


# =============================================================================
# BlockKitBuilder Tests
# =============================================================================

class TestBlockKitBuilder:
    """Tests for BlockKitBuilder helper class."""
    
    def test_header_block(self):
        """Test header block creation."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.header("Test Header")
        
        assert block["type"] == "header"
        assert block["text"]["type"] == "plain_text"
        assert block["text"]["text"] == "Test Header"
        assert block["text"]["emoji"] is True
    
    def test_section_block(self):
        """Test section block creation."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.section("*Bold text* and _italic_")
        
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
        assert "*Bold text*" in block["text"]["text"]
    
    def test_section_block_with_accessory(self):
        """Test section block with accessory."""
        from main import BlockKitBuilder
        
        accessory = {"type": "button", "text": {"type": "plain_text", "text": "Click"}}
        block = BlockKitBuilder.section("Some text", accessory=accessory)
        
        assert block["accessory"] == accessory
    
    def test_divider_block(self):
        """Test divider block creation."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.divider()
        
        assert block["type"] == "divider"
    
    def test_context_block(self):
        """Test context block creation."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.context(["Element 1", "Element 2"])
        
        assert block["type"] == "context"
        assert len(block["elements"]) == 2
        assert block["elements"][0]["type"] == "mrkdwn"
    
    def test_actions_block(self):
        """Test actions block creation."""
        from main import BlockKitBuilder
        
        elements = [{"type": "button", "text": {"type": "plain_text", "text": "Button"}}]
        block = BlockKitBuilder.actions(elements)
        
        assert block["type"] == "actions"
        assert block["elements"] == elements
    
    def test_button_element(self):
        """Test button element creation."""
        from main import BlockKitBuilder
        
        btn = BlockKitBuilder.button("Click Me", "btn_action", "click_value")
        
        assert btn["type"] == "button"
        assert btn["text"]["text"] == "Click Me"
        assert btn["action_id"] == "btn_action"
        assert btn["value"] == "click_value"
    
    def test_button_with_style(self):
        """Test button with style."""
        from main import BlockKitBuilder
        
        btn = BlockKitBuilder.button("Danger", "danger_action", style="danger")
        
        assert btn["style"] == "danger"
    
    def test_input_block(self):
        """Test input block creation."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.input_block(
            label="Enter text",
            block_id="input_block",
            action_id="input_action",
            placeholder="Type here..."
        )
        
        assert block["type"] == "input"
        assert block["block_id"] == "input_block"
        assert block["element"]["action_id"] == "input_action"
        assert block["label"]["text"] == "Enter text"
    
    def test_input_block_optional(self):
        """Test optional input block."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.input_block(
            label="Optional",
            block_id="opt_block",
            action_id="opt_action",
            optional=True
        )
        
        assert block["optional"] is True
    
    def test_input_block_multiline(self):
        """Test multiline input block."""
        from main import BlockKitBuilder
        
        block = BlockKitBuilder.input_block(
            label="Description",
            block_id="desc_block",
            action_id="desc_action",
            multiline=True
        )
        
        assert block["element"]["multiline"] is True
    
    def test_select_block(self):
        """Test select block creation."""
        from main import BlockKitBuilder
        
        options = [
            {"text": "Option 1", "value": "opt1"},
            {"text": "Option 2", "value": "opt2"}
        ]
        block = BlockKitBuilder.select_block(
            label="Choose",
            block_id="select_block",
            action_id="select_action",
            options=options
        )
        
        assert block["type"] == "input"
        assert block["element"]["type"] == "static_select"
        assert len(block["element"]["options"]) == 2
    
    def test_status_message_success(self):
        """Test status message for success."""
        from main import BlockKitBuilder
        
        blocks = BlockKitBuilder.status_message(
            title="Release Ready",
            status="success",
            details=["All tests passed", "No blockers"],
            decision="GO"
        )
        
        assert len(blocks) >= 4  # Header, divider, details, decision
        assert blocks[0]["type"] == "header"
        assert "✅" in blocks[0]["text"]["text"]
    
    def test_status_message_failure(self):
        """Test status message for failure."""
        from main import BlockKitBuilder
        
        blocks = BlockKitBuilder.status_message(
            title="Build Failed",
            status="failure",
            details=["Tests failed", "Blockers found"]
        )
        
        assert "❌" in blocks[0]["text"]["text"]
    
    def test_status_message_pending(self):
        """Test status message for pending."""
        from main import BlockKitBuilder
        
        blocks = BlockKitBuilder.status_message(
            title="Build Running",
            status="pending",
            details=["Running tests..."]
        )
        
        assert "⏳" in blocks[0]["text"]["text"]


# =============================================================================
# Modal Builder Tests
# =============================================================================

class TestModalBuilders:
    """Tests for modal building functions."""
    
    def test_build_jira_update_modal(self):
        """Test Jira update modal structure."""
        from main import build_jira_update_modal
        
        modal = build_jira_update_modal()
        
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "jira_update_submission"
        assert modal["title"]["text"] == "Update Jira Ticket"
        assert modal["submit"]["text"] == "Update"
        assert len(modal["blocks"]) >= 3  # ticket_key, status, comment
    
    def test_build_release_check_modal(self):
        """Test release check modal structure."""
        from main import build_release_check_modal
        
        modal = build_release_check_modal()
        
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "release_check_submission"
        assert modal["title"]["text"] == "Release Readiness Check"
        assert len(modal["blocks"]) >= 5  # section, divider, version, epic, repo, env
    
    def test_build_report_modal(self):
        """Test report generation modal structure."""
        from main import build_report_modal
        
        modal = build_report_modal()
        
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "report_submission"
        assert modal["title"]["text"] == "Generate Report"
        assert len(modal["blocks"]) >= 3  # type, version, page_id


# =============================================================================
# Hygiene Fix Modal Tests
# =============================================================================

class TestHygieneFixModal:
    """Tests for hygiene fix modal functions."""
    
    @pytest.mark.asyncio
    async def test_build_hygiene_fix_modal_with_data(self):
        """Test building hygiene fix modal with violation data."""
        from main import build_hygiene_fix_modal
        
        violation_data = {
            "check_id": "hygiene-123",
            "tickets": [
                {
                    "key": "NEXUS-101",
                    "summary": "Test ticket",
                    "missing_fields": ["Labels", "Fix Version"]
                }
            ]
        }
        
        modal = await build_hygiene_fix_modal(json.dumps(violation_data))
        
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "hygiene_fix_submission"
        assert modal["private_metadata"] == json.dumps(violation_data)
    
    @pytest.mark.asyncio
    async def test_build_hygiene_fix_modal_empty_data(self):
        """Test building hygiene fix modal with empty data."""
        from main import build_hygiene_fix_modal
        
        modal = await build_hygiene_fix_modal("{}")
        
        assert modal["type"] == "modal"
        assert "blocks" in modal
    
    @pytest.mark.asyncio
    async def test_build_hygiene_fix_modal_invalid_json(self):
        """Test building hygiene fix modal with invalid JSON."""
        from main import build_hygiene_fix_modal
        
        modal = await build_hygiene_fix_modal("not valid json")
        
        # Should handle gracefully
        assert modal["type"] == "modal"
    
    @pytest.mark.asyncio
    async def test_build_hygiene_fix_modal_multiple_missing_fields(self):
        """Test modal with multiple missing fields."""
        from main import build_hygiene_fix_modal
        
        violation_data = {
            "tickets": [
                {
                    "key": "NEXUS-102",
                    "summary": "Ticket with many issues",
                    "missing_fields": ["Labels", "Fix Version", "Affected Version", "Story Points", "Team/Contributors"]
                }
            ]
        }
        
        modal = await build_hygiene_fix_modal(json.dumps(violation_data))
        
        # Should have input blocks for each missing field
        input_blocks = [b for b in modal["blocks"] if b.get("type") == "input"]
        assert len(input_blocks) >= 5
    
    @pytest.mark.asyncio
    async def test_build_hygiene_fix_modal_limit_tickets(self):
        """Test modal limits to 5 tickets."""
        from main import build_hygiene_fix_modal
        
        violation_data = {
            "tickets": [
                {"key": f"NEXUS-{i}", "summary": f"Ticket {i}", "missing_fields": ["Labels"]}
                for i in range(10)
            ]
        }
        
        modal = await build_hygiene_fix_modal(json.dumps(violation_data))
        
        # Should only process 5 tickets max
        header_count = sum(1 for b in modal["blocks"] if "*NEXUS-" in str(b))
        assert header_count <= 5


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestSlackAgentAPI:
    """Tests for Slack Agent API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            # Mock app_home import to avoid import errors
            with patch.dict('sys.modules', {'app_home': MagicMock()}):
                from main import app
                with TestClient(app) as client:
                    yield client
        except ImportError as e:
            pytest.skip(f"Slack agent module not available: {e}")
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "slack-agent"
    
    def test_execute_notify(self, client):
        """Test POST /execute with notify action."""
        response = client.post("/execute", json={
            "task_id": "test-1",
            "action": "notify",
            "payload": {
                "channel": "#release",
                "message": "Test notification"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_execute_send_dm(self, client):
        """Test POST /execute with send_dm action."""
        response = client.post("/execute", json={
            "task_id": "test-2",
            "action": "send_dm",
            "payload": {
                "email": "test@example.com",
                "message": "Test DM"
            }
        })
        
        assert response.status_code == 200
    
    def test_execute_unknown_action(self, client):
        """Test POST /execute with unknown action."""
        response = client.post("/execute", json={
            "task_id": "test-3",
            "action": "unknown_action",
            "payload": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
    
    def test_send_dm_endpoint(self, client):
        """Test POST /send-dm endpoint."""
        response = client.post("/send-dm", json={
            "email": "test@example.com",
            "message": "Test message"
        })
        
        assert response.status_code == 200
    
    def test_send_dm_with_blocks(self, client):
        """Test send-dm with blocks."""
        response = client.post("/send-dm", json={
            "email": "test@example.com",
            "message": "Test message",
            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]
        })
        
        assert response.status_code == 200


# =============================================================================
# Slash Command Tests
# =============================================================================

class TestSlashCommands:
    """Tests for slash command handling."""
    
    @pytest.fixture
    def client(self):
        try:
            with patch.dict('sys.modules', {'app_home': MagicMock()}):
                from main import app
                with TestClient(app) as client:
                    yield client
        except ImportError as e:
            pytest.skip(f"Slack agent module not available: {e}")
    
    def test_nexus_help_command(self, client):
        """Test /nexus help command."""
        response = client.post("/slack/commands", data={
            "command": "/nexus",
            "text": "help",
            "user_id": "U123",
            "user_name": "testuser",
            "channel_id": "C123",
            "team_id": "T123",
            "trigger_id": "trigger-123",
            "response_url": "https://hooks.slack.com/response"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "blocks" in data
    
    def test_nexus_empty_command(self, client):
        """Test /nexus with empty text."""
        response = client.post("/slack/commands", data={
            "command": "/nexus",
            "text": "",
            "user_id": "U123",
            "user_name": "testuser",
            "channel_id": "C123",
            "team_id": "T123",
            "trigger_id": "trigger-123",
            "response_url": "https://hooks.slack.com/response"
        })
        
        assert response.status_code == 200


# =============================================================================
# Event Handling Tests
# =============================================================================

class TestEventHandling:
    """Tests for Slack Events API handling."""
    
    @pytest.fixture
    def client(self):
        try:
            with patch.dict('sys.modules', {'app_home': MagicMock()}):
                from main import app
                with TestClient(app) as client:
                    yield client
        except ImportError as e:
            pytest.skip(f"Slack agent module not available: {e}")
    
    def test_url_verification(self, client):
        """Test URL verification challenge."""
        response = client.post("/slack/events", json={
            "type": "url_verification",
            "challenge": "test-challenge-123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test-challenge-123"
    
    def test_app_mention_event(self, client):
        """Test app_mention event."""
        response = client.post("/slack/events", json={
            "type": "event_callback",
            "event": {
                "type": "app_mention",
                "channel": "C123",
                "text": "<@U_BOT> What is the status?",
                "user": "U456"
            }
        })
        
        assert response.status_code == 200
    
    def test_app_home_opened_event(self, client):
        """Test app_home_opened event."""
        response = client.post("/slack/events", json={
            "type": "event_callback",
            "event": {
                "type": "app_home_opened",
                "user": "U123"
            }
        })
        
        assert response.status_code == 200


# =============================================================================
# Interaction Handling Tests
# =============================================================================

class TestInteractionHandling:
    """Tests for Block Kit interaction handling."""
    
    @pytest.fixture
    def client(self):
        try:
            with patch.dict('sys.modules', {'app_home': MagicMock()}):
                from main import app
                with TestClient(app) as client:
                    yield client
        except ImportError as e:
            pytest.skip(f"Slack agent module not available: {e}")
    
    def test_view_submission_jira_update(self, client):
        """Test Jira update modal submission."""
        payload = {
            "type": "view_submission",
            "user": {"id": "U123", "username": "testuser"},
            "trigger_id": "trigger-123",
            "view": {
                "callback_id": "jira_update_submission",
                "state": {
                    "values": {
                        "ticket_key": {"ticket_key_input": {"value": "NEXUS-123"}},
                        "new_status": {"status_select": {"selected_option": {"value": "Done"}}},
                        "comment": {"comment_input": {"value": "Done via Slack"}}
                    }
                }
            }
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200
    
    def test_view_submission_release_check(self, client):
        """Test release check modal submission."""
        payload = {
            "type": "view_submission",
            "user": {"id": "U123", "username": "testuser"},
            "view": {
                "callback_id": "release_check_submission",
                "state": {
                    "values": {
                        "release_version": {"version_input": {"value": "v2.0.0"}},
                        "epic_key": {"epic_input": {"value": "NEXUS-100"}},
                        "repo_name": {"repo_input": {"value": "org/repo"}},
                        "environment": {"env_select": {"selected_option": {"value": "prod"}}}
                    }
                }
            }
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200
    
    def test_block_actions(self, client):
        """Test block action handling."""
        payload = {
            "type": "block_actions",
            "user": {"id": "U123", "username": "testuser"},
            "actions": [
                {"action_id": "some_action", "value": "some_value"}
            ]
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestSlackHelperFunctions:
    """Tests for Slack agent helper functions."""
    
    def test_status_emoji_mapping(self):
        """Test status emoji mapping in status_message."""
        from main import BlockKitBuilder
        
        # Test different statuses get correct emojis
        success_blocks = BlockKitBuilder.status_message("Test", "success", ["detail"])
        assert "✅" in success_blocks[0]["text"]["text"]
        
        failure_blocks = BlockKitBuilder.status_message("Test", "failure", ["detail"])
        assert "❌" in failure_blocks[0]["text"]["text"]
        
        pending_blocks = BlockKitBuilder.status_message("Test", "pending", ["detail"])
        assert "⏳" in pending_blocks[0]["text"]["text"]
        
        in_progress_blocks = BlockKitBuilder.status_message("Test", "in_progress", ["detail"])
        assert "🔄" in in_progress_blocks[0]["text"]["text"]
    
    def test_decision_emoji_mapping(self):
        """Test decision emoji mapping in status_message."""
        from main import BlockKitBuilder
        
        go_blocks = BlockKitBuilder.status_message("Test", "success", ["detail"], decision="GO")
        go_text = str(go_blocks)
        assert "🟢 GO" in go_text
        
        no_go_blocks = BlockKitBuilder.status_message("Test", "failure", ["detail"], decision="NO_GO")
        no_go_text = str(no_go_blocks)
        assert "🔴 NO-GO" in no_go_text
        
        conditional_blocks = BlockKitBuilder.status_message("Test", "success", ["detail"], decision="CONDITIONAL")
        conditional_text = str(conditional_blocks)
        assert "🟡 CONDITIONAL" in conditional_text


# =============================================================================
# Send DM Request Tests
# =============================================================================

class TestSendDMRequest:
    """Tests for SendDMRequest model."""
    
    def test_send_dm_request_creation(self):
        """Test SendDMRequest model creation."""
        from main import SendDMRequest
        
        request = SendDMRequest(
            email="test@example.com",
            message="Hello!",
            blocks=None
        )
        
        assert request.email == "test@example.com"
        assert request.message == "Hello!"
        assert request.blocks is None
    
    def test_send_dm_request_with_blocks(self):
        """Test SendDMRequest with blocks."""
        from main import SendDMRequest
        
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Hi"}}]
        request = SendDMRequest(
            email="test@example.com",
            message="Hello!",
            blocks=blocks
        )
        
        assert request.blocks == blocks


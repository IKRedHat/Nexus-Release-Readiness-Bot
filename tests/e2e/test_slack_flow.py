"""
End-to-End Tests for Slack Flow
Tests Slack command handling and interactions
"""
import pytest
import json
import sys
import os
import importlib

# Set test environment
os.environ["NEXUS_ENV"] = "test"

# Calculate paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SLACK_AGENT_PATH = os.path.join(PROJECT_ROOT, "services/agents/slack_agent")
SHARED_PATH = os.path.join(PROJECT_ROOT, "shared")


def get_slack_app():
    """Get the Slack agent FastAPI app with proper imports."""
    # Save current state
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        # Clear any cached imports
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'main' or mod_name.startswith('main.'):
                del sys.modules[mod_name]
        
        # Set up path
        sys.path.insert(0, SLACK_AGENT_PATH)
        sys.path.insert(0, SHARED_PATH)
        os.chdir(SLACK_AGENT_PATH)
        
        # Import
        import main as slack_main
        return slack_main.app, slack_main
        
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class TestSlackAgentHealth:
    """E2E tests for the Slack Agent health"""
    
    @pytest.fixture
    def client(self):
        """Create test client for slack agent"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test slack agent health"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "slack-agent"


class TestSlackCommands:
    """E2E tests for Slack slash commands"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_slash_command_help(self, client):
        """Test /nexus help command"""
        response = client.post("/slack/commands", data={
            "command": "/nexus",
            "text": "help",
            "user_id": "U123456",
            "user_name": "testuser",
            "channel_id": "C123456",
            "team_id": "T123456",
            "trigger_id": "trigger-123",
            "response_url": "https://hooks.slack.com/test"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return help message
        assert data["response_type"] == "ephemeral"
        assert "blocks" in data or "text" in data
    
    def test_slash_command_status(self, client):
        """Test /nexus status command"""
        response = client.post("/slack/commands", data={
            "command": "/nexus",
            "text": "status v2.0",
            "user_id": "U123456",
            "user_name": "testuser",
            "channel_id": "C123456",
            "team_id": "T123456",
            "trigger_id": "trigger-123",
            "response_url": "https://hooks.slack.com/test"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response_type" in data
    
    def test_jira_update_command(self, client):
        """Test /jira-update command"""
        response = client.post("/slack/commands", data={
            "command": "/jira-update",
            "text": "",
            "user_id": "U123456",
            "user_name": "testuser",
            "channel_id": "C123456",
            "team_id": "T123456",
            "trigger_id": "trigger-123",
            "response_url": "https://hooks.slack.com/test"
        })
        
        assert response.status_code == 200


class TestSlackEvents:
    """E2E tests for Slack Events API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_event_url_verification(self, client):
        """Test Slack Events API URL verification"""
        response = client.post("/slack/events", json={
            "type": "url_verification",
            "challenge": "test-challenge-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test-challenge-token"


class TestSlackNotifications:
    """E2E tests for Slack notifications"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_send_notification(self, client):
        """Test sending notification to channel"""
        # /notify endpoint takes query parameters
        response = client.post("/notify", params={
            "channel": "C123456",
            "message": "Test notification from Nexus"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestSlackInteractions:
    """Tests for Slack Block Kit interactions"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_modal_submission_jira_update(self, client):
        """Test Jira update modal submission"""
        payload = {
            "type": "view_submission",
            "user": {"id": "U123", "username": "testuser"},
            "trigger_id": "trigger-123",
            "view": {
                "callback_id": "jira_update_submission",
                "state": {
                    "values": {
                        "ticket_key": {
                            "ticket_key_input": {"value": "PROJ-123"}
                        },
                        "new_status": {
                            "status_select": {
                                "selected_option": {"value": "Done"}
                            }
                        },
                        "comment": {
                            "comment_input": {"value": "Fixed and verified"}
                        }
                    }
                }
            }
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200
    
    def test_modal_submission_release_check(self, client):
        """Test release check modal submission"""
        payload = {
            "type": "view_submission",
            "user": {"id": "U123", "username": "testuser"},
            "view": {
                "callback_id": "release_check_submission",
                "state": {
                    "values": {
                        "release_version": {
                            "version_input": {"value": "v2.0.0"}
                        },
                        "epic_key": {
                            "epic_input": {"value": "PROJ-100"}
                        },
                        "repo_name": {
                            "repo_input": {"value": "nexus/backend"}
                        },
                        "environment": {
                            "env_select": {
                                "selected_option": {"value": "prod"}
                            }
                        }
                    }
                }
            }
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200
    
    def test_block_action(self, client):
        """Test Block Kit button action"""
        payload = {
            "type": "block_actions",
            "user": {"id": "U123", "username": "testuser"},
            "trigger_id": "trigger-123",
            "actions": [
                {
                    "action_id": "view_report",
                    "value": "report-123"
                }
            ]
        }
        
        response = client.post("/slack/interactions", data={
            "payload": json.dumps(payload)
        })
        
        assert response.status_code == 200


class TestBlockKitBuilder:
    """Tests for BlockKitBuilder utility"""
    
    def test_block_kit_builder_exists(self):
        """Test BlockKitBuilder can be imported"""
        _, slack_module = get_slack_app()
        assert hasattr(slack_module, 'BlockKitBuilder')
        assert slack_module.BlockKitBuilder is not None
    
    def test_header_block(self):
        """Test BlockKitBuilder.header"""
        _, slack_module = get_slack_app()
        BlockKitBuilder = slack_module.BlockKitBuilder
        
        header = BlockKitBuilder.header("Test Header")
        assert header["type"] == "header"
        assert header["text"]["text"] == "Test Header"
    
    def test_section_block(self):
        """Test BlockKitBuilder.section"""
        _, slack_module = get_slack_app()
        BlockKitBuilder = slack_module.BlockKitBuilder
        
        section = BlockKitBuilder.section("Test *bold* text")
        assert section["type"] == "section"
        assert "bold" in section["text"]["text"]
    
    def test_divider_block(self):
        """Test BlockKitBuilder.divider"""
        _, slack_module = get_slack_app()
        BlockKitBuilder = slack_module.BlockKitBuilder
        
        divider = BlockKitBuilder.divider()
        assert divider["type"] == "divider"


class TestSlackExecuteEndpoint:
    """Tests for /execute endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app, _ = get_slack_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
    
    def test_execute_endpoint(self, client):
        """Test /execute endpoint"""
        # Use the correct schema for AgentTaskRequest
        response = client.post("/execute", json={
            "task_id": "task-123",
            "agent_type": "slack",
            "action": "send_notification",
            "parameters": {
                "channel": "C123456",
                "message": "Test message"
            }
        })
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

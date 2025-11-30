"""
End-to-End Tests for Slack Flow
Tests Slack command handling and interactions
"""
import pytest
import json
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath("services/agents/slack_agent"))
sys.path.insert(0, os.path.abspath("shared"))


class TestSlackAgent:
    """E2E tests for the Slack Agent"""
    
    @pytest.fixture
    def client(self):
        """Create test client for slack agent"""
        from main import app
        with TestClient(app) as client:
            yield client
    
    def test_health_check(self, client):
        """Test slack agent health"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "slack-agent"
    
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
        """Test /jira-update command opens modal"""
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
    
    def test_event_url_verification(self, client):
        """Test Slack Events API URL verification"""
        response = client.post("/slack/events", json={
            "type": "url_verification",
            "challenge": "test-challenge-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test-challenge-token"
    
    def test_send_notification(self, client):
        """Test sending notification to channel"""
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
        from main import app
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
        data = response.json()
        assert data.get("response_action") == "clear" or "ok" in data
    
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


class TestSlackMessageFormatting:
    """Tests for Slack message formatting"""
    
    def test_block_kit_builder(self):
        """Test BlockKitBuilder utility"""
        from main import BlockKitBuilder
        
        header = BlockKitBuilder.header("Test Header")
        assert header["type"] == "header"
        assert header["text"]["text"] == "Test Header"
        
        section = BlockKitBuilder.section("Test *bold* text")
        assert section["type"] == "section"
        assert "bold" in section["text"]["text"]
        
        divider = BlockKitBuilder.divider()
        assert divider["type"] == "divider"
    
    def test_status_message_builder(self):
        """Test status message building"""
        from main import BlockKitBuilder
        
        blocks = BlockKitBuilder.status_message(
            title="Release Check Complete",
            status="success",
            details=["All tests passed", "No blockers found"],
            decision="GO"
        )
        
        assert len(blocks) > 0
        assert any("header" in str(b) for b in blocks)


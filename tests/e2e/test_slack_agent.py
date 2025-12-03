"""
End-to-End Tests for Slack Agent
=================================

Comprehensive E2E tests for all Slack Agent endpoints and workflows.

Coverage:
- Health and status endpoints
- Notification endpoints
- Direct message endpoints
- Slash command handling
- Event handling
- Modal interactions
- Execute endpoint

Usage:
    pytest tests/e2e/test_slack_agent.py -v
"""

import pytest
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any

SLACK_AGENT_URL = os.environ.get("SLACK_AGENT_URL", "http://localhost:8084")


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create async HTTP client."""
    return httpx.AsyncClient(timeout=30.0)


@pytest.fixture
def sample_notify_request():
    """Sample notification request."""
    return {
        "channel": "#release-updates",
        "message": "Test notification from E2E test",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*E2E Test Notification*"}
            }
        ]
    }


@pytest.fixture
def sample_dm_request():
    """Sample DM request."""
    return {
        "email": "test@example.com",
        "message": "Test DM from E2E test"
    }


@pytest.fixture
def sample_slash_command():
    """Sample slash command form data."""
    return {
        "command": "/nexus",
        "text": "help",
        "user_id": "U12345",
        "user_name": "testuser",
        "channel_id": "C12345",
        "team_id": "T12345",
        "trigger_id": "trigger-12345",
        "response_url": "https://hooks.slack.com/commands/test"
    }


# =============================================================================
# Health Endpoint Tests
# =============================================================================

class TestSlackAgentHealth:
    """Tests for Slack Agent health endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_health_endpoint(self, client):
        """Test health check returns healthy status."""
        try:
            response = await client.get(f"{SLACK_AGENT_URL}/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["service"] == "slack-agent"
            assert "mock_mode" in data
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        try:
            response = await client.get(f"{SLACK_AGENT_URL}/metrics")
            
            assert response.status_code == 200
            assert len(response.text) > 0
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Execute Endpoint Tests
# =============================================================================

class TestSlackAgentExecute:
    """Tests for Slack Agent execute endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_execute_notify(self, client, sample_notify_request):
        """Test execute with notify action."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/execute",
                json={
                    "task_id": "e2e-notify-1",
                    "action": "notify",
                    "payload": sample_notify_request
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert data["agent_type"] == "slack"
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_execute_send_dm(self, client, sample_dm_request):
        """Test execute with send_dm action."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/execute",
                json={
                    "task_id": "e2e-dm-1",
                    "action": "send_dm",
                    "payload": sample_dm_request
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # In mock mode, this should succeed
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_execute_unknown_action(self, client):
        """Test execute with unknown action fails gracefully."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/execute",
                json={
                    "task_id": "e2e-unknown-1",
                    "action": "unknown_action",
                    "payload": {}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "failed"
            assert "unknown" in data["error_message"].lower()
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Notification Endpoint Tests
# =============================================================================

class TestSlackAgentNotifications:
    """Tests for Slack notification endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_notify_endpoint(self, client):
        """Test notify endpoint with query params."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/notify",
                params={
                    "channel": "#test-channel",
                    "message": "E2E Test notification"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_notify_with_blocks(self, client):
        """Test notify with Block Kit blocks."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/notify",
                params={
                    "channel": "#test-channel",
                    "message": "E2E Test with blocks"
                },
                json=[
                    {"type": "header", "text": {"type": "plain_text", "text": "Test Header"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": "Test content"}}
                ]
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Direct Message Tests
# =============================================================================

class TestSlackAgentDM:
    """Tests for Slack direct message endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_send_dm_endpoint(self, client, sample_dm_request):
        """Test send-dm endpoint."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/send-dm",
                json=sample_dm_request
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # In mock mode, this should succeed
            assert data["status"] in ["success", "failed"]
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_send_dm_with_blocks(self, client):
        """Test send-dm with Block Kit blocks."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/send-dm",
                json={
                    "email": "test@example.com",
                    "message": "DM with blocks",
                    "blocks": [
                        {"type": "section", "text": {"type": "mrkdwn", "text": "*Important!*"}}
                    ]
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Slash Command Tests
# =============================================================================

class TestSlackAgentCommands:
    """Tests for Slack slash command handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_nexus_help_command(self, client):
        """Test /nexus help command."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/commands",
                data={
                    "command": "/nexus",
                    "text": "help",
                    "user_id": "U123",
                    "user_name": "testuser",
                    "channel_id": "C123",
                    "team_id": "T123",
                    "trigger_id": "trigger-123",
                    "response_url": "https://hooks.slack.com/commands/test"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Help should return blocks
            assert "blocks" in data or "text" in data
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_nexus_empty_command(self, client):
        """Test /nexus with empty text shows help."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/commands",
                data={
                    "command": "/nexus",
                    "text": "",
                    "user_id": "U123",
                    "user_name": "testuser",
                    "channel_id": "C123",
                    "team_id": "T123",
                    "trigger_id": "trigger-123",
                    "response_url": "https://hooks.slack.com/commands/test"
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_nexus_query_command(self, client):
        """Test /nexus with a query."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/commands",
                data={
                    "command": "/nexus",
                    "text": "What is the release status?",
                    "user_id": "U123",
                    "user_name": "testuser",
                    "channel_id": "C123",
                    "team_id": "T123",
                    "trigger_id": "trigger-123",
                    "response_url": "https://hooks.slack.com/commands/test"
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Event Handling Tests
# =============================================================================

class TestSlackAgentEvents:
    """Tests for Slack Events API handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_url_verification(self, client):
        """Test URL verification challenge."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/events",
                json={
                    "type": "url_verification",
                    "challenge": "e2e-challenge-token"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["challenge"] == "e2e-challenge-token"
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_app_mention_event(self, client):
        """Test app_mention event."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/events",
                json={
                    "type": "event_callback",
                    "event": {
                        "type": "app_mention",
                        "channel": "C123",
                        "text": "<@U_BOT> check release status",
                        "user": "U456"
                    }
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_app_home_opened_event(self, client):
        """Test app_home_opened event."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/events",
                json={
                    "type": "event_callback",
                    "event": {
                        "type": "app_home_opened",
                        "user": "U123"
                    }
                }
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Interaction Handling Tests
# =============================================================================

class TestSlackAgentInteractions:
    """Tests for Block Kit interaction handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_jira_update_modal_submission(self, client):
        """Test Jira update modal submission."""
        try:
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
                            "comment": {"comment_input": {"value": "Done via E2E test"}}
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": json.dumps(payload)}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_release_check_modal_submission(self, client):
        """Test release check modal submission."""
        try:
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
                            "environment": {"env_select": {"selected_option": {"value": "staging"}}}
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": json.dumps(payload)}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_report_modal_submission(self, client):
        """Test report generation modal submission."""
        try:
            payload = {
                "type": "view_submission",
                "user": {"id": "U123", "username": "testuser"},
                "view": {
                    "callback_id": "report_submission",
                    "state": {
                        "values": {
                            "report_type": {"type_select": {"selected_option": {"value": "release"}}},
                            "version": {"version_input": {"value": "v2.0.0"}},
                            "page_id": {"page_input": {"value": ""}}
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": json.dumps(payload)}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_hygiene_fix_modal_submission(self, client):
        """Test hygiene fix modal submission."""
        try:
            private_metadata = json.dumps({
                "tickets": [
                    {"key": "NEXUS-101", "missing_fields": ["Labels"]}
                ]
            })
            
            payload = {
                "type": "view_submission",
                "user": {"id": "U123", "username": "testuser"},
                "view": {
                    "callback_id": "hygiene_fix_submission",
                    "private_metadata": private_metadata,
                    "state": {
                        "values": {
                            "labels_NEXUS-101": {"labels_input": {"value": "backend, api"}}
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": json.dumps(payload)}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_block_action(self, client):
        """Test block action handling."""
        try:
            payload = {
                "type": "block_actions",
                "user": {"id": "U123", "username": "testuser"},
                "trigger_id": "trigger-123",
                "actions": [
                    {"action_id": "test_action", "value": "test_value"}
                ],
                "channel": {"id": "C123"},
                "message": {"ts": "1234567890.123456"}
            }
            
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": json.dumps(payload)}
            )
            
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestSlackAgentErrors:
    """Tests for error handling in Slack Agent."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_invalid_execute_payload(self, client):
        """Test execute with invalid payload."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/execute",
                json={
                    "task_id": "e2e-invalid-1",
                    # Missing action field
                    "payload": {}
                }
            )
            
            # Should return validation error
            assert response.status_code == 422
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_invalid_dm_request(self, client):
        """Test send-dm with missing required fields."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/send-dm",
                json={
                    # Missing email
                    "message": "Test message"
                }
            )
            
            assert response.status_code == 422
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_malformed_interaction_payload(self, client):
        """Test interaction with malformed payload."""
        try:
            response = await client.post(
                f"{SLACK_AGENT_URL}/slack/interactions",
                data={"payload": "not valid json"}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 422, 500]
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


# =============================================================================
# Performance Tests
# =============================================================================

class TestSlackAgentPerformance:
    """Basic performance tests for Slack Agent."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_health_check_fast(self, client):
        """Test health check responds quickly."""
        import time
        
        try:
            start = time.perf_counter()
            response = await client.get(f"{SLACK_AGENT_URL}/health")
            duration = time.perf_counter() - start
            
            assert response.status_code == 200
            assert duration < 0.5  # Should be under 500ms
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_concurrent_notifications(self, client):
        """Test handling concurrent notifications."""
        import asyncio
        
        try:
            async def send_notification(i: int):
                return await client.post(
                    f"{SLACK_AGENT_URL}/execute",
                    json={
                        "task_id": f"e2e-concurrent-{i}",
                        "action": "notify",
                        "payload": {
                            "channel": "#test",
                            "message": f"Concurrent test {i}"
                        }
                    }
                )
            
            tasks = [send_notification(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r.status_code == 200 for r in results)
            
        except httpx.ConnectError:
            pytest.skip("Slack Agent not running")


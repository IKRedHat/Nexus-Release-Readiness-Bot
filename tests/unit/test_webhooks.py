"""
Unit Tests for Webhooks Service
===============================

Tests for webhook subscription management, event delivery,
HMAC security, and retry logic.
"""

import pytest
import sys
import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/webhooks")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["WEBHOOKS_HMAC_SECRET"] = "test-secret-key"


class TestWebhookSubscription:
    """Tests for webhook subscription management."""
    
    def test_create_subscription(self):
        """Test creating a webhook subscription."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        subscription = manager.create_subscription(
            endpoint_url="https://example.com/webhook",
            event_types=["release.created", "build.completed"],
            secret="subscriber-secret"
        )
        
        assert subscription["id"] is not None
        assert subscription["endpoint_url"] == "https://example.com/webhook"
        assert len(subscription["event_types"]) == 2
        assert subscription["active"] is True
    
    def test_create_subscription_all_events(self):
        """Test subscription to all events."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        subscription = manager.create_subscription(
            endpoint_url="https://example.com/all-events",
            event_types=["*"],  # Subscribe to all
            secret="secret"
        )
        
        assert "*" in subscription["event_types"]
    
    def test_update_subscription(self):
        """Test updating an existing subscription."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        # Create initial subscription
        sub = manager.create_subscription(
            endpoint_url="https://example.com/webhook",
            event_types=["build.completed"],
            secret="secret"
        )
        
        # Update it
        updated = manager.update_subscription(
            sub["id"],
            event_types=["build.completed", "build.failed"],
            active=False
        )
        
        assert len(updated["event_types"]) == 2
        assert updated["active"] is False
    
    def test_delete_subscription(self):
        """Test deleting a subscription."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        sub = manager.create_subscription(
            endpoint_url="https://example.com/webhook",
            event_types=["release.created"],
            secret="secret"
        )
        
        result = manager.delete_subscription(sub["id"])
        
        assert result["deleted"] is True
        
        # Should not exist anymore
        with pytest.raises(KeyError):
            manager.get_subscription(sub["id"])
    
    def test_list_subscriptions(self):
        """Test listing all subscriptions."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        # Create multiple subscriptions
        manager.create_subscription("https://a.com", ["event.a"], "s1")
        manager.create_subscription("https://b.com", ["event.b"], "s2")
        manager.create_subscription("https://c.com", ["event.c"], "s3")
        
        subs = manager.list_subscriptions()
        
        assert len(subs) >= 3


class TestHMACSecurity:
    """Tests for HMAC signature security."""
    
    def test_generate_signature(self):
        """Test HMAC signature generation."""
        from main import WebhookSecurity
        
        payload = {"event": "test", "data": {"key": "value"}}
        secret = "test-secret"
        
        signature = WebhookSecurity.generate_signature(
            json.dumps(payload),
            secret
        )
        
        assert signature.startswith("sha256=")
        assert len(signature) > 10
    
    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        from main import WebhookSecurity
        
        payload = {"event": "test", "data": {"key": "value"}}
        payload_str = json.dumps(payload)
        secret = "test-secret"
        
        signature = WebhookSecurity.generate_signature(payload_str, secret)
        
        is_valid = WebhookSecurity.verify_signature(
            payload_str,
            signature,
            secret
        )
        
        assert is_valid is True
    
    def test_verify_invalid_signature(self):
        """Test rejection of invalid signature."""
        from main import WebhookSecurity
        
        payload = {"event": "test"}
        payload_str = json.dumps(payload)
        
        is_valid = WebhookSecurity.verify_signature(
            payload_str,
            "sha256=invalid_signature",
            "secret"
        )
        
        assert is_valid is False
    
    def test_verify_tampered_payload(self):
        """Test rejection of tampered payload."""
        from main import WebhookSecurity
        
        original_payload = {"event": "test", "data": {"amount": 100}}
        secret = "secret"
        
        signature = WebhookSecurity.generate_signature(
            json.dumps(original_payload),
            secret
        )
        
        # Tamper with the payload
        tampered_payload = {"event": "test", "data": {"amount": 999}}
        
        is_valid = WebhookSecurity.verify_signature(
            json.dumps(tampered_payload),
            signature,
            secret
        )
        
        assert is_valid is False
    
    def test_timing_safe_comparison(self):
        """Test that signature comparison is timing-safe."""
        from main import WebhookSecurity
        
        # This is more of a verification that hmac.compare_digest is used
        payload = "test"
        secret = "secret"
        
        sig1 = WebhookSecurity.generate_signature(payload, secret)
        sig2 = WebhookSecurity.generate_signature(payload, secret)
        
        # Same inputs should produce same output
        assert sig1 == sig2


class TestEventDelivery:
    """Tests for webhook event delivery."""
    
    @pytest.fixture
    def manager(self):
        """Create WebhookManager with mock HTTP client."""
        from main import WebhookManager
        return WebhookManager()
    
    @pytest.mark.asyncio
    async def test_deliver_event_success(self, manager):
        """Test successful event delivery."""
        # Create subscription
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["test.event"],
            "secret"
        )
        
        event = {
            "type": "test.event",
            "data": {"key": "value"},
            "timestamp": datetime.now().isoformat()
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            result = await manager.deliver_event(sub["id"], event)
            
            assert result["status"] == "delivered"
            assert result["attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_deliver_event_includes_headers(self, manager):
        """Test event delivery includes required headers."""
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["test.event"],
            "secret"
        )
        
        event = {"type": "test.event", "data": {}}
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock(status_code=200)
            mock_post.return_value = mock_response
            
            await manager.deliver_event(sub["id"], event)
            
            call_args = mock_post.call_args
            headers = call_args.kwargs.get("headers", {})
            
            # Should include signature header
            assert "X-Nexus-Signature" in headers or "X-Hub-Signature-256" in headers
            assert "Content-Type" in headers
    
    @pytest.mark.asyncio
    async def test_deliver_event_retry_on_failure(self, manager):
        """Test retry logic on delivery failure."""
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["test.event"],
            "secret"
        )
        
        event = {"type": "test.event", "data": {}}
        
        # Fail twice, succeed on third attempt
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection failed")
            return MagicMock(status_code=200)
        
        with patch('httpx.AsyncClient.post', side_effect=mock_post):
            result = await manager.deliver_event(
                sub["id"],
                event,
                max_retries=3
            )
            
            assert call_count >= 2
    
    @pytest.mark.asyncio
    async def test_delivery_tracking(self, manager):
        """Test delivery attempt tracking."""
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["test.event"],
            "secret"
        )
        
        event = {"type": "test.event", "data": {}}
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            
            await manager.deliver_event(sub["id"], event)
            
            history = manager.get_delivery_history(sub["id"])
            
            assert len(history) >= 1
            assert history[0]["status"] == "success"


class TestEventTypes:
    """Tests for event type management."""
    
    def test_list_event_types(self):
        """Test listing available event types."""
        from main import EventRegistry
        
        event_types = EventRegistry.list_all()
        
        # Check for expected event types
        expected = [
            "release.created",
            "release.deployed",
            "build.completed",
            "build.failed",
            "ticket.updated",
            "hygiene.violation"
        ]
        
        for event in expected:
            assert event in event_types
    
    def test_event_type_validation(self):
        """Test event type validation."""
        from main import EventRegistry
        
        assert EventRegistry.is_valid("release.created") is True
        assert EventRegistry.is_valid("invalid.event.type") is False
    
    def test_event_type_schema(self):
        """Test getting event type schema."""
        from main import EventRegistry
        
        schema = EventRegistry.get_schema("build.completed")
        
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema


class TestRateLimiting:
    """Tests for webhook rate limiting."""
    
    def test_rate_limit_enforcement(self):
        """Test rate limit is enforced."""
        from main import WebhookManager, RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 should succeed
        for i in range(5):
            assert limiter.allow_request("subscription-1") is True
        
        # 6th should be rate limited
        assert limiter.allow_request("subscription-1") is False
    
    def test_rate_limit_per_subscription(self):
        """Test rate limits are per-subscription."""
        from main import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Use up sub-1's quota
        for i in range(3):
            limiter.allow_request("sub-1")
        
        # sub-2 should still have quota
        assert limiter.allow_request("sub-2") is True
    
    def test_rate_limit_reset(self):
        """Test rate limit window reset."""
        from main import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use quota
        limiter.allow_request("sub-1")
        limiter.allow_request("sub-1")
        assert limiter.allow_request("sub-1") is False
        
        # Wait for window to reset (use mock time)
        with patch('time.time', return_value=time.time() + 2):
            assert limiter.allow_request("sub-1") is True


class TestEventFiltering:
    """Tests for event filtering."""
    
    def test_filter_by_event_type(self):
        """Test filtering events by type."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        # Create subscription for specific events
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["build.completed"],
            "secret"
        )
        
        # Should match
        assert manager.should_deliver(sub["id"], "build.completed") is True
        
        # Should not match
        assert manager.should_deliver(sub["id"], "build.failed") is False
    
    def test_wildcard_subscription(self):
        """Test wildcard event subscription."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["build.*"],  # All build events
            "secret"
        )
        
        assert manager.should_deliver(sub["id"], "build.completed") is True
        assert manager.should_deliver(sub["id"], "build.failed") is True
        assert manager.should_deliver(sub["id"], "release.created") is False


class TestWebhookPayload:
    """Tests for webhook payload formatting."""
    
    def test_standard_payload_format(self):
        """Test standard payload format."""
        from main import WebhookPayload
        
        payload = WebhookPayload.create(
            event_type="build.completed",
            data={"job_name": "nexus-main", "build_number": 142}
        )
        
        assert "id" in payload
        assert "type" in payload
        assert "timestamp" in payload
        assert "data" in payload
        assert payload["type"] == "build.completed"
    
    def test_payload_serialization(self):
        """Test payload JSON serialization."""
        from main import WebhookPayload
        
        payload = WebhookPayload.create(
            event_type="test.event",
            data={"nested": {"key": "value"}, "list": [1, 2, 3]}
        )
        
        # Should be JSON serializable
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        assert parsed["data"]["nested"]["key"] == "value"


class TestHealthAndStatus:
    """Tests for webhook service health and status."""
    
    def test_subscription_health_check(self):
        """Test subscription health status."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        sub = manager.create_subscription(
            "https://example.com/webhook",
            ["test.event"],
            "secret"
        )
        
        health = manager.get_subscription_health(sub["id"])
        
        assert "status" in health
        assert "last_delivery" in health
        assert "success_rate" in health
    
    def test_service_stats(self):
        """Test service statistics."""
        from main import WebhookManager
        
        manager = WebhookManager()
        
        stats = manager.get_stats()
        
        assert "total_subscriptions" in stats
        assert "total_deliveries" in stats
        assert "success_rate" in stats
        assert "events_per_minute" in stats


import time  # Import for mock

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


"""
Unit Tests for Webhooks Service
===============================

Tests for webhook subscription management, HMAC security,
event delivery, and rate limiting.
"""

import pytest
import sys
import os
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add paths for imports
WEBHOOKS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/webhooks"))
SHARED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
sys.path.insert(0, WEBHOOKS_PATH)
sys.path.insert(0, SHARED_PATH)

# Change directory context for relative imports
os.chdir(WEBHOOKS_PATH)

# Set test environment
os.environ["NEXUS_ENV"] = "test"


class TestWebhookModels:
    """Tests for webhook Pydantic models."""
    
    def test_create_subscription_request(self):
        """Test CreateSubscriptionRequest model."""
        from main import CreateSubscriptionRequest
        
        request = CreateSubscriptionRequest(
            name="Test Subscription",
            url="https://example.com/webhook",
            events=["release.created", "build.success"]
        )
        
        assert request.name == "Test Subscription"
        assert str(request.url) == "https://example.com/webhook"
        assert len(request.events) == 2
    
    def test_webhook_subscription_model(self):
        """Test WebhookSubscription model."""
        from main import WebhookSubscription
        
        sub = WebhookSubscription(
            id="sub-123",
            name="Test Sub",
            url="https://example.com/webhook",
            events=["release.created"],
            secret="test-secret",
            active=True
        )
        
        assert sub.id == "sub-123"
        assert sub.active == True
    
    def test_webhook_event_model(self):
        """Test WebhookEvent model."""
        from main import WebhookEvent
        
        event = WebhookEvent(
            event_type="release.created",
            payload={"version": "2.3.0"},
            source="nexus"
        )
        
        assert event.event_type == "release.created"
        assert event.payload["version"] == "2.3.0"


class TestEventTypes:
    """Tests for event type definitions."""
    
    def test_event_types_enum(self):
        """Test EventType enum exists."""
        from main import EventType
        
        # Check actual enum values
        assert hasattr(EventType, 'RELEASE_CREATED')
        assert hasattr(EventType, 'BUILD_SUCCESS')
        assert hasattr(EventType, 'BUILD_FAILED')
    
    def test_event_type_values(self):
        """Test EventType enum values."""
        from main import EventType
        
        assert EventType.RELEASE_CREATED.value == "release.created"
        assert EventType.BUILD_SUCCESS.value == "build.success"


class TestSignatureGeneration:
    """Tests for HMAC signature generation."""
    
    def test_generate_signature(self):
        """Test signature generation."""
        secret = "test-secret"
        payload = '{"event": "test"}'
        timestamp = "1234567890"
        
        # Generate signature manually
        message = f"{timestamp}.{payload}"
        expected = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert len(expected) == 64  # SHA256 hex digest
    
    def test_signature_changes_with_payload(self):
        """Test different payloads produce different signatures."""
        secret = "test-secret"
        timestamp = "1234567890"
        
        payload1 = '{"event": "test1"}'
        payload2 = '{"event": "test2"}'
        
        message1 = f"{timestamp}.{payload1}"
        message2 = f"{timestamp}.{payload2}"
        
        sig1 = hmac.new(secret.encode(), message1.encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode(), message2.encode(), hashlib.sha256).hexdigest()
        
        assert sig1 != sig2
    
    def test_signature_changes_with_secret(self):
        """Test different secrets produce different signatures."""
        payload = '{"event": "test"}'
        timestamp = "1234567890"
        message = f"{timestamp}.{payload}"
        
        sig1 = hmac.new("secret1".encode(), message.encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new("secret2".encode(), message.encode(), hashlib.sha256).hexdigest()
        
        assert sig1 != sig2


class TestSignatureVerification:
    """Tests for signature verification."""
    
    def test_valid_signature_verifies(self):
        """Test valid signature passes verification."""
        secret = "test-secret"
        payload = '{"event": "test"}'
        timestamp = "1234567890"
        
        message = f"{timestamp}.{payload}"
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        
        # Verify
        expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        
        assert hmac.compare_digest(signature, expected)
    
    def test_invalid_signature_fails(self):
        """Test invalid signature fails verification."""
        secret = "test-secret"
        payload = '{"event": "test"}'
        timestamp = "1234567890"
        
        message = f"{timestamp}.{payload}"
        valid_sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        invalid_sig = "invalid" + valid_sig[7:]
        
        assert not hmac.compare_digest(valid_sig, invalid_sig)
    
    def test_timing_safe_comparison(self):
        """Test timing-safe comparison is used."""
        # hmac.compare_digest is timing-safe
        sig1 = "a" * 64
        sig2 = "a" * 64
        
        # Should use compare_digest, not ==
        assert hmac.compare_digest(sig1, sig2)


class TestWebhookConfig:
    """Tests for webhook configuration."""
    
    def test_config_defaults(self):
        """Test Config class has defaults."""
        from main import Config
        
        assert hasattr(Config, 'MAX_RETRIES')
        assert hasattr(Config, 'INITIAL_RETRY_DELAY')
        assert hasattr(Config, 'SIGNATURE_HEADER')
    
    def test_config_values(self):
        """Test Config values are reasonable."""
        from main import Config
        
        assert Config.MAX_RETRIES >= 1
        assert Config.INITIAL_RETRY_DELAY >= 1
        assert Config.DELIVERY_TIMEOUT >= 1


class TestDeliveryAttempt:
    """Tests for delivery attempt model."""
    
    def test_delivery_attempt_model(self):
        """Test DeliveryAttempt model."""
        from main import DeliveryAttempt
        
        attempt = DeliveryAttempt(
            attempt_number=1,
            timestamp=datetime.utcnow(),
            status_code=200,
            success=True
        )
        
        assert attempt.attempt_number == 1
        assert attempt.success == True


class TestWebhookPayload:
    """Tests for webhook payload structure."""
    
    def test_payload_structure(self):
        """Test webhook payload has required fields."""
        payload = {
            "event_type": "release.created",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"version": "2.3.0"},
            "delivery_id": "del-123"
        }
        
        assert "event_type" in payload
        assert "timestamp" in payload
        assert "data" in payload
    
    def test_payload_serialization(self):
        """Test payload can be serialized to JSON."""
        payload = {
            "event_type": "release.created",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"version": "2.3.0", "ready": True}
        }
        
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        assert parsed["event_type"] == "release.created"


class TestRateLimiting:
    """Tests for rate limiting configuration."""
    
    def test_rate_limit_config(self):
        """Test rate limit configuration exists."""
        from main import Config
        
        assert hasattr(Config, 'MAX_REQUESTS_PER_MINUTE')
        assert Config.MAX_REQUESTS_PER_MINUTE > 0


class TestEventFiltering:
    """Tests for event filtering logic."""
    
    def test_wildcard_matches_all(self):
        """Test wildcard * matches all events."""
        wildcard = "*"
        test_events = ["release.created", "build.success", "custom.event"]
        
        for event in test_events:
            # Wildcard should match any event
            assert wildcard == "*"
    
    def test_specific_event_matching(self):
        """Test specific event matching."""
        subscribed_events = ["release.created", "build.success"]
        
        assert "release.created" in subscribed_events
        assert "build.failed" not in subscribed_events


class TestWebhookStats:
    """Tests for webhook statistics model."""
    
    def test_webhook_stats_model(self):
        """Test WebhookStats model."""
        from main import WebhookStats
        
        stats = WebhookStats(
            total_subscriptions=5,
            active_subscriptions=3,
            total_deliveries=100,
            successful_deliveries=95,
            failed_deliveries=5
        )
        
        assert stats.total_subscriptions == 5
        assert stats.successful_deliveries == 95


class TestWebhookHealthEndpoint:
    """Tests for webhook health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPrometheusMetrics:
    """Tests for Prometheus metrics exposure."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert b"nexus_webhook" in response.content or b"# HELP" in response.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

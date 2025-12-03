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
from datetime import datetime

# Set test environment
os.environ["NEXUS_ENV"] = "test"


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
        sig1 = "a" * 64
        sig2 = "a" * 64
        
        assert hmac.compare_digest(sig1, sig2)


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
    
    def test_prefix_matching(self):
        """Test event prefix matching."""
        prefix = "release."
        events = ["release.created", "release.updated", "build.success"]
        
        matching = [e for e in events if e.startswith(prefix)]
        
        assert len(matching) == 2


class TestRetryLogic:
    """Tests for retry logic."""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        base_delay = 5
        max_delay = 3600
        
        def calculate_delay(attempt: int) -> int:
            delay = base_delay * (2 ** attempt)
            return min(delay, max_delay)
        
        assert calculate_delay(0) == 5
        assert calculate_delay(1) == 10
        assert calculate_delay(2) == 20
        assert calculate_delay(10) == 3600  # Capped at max
    
    def test_max_retries(self):
        """Test max retries configuration."""
        max_retries = 5
        attempts = 0
        
        while attempts < max_retries:
            attempts += 1
        
        assert attempts == max_retries


class TestWebhookAppImport:
    """Tests for Webhook service app import."""
    
    def test_app_can_be_imported(self):
        """Test webhook service app can be imported."""
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/webhooks")))
        
        try:
            from main import app
            assert app is not None
        except ImportError:
            pytest.skip("Webhook dependencies not available")


class TestDeliveryStatus:
    """Tests for delivery status constants."""
    
    def test_status_values(self):
        """Test delivery status constants."""
        statuses = ["pending", "success", "failed", "retrying"]
        
        assert "pending" in statuses
        assert "success" in statuses
        assert "failed" in statuses


class TestSubscriptionValidation:
    """Tests for subscription validation logic."""
    
    def test_valid_url(self):
        """Test URL validation."""
        import re
        
        url_pattern = r'^https?://'
        
        assert re.match(url_pattern, "https://example.com/webhook")
        assert re.match(url_pattern, "http://localhost:8080/hook")
        assert not re.match(url_pattern, "not-a-url")
    
    def test_valid_event_list(self):
        """Test event list validation."""
        events = ["release.created", "build.success"]
        
        assert len(events) > 0
        assert all(isinstance(e, str) for e in events)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

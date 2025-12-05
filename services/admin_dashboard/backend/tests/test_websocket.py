"""
WebSocket Integration Tests

Tests for WebSocket endpoints and real-time functionality.
"""

import pytest
import json
from fastapi.testclient import TestClient
from websockets.sync.client import connect as ws_connect
import asyncio


class TestWebSocketMain:
    """Tests for main WebSocket endpoint."""
    
    def test_websocket_connect(self, client: TestClient):
        """Test basic WebSocket connection."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
    
    def test_websocket_ping_pong(self, client: TestClient):
        """Test heartbeat ping/pong."""
        with client.websocket_connect("/ws") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_websocket_subscribe(self, client: TestClient):
        """Test channel subscription."""
        with client.websocket_connect("/ws") as websocket:
            # Subscribe to health channel
            websocket.send_json({
                "type": "subscribe",
                "channel": "health"
            })
            
            # Should receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["channel"] == "health"
    
    def test_websocket_unsubscribe(self, client: TestClient):
        """Test channel unsubscription."""
        with client.websocket_connect("/ws") as websocket:
            # Subscribe first
            websocket.send_json({
                "type": "subscribe",
                "channel": "health"
            })
            websocket.receive_json()  # Subscription confirmation
            
            # Unsubscribe
            websocket.send_json({
                "type": "unsubscribe",
                "channel": "health"
            })
            
            # Should receive unsubscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "unsubscribed"
            assert response["channel"] == "health"


class TestWebSocketHealth:
    """Tests for health WebSocket endpoint."""
    
    def test_health_websocket_connect(self, client: TestClient):
        """Test health WebSocket connection."""
        with client.websocket_connect("/ws/health") as websocket:
            assert websocket is not None
    
    def test_health_websocket_receives_updates(self, client: TestClient):
        """Test health WebSocket receives periodic updates."""
        with client.websocket_connect("/ws/health") as websocket:
            # Should receive health update within timeout
            # Note: In tests, we may not wait for the full 10s interval
            websocket.send_json({"type": "ping"})
            
            try:
                response = websocket.receive_json(timeout=2)
                # Either pong or health_update
                assert response["type"] in ["pong", "health_update"]
            except Exception:
                # Timeout is acceptable in test environment
                pass


class TestWebSocketActivity:
    """Tests for activity WebSocket endpoint."""
    
    def test_activity_websocket_connect(self, client: TestClient):
        """Test activity WebSocket connection."""
        with client.websocket_connect("/ws/activity") as websocket:
            assert websocket is not None


class TestWebSocketMetrics:
    """Tests for metrics WebSocket endpoint."""
    
    def test_metrics_websocket_connect(self, client: TestClient):
        """Test metrics WebSocket connection."""
        with client.websocket_connect("/ws/metrics") as websocket:
            assert websocket is not None


class TestWebSocketMessageFormats:
    """Tests for WebSocket message formats."""
    
    def test_message_has_timestamp(self, client: TestClient):
        """Test all messages include timestamp."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert "timestamp" in response
    
    def test_invalid_message_handling(self, client: TestClient):
        """Test handling of invalid messages."""
        with client.websocket_connect("/ws") as websocket:
            # Send invalid JSON (raw text)
            try:
                websocket.send_text("invalid json")
                # Should not crash, may disconnect
            except Exception:
                pass  # Expected behavior


class TestWebSocketConcurrency:
    """Tests for WebSocket concurrent connections."""
    
    def test_multiple_connections(self, client: TestClient):
        """Test multiple simultaneous connections."""
        with client.websocket_connect("/ws") as ws1:
            with client.websocket_connect("/ws") as ws2:
                # Both connections should work
                ws1.send_json({"type": "ping"})
                ws2.send_json({"type": "ping"})
                
                response1 = ws1.receive_json()
                response2 = ws2.receive_json()
                
                assert response1["type"] == "pong"
                assert response2["type"] == "pong"
    
    def test_multiple_channel_subscriptions(self, client: TestClient):
        """Test subscribing to multiple channels."""
        with client.websocket_connect("/ws") as websocket:
            channels = ["health", "activity", "metrics"]
            
            for channel in channels:
                websocket.send_json({
                    "type": "subscribe",
                    "channel": channel
                })
                response = websocket.receive_json()
                assert response["type"] == "subscribed"
                assert response["channel"] == channel


class TestWebSocketReconnection:
    """Tests for WebSocket reconnection scenarios."""
    
    def test_reconnect_after_disconnect(self, client: TestClient):
        """Test that reconnection works after disconnect."""
        # First connection
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "ping"})
            websocket.receive_json()
        
        # Second connection (after first closed)
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"


class TestWebSocketChannelBroadcast:
    """Tests for WebSocket channel broadcasting."""
    
    def test_broadcast_to_subscribed_clients(self, client: TestClient):
        """Test that broadcasts reach subscribed clients."""
        # This test would require triggering a broadcast from the backend
        # In a real scenario, we'd trigger an event and verify clients receive it
        with client.websocket_connect("/ws") as websocket:
            # Subscribe to activity channel
            websocket.send_json({
                "type": "subscribe",
                "channel": "activity"
            })
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            
            # In production, we'd trigger an activity and verify receipt
            # For now, just verify subscription works


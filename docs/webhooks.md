# Webhook Integrations for External Systems

The Nexus Webhook Service provides enterprise-grade webhook capabilities for integrating with external systems. Receive real-time notifications about releases, builds, deployments, and more.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      NEXUS WEBHOOK ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    Events    ┌──────────────┐    Delivery    ┌─────┐ │
│  │    Nexus     │ ──────────▶  │   Webhook    │ ──────────────▶│ Your│ │
│  │   Services   │              │   Service    │                │ App │ │
│  └──────────────┘              └──────────────┘                └─────┘ │
│                                       │                                 │
│                                       │ Features:                       │
│                                       │ ✓ HMAC Signatures              │
│                                       │ ✓ Automatic Retries            │
│                                       │ ✓ Rate Limiting                │
│                                       │ ✓ Event Filtering              │
│                                       │ ✓ Delivery Tracking            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### 🔔 Event Types

Subscribe to any of the following event types:

#### Release Events
| Event | Description |
|-------|-------------|
| `release.created` | New release initiated |
| `release.started` | Release process started |
| `release.completed` | Release successfully completed |
| `release.failed` | Release failed |
| `release.rolled_back` | Release was rolled back |

#### Build Events
| Event | Description |
|-------|-------------|
| `build.started` | Build started |
| `build.completed` | Build completed successfully |
| `build.failed` | Build failed |

#### Deployment Events
| Event | Description |
|-------|-------------|
| `deployment.started` | Deployment to environment started |
| `deployment.completed` | Deployment completed |
| `deployment.failed` | Deployment failed |

#### Jira Events
| Event | Description |
|-------|-------------|
| `ticket.created` | New ticket created |
| `ticket.updated` | Ticket updated |
| `ticket.transitioned` | Ticket status changed |
| `ticket.completed` | Ticket marked done |

#### Hygiene Events
| Event | Description |
|-------|-------------|
| `hygiene.check_completed` | Hygiene check finished |
| `hygiene.violations_found` | New violations detected |
| `hygiene.score_changed` | Hygiene score changed significantly |

#### Security Events
| Event | Description |
|-------|-------------|
| `security.scan_completed` | Security scan finished |
| `security.vulnerability_detected` | New vulnerability found |

#### Analytics Events
| Event | Description |
|-------|-------------|
| `analytics.anomaly_detected` | Metric anomaly detected |
| `analytics.kpi_threshold_breached` | KPI threshold exceeded |

#### System Events
| Event | Description |
|-------|-------------|
| `system.agent_status_changed` | Agent health changed |
| `system.orchestrator_error` | Orchestrator error occurred |

### 🔐 Security

#### HMAC Signature Verification

Every webhook request includes an HMAC-SHA256 signature for verification:

```
X-Nexus-Signature-256: sha256=abc123...
X-Nexus-Timestamp: 2025-11-30T10:30:00Z
X-Nexus-Delivery: uuid-delivery-id
X-Nexus-Event: release.completed
```

**Verify the signature in your application:**

```python
import hmac
import hashlib

def verify_webhook(payload: str, timestamp: str, signature: str, secret: str) -> bool:
    """Verify Nexus webhook signature."""
    # Construct the signed message
    message = f"{timestamp}.{payload}"
    
    # Calculate expected signature
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    # Use constant-time comparison
    return hmac.compare_digest(expected, signature)
```

```javascript
// Node.js verification
const crypto = require('crypto');

function verifyWebhook(payload, timestamp, signature, secret) {
    const message = `${timestamp}.${payload}`;
    const expected = crypto
        .createHmac('sha256', secret)
        .update(message)
        .digest('hex');
    
    const providedSig = signature.replace('sha256=', '');
    return crypto.timingSafeEqual(
        Buffer.from(expected),
        Buffer.from(providedSig)
    );
}
```

### 🔄 Automatic Retries

Failed deliveries are automatically retried with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 5 seconds |
| 3 | 10 seconds |
| 4 | 20 seconds |
| 5 | 40 seconds |
| ... | Up to 1 hour max |

**Retry Configuration:**
```yaml
WEBHOOK_MAX_RETRIES: 5
WEBHOOK_INITIAL_DELAY: 5  # seconds
WEBHOOK_MAX_DELAY: 3600   # 1 hour
```

### 🎛️ Rate Limiting

Each subscription has configurable rate limiting:

```json
{
  "name": "My Webhook",
  "rate_limit": 60  // max 60 requests per minute
}
```

## Quick Start

### 1. Create a Subscription

```bash
curl -X POST "http://webhooks:8087/api/v1/subscriptions" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Notifier",
    "url": "https://your-app.com/webhooks/nexus",
    "events": [
      "build.completed",
      "build.failed",
      "deployment.completed"
    ],
    "description": "Notify CI/CD dashboard of build events"
  }'
```

**Response:**
```json
{
  "id": "sub_abc123",
  "name": "CI/CD Notifier",
  "url": "https://your-app.com/webhooks/nexus",
  "secret": "a1b2c3d4e5f6...",  // Store this securely!
  "events": ["build.completed", "build.failed", "deployment.completed"],
  "active": true,
  "created_at": "2025-11-30T10:30:00Z"
}
```

> ⚠️ **Important:** Store the `secret` securely. It cannot be retrieved later and is needed to verify webhook signatures.

### 2. Test Your Endpoint

```bash
curl -X POST "http://webhooks:8087/api/v1/subscriptions/sub_abc123/test"
```

### 3. Handle Webhooks

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

WEBHOOK_SECRET = "your-webhook-secret"

@app.post("/webhooks/nexus")
async def handle_nexus_webhook(request: Request):
    # Get headers
    signature = request.headers.get("X-Nexus-Signature-256", "")
    timestamp = request.headers.get("X-Nexus-Timestamp", "")
    event_type = request.headers.get("X-Nexus-Event", "")
    
    # Get raw body
    body = await request.body()
    payload = body.decode()
    
    # Verify signature
    if not verify_signature(payload, timestamp, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event
    event = await request.json()
    
    # Handle by event type
    if event_type == "build.completed":
        handle_build_completed(event["data"])
    elif event_type == "deployment.completed":
        handle_deployment_completed(event["data"])
    
    return {"status": "received"}

def verify_signature(payload, timestamp, signature, secret):
    message = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)
```

## API Reference

### Subscription Management

#### Create Subscription
```http
POST /api/v1/subscriptions
```

**Request Body:**
```json
{
  "name": "string (required)",
  "url": "https://... (required)",
  "events": ["event.type", ...],
  "project_filter": "PROJECT_KEY",
  "team_filter": "team-name",
  "severity_filter": ["critical", "high"],
  "description": "optional description",
  "rate_limit": 60
}
```

#### List Subscriptions
```http
GET /api/v1/subscriptions?active_only=true&event_type=build.completed
```

#### Get Subscription
```http
GET /api/v1/subscriptions/{subscription_id}
```

#### Update Subscription
```http
PATCH /api/v1/subscriptions/{subscription_id}
```

#### Delete Subscription
```http
DELETE /api/v1/subscriptions/{subscription_id}
```

#### Toggle Active Status
```http
POST /api/v1/subscriptions/{subscription_id}/toggle
```

#### Rotate Secret
```http
POST /api/v1/subscriptions/{subscription_id}/rotate-secret
```

### Event Publishing (Internal)

#### Publish Event
```http
POST /api/v1/events
```

**Request Body:**
```json
{
  "type": "release.completed",
  "source": "orchestrator",
  "data": {
    "release_id": "rel-123",
    "version": "2.0.0",
    "status": "success"
  },
  "metadata": {
    "project": "NEXUS",
    "team": "platform"
  }
}
```

#### Batch Publish
```http
POST /api/v1/events/batch
```

### Delivery Management

#### Get Delivery History
```http
GET /api/v1/deliveries?subscription_id=sub_123&status=failed&limit=50
```

#### Get Pending Retries
```http
GET /api/v1/deliveries/pending
```

#### Manual Retry
```http
POST /api/v1/deliveries/{delivery_id}/retry
```

### Testing

#### Test Webhook URL
```http
POST /api/v1/test
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "secret": "optional-secret",
  "event_type": "release.started"
}
```

#### Test Subscription
```http
POST /api/v1/subscriptions/{subscription_id}/test
```

### Statistics

#### Get Service Stats
```http
GET /api/v1/stats
```

**Response:**
```json
{
  "total_subscriptions": 15,
  "active_subscriptions": 12,
  "total_events_processed": 5432,
  "successful_deliveries": 5210,
  "failed_deliveries": 45,
  "pending_retries": 3,
  "avg_delivery_time_ms": 245.5,
  "events_by_type": {
    "build.completed": 2100,
    "deployment.completed": 890,
    "release.completed": 312
  }
}
```

## Webhook Payload Format

All webhooks are delivered with the following structure:

```json
{
  "id": "evt_abc123",
  "type": "release.completed",
  "timestamp": "2025-11-30T10:30:00Z",
  "source": "orchestrator",
  "data": {
    // Event-specific data
  },
  "metadata": {
    "project": "NEXUS",
    "team": "platform",
    "environment": "production"
  }
}
```

### Event-Specific Data Examples

#### release.completed
```json
{
  "data": {
    "release_id": "rel-2.0.0",
    "version": "2.0.0",
    "status": "success",
    "duration_seconds": 3600,
    "tickets_included": 45,
    "deployed_to": ["staging", "production"]
  }
}
```

#### build.failed
```json
{
  "data": {
    "build_id": "build-12345",
    "job_name": "nexus-main",
    "branch": "feature/new-feature",
    "commit_sha": "abc123def",
    "error_message": "Test failures in module X",
    "failed_tests": 3,
    "logs_url": "https://jenkins/build/12345/console"
  }
}
```

#### security.vulnerability_detected
```json
{
  "data": {
    "scan_id": "scan-789",
    "severity": "critical",
    "cve_id": "CVE-2025-1234",
    "package": "vulnerable-lib",
    "current_version": "1.0.0",
    "fixed_version": "1.0.1",
    "recommendation": "Upgrade immediately"
  }
}
```

## Prometheus Metrics

```prometheus
# Webhook deliveries
nexus_webhook_deliveries_total{event_type="build.completed",status="success"} 1523
nexus_webhook_deliveries_total{event_type="build.completed",status="failed"} 12

# Delivery latency
nexus_webhook_delivery_latency_seconds_bucket{subscriber_id="sub_123",le="0.5"} 1200
nexus_webhook_delivery_latency_seconds_bucket{subscriber_id="sub_123",le="1.0"} 1450

# Retry attempts
nexus_webhook_retries_total{event_type="deployment.completed"} 45

# Active subscriptions
nexus_webhook_active_subscriptions{event_type="build.completed"} 8

# Queue size
nexus_webhook_queue_size 3
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis for queue management |
| `POSTGRES_URL` | `postgresql://...` | PostgreSQL for persistence |
| `WEBHOOK_MAX_RETRIES` | `5` | Maximum retry attempts |
| `WEBHOOK_INITIAL_DELAY` | `5` | Initial retry delay (seconds) |
| `WEBHOOK_MAX_DELAY` | `3600` | Maximum retry delay (seconds) |
| `WEBHOOK_RATE_LIMIT` | `60` | Default rate limit per minute |
| `WEBHOOK_TIMEOUT` | `30` | Delivery timeout (seconds) |

## Best Practices

### For Webhook Consumers

1. **Always verify signatures** - Never trust unverified webhooks
2. **Respond quickly** - Return 2xx within 30 seconds, process async
3. **Be idempotent** - Handle duplicate deliveries gracefully
4. **Log delivery IDs** - For debugging and deduplication

### For Administrators

1. **Monitor delivery success rates** - Alert on high failure rates
2. **Rotate secrets regularly** - Use the rotate-secret endpoint
3. **Set appropriate rate limits** - Balance reliability and volume
4. **Review pending retries** - Clear stuck deliveries

### Example: Idempotent Handler

```python
from redis import Redis
import json

redis = Redis()

async def handle_webhook(event):
    delivery_id = request.headers.get("X-Nexus-Delivery")
    
    # Check if already processed
    if redis.get(f"webhook:processed:{delivery_id}"):
        return {"status": "already_processed"}
    
    # Process the event
    await process_event(event)
    
    # Mark as processed (expire after 24h)
    redis.setex(f"webhook:processed:{delivery_id}", 86400, "1")
    
    return {"status": "processed"}
```

## Troubleshooting

### Common Issues

#### Signature Verification Fails
- Ensure you're using the raw request body, not parsed JSON
- Check that the timestamp header matches what was signed
- Verify the secret matches what was provided at creation

#### Deliveries Not Received
- Check subscription is active: `GET /api/v1/subscriptions/{id}`
- Verify event type is in subscription's events list
- Check delivery history for errors: `GET /api/v1/deliveries`

#### High Retry Rate
- Ensure your endpoint responds within 30 seconds
- Check your endpoint is returning 2xx status codes
- Verify your endpoint is accessible from Nexus network

### Debug Endpoint

Use the signature verification endpoint to debug issues:

```bash
curl -X POST "http://webhooks:8087/api/v1/verify-signature" \
  -d 'payload={"test": true}' \
  -G --data-urlencode "timestamp=2025-11-30T10:30:00Z" \
  --data-urlencode "signature=sha256=abc123" \
  --data-urlencode "secret=your-secret"
```

## Integration Examples

### Slack Notification

```python
import requests

def handle_release_completed(event):
    slack_webhook = "https://hooks.slack.com/services/..."
    
    requests.post(slack_webhook, json={
        "text": f"🚀 Release {event['data']['version']} deployed!",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Release {event['data']['version']}* has been deployed\n"
                            f"Tickets: {event['data']['tickets_included']}\n"
                            f"Duration: {event['data']['duration_seconds']}s"
                }
            }
        ]
    })
```

### PagerDuty Alert

```python
import requests

def handle_vulnerability_detected(event):
    if event['data']['severity'] == 'critical':
        requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json={
                "routing_key": "your-routing-key",
                "event_action": "trigger",
                "payload": {
                    "summary": f"Critical vulnerability: {event['data']['cve_id']}",
                    "severity": "critical",
                    "source": "nexus-security",
                    "custom_details": event['data']
                }
            }
        )
```

### Datadog Event

```python
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.events_api import EventsApi

def handle_build_failed(event):
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api = EventsApi(api_client)
        api.create_event({
            "title": f"Build Failed: {event['data']['job_name']}",
            "text": event['data']['error_message'],
            "alert_type": "error",
            "tags": ["nexus", f"branch:{event['data']['branch']}"]
        })
```


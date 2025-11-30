"""
Nexus Webhook Service
=====================

Enterprise-grade webhook system for external integrations providing:
- Webhook subscription management (CRUD)
- Multiple event types support
- HMAC signature verification for security
- Retry logic with exponential backoff
- Delivery tracking and logging
- Event filtering and transformation
- Rate limiting per subscriber

Author: Nexus Team
Version: 2.0.0
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Query, Header, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, field_validator
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Webhook service configuration."""
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://nexus:nexus@localhost:5432/nexus")
    
    # Retry configuration
    MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "5"))
    INITIAL_RETRY_DELAY = int(os.getenv("WEBHOOK_INITIAL_DELAY", "5"))  # seconds
    MAX_RETRY_DELAY = int(os.getenv("WEBHOOK_MAX_DELAY", "3600"))  # 1 hour
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("WEBHOOK_RATE_LIMIT", "60"))
    
    # Security
    SIGNATURE_HEADER = "X-Nexus-Signature-256"
    TIMESTAMP_HEADER = "X-Nexus-Timestamp"
    DELIVERY_ID_HEADER = "X-Nexus-Delivery"
    
    # Timeouts
    DELIVERY_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "30"))

# =============================================================================
# Prometheus Metrics
# =============================================================================

WEBHOOK_DELIVERIES = Counter(
    "nexus_webhook_deliveries_total",
    "Total webhook delivery attempts",
    ["event_type", "status"]
)
WEBHOOK_LATENCY = Histogram(
    "nexus_webhook_delivery_latency_seconds",
    "Webhook delivery latency",
    ["subscriber_id"]
)
WEBHOOK_RETRIES = Counter(
    "nexus_webhook_retries_total",
    "Total webhook retry attempts",
    ["event_type"]
)
ACTIVE_SUBSCRIPTIONS = Gauge(
    "nexus_webhook_active_subscriptions",
    "Number of active webhook subscriptions",
    ["event_type"]
)
WEBHOOK_QUEUE_SIZE = Gauge(
    "nexus_webhook_queue_size",
    "Current webhook delivery queue size"
)

# =============================================================================
# Event Types
# =============================================================================

class EventType(str, Enum):
    """Supported webhook event types."""
    
    # Release Events
    RELEASE_CREATED = "release.created"
    RELEASE_STARTED = "release.started"
    RELEASE_COMPLETED = "release.completed"
    RELEASE_FAILED = "release.failed"
    RELEASE_ROLLED_BACK = "release.rolled_back"
    
    # Build Events
    BUILD_STARTED = "build.started"
    BUILD_COMPLETED = "build.completed"
    BUILD_FAILED = "build.failed"
    
    # Deployment Events
    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"
    
    # Jira Events
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_TRANSITIONED = "ticket.transitioned"
    TICKET_COMPLETED = "ticket.completed"
    
    # Hygiene Events
    HYGIENE_CHECK_COMPLETED = "hygiene.check_completed"
    HYGIENE_VIOLATIONS_FOUND = "hygiene.violations_found"
    HYGIENE_SCORE_CHANGED = "hygiene.score_changed"
    
    # Security Events
    SECURITY_SCAN_COMPLETED = "security.scan_completed"
    VULNERABILITY_DETECTED = "security.vulnerability_detected"
    
    # Analytics Events
    ANOMALY_DETECTED = "analytics.anomaly_detected"
    KPI_THRESHOLD_BREACHED = "analytics.kpi_threshold_breached"
    
    # System Events
    AGENT_STATUS_CHANGED = "system.agent_status_changed"
    ORCHESTRATOR_ERROR = "system.orchestrator_error"

# =============================================================================
# Data Models
# =============================================================================

class WebhookEvent(BaseModel):
    """Represents an event to be delivered via webhook."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to webhook payload format."""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "metadata": self.metadata or {}
        }

class WebhookSubscription(BaseModel):
    """Webhook subscription configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    secret: str = Field(default_factory=lambda: secrets.token_hex(32))
    
    # Event filtering
    events: List[EventType] = Field(default_factory=list)
    
    # Optional filters
    project_filter: Optional[str] = None
    team_filter: Optional[str] = None
    severity_filter: Optional[List[str]] = None
    
    # Configuration
    active: bool = True
    content_type: str = "application/json"
    
    # Rate limiting
    rate_limit: int = Field(default=60, ge=1, le=1000)  # per minute
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    description: Optional[str] = None
    
    # Statistics
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: Optional[datetime] = None
    last_delivery_status: Optional[str] = None
    
    @field_validator('events')
    @classmethod
    def events_not_empty(cls, v):
        if not v:
            raise ValueError('At least one event type must be specified')
        return v

class CreateSubscriptionRequest(BaseModel):
    """Request to create a new webhook subscription."""
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    events: List[EventType]
    project_filter: Optional[str] = None
    team_filter: Optional[str] = None
    severity_filter: Optional[List[str]] = None
    description: Optional[str] = None
    rate_limit: int = Field(default=60, ge=1, le=1000)

class UpdateSubscriptionRequest(BaseModel):
    """Request to update a webhook subscription."""
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    events: Optional[List[EventType]] = None
    project_filter: Optional[str] = None
    team_filter: Optional[str] = None
    active: Optional[bool] = None
    rate_limit: Optional[int] = None
    description: Optional[str] = None

class DeliveryAttempt(BaseModel):
    """Record of a webhook delivery attempt."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_id: str
    event_id: str
    event_type: str
    
    attempt_number: int
    status: str  # pending, success, failed, retrying
    
    request_url: str
    request_headers: Dict[str, str]
    request_body: str
    
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

class DeliveryQueue(BaseModel):
    """Pending delivery in the queue."""
    event: WebhookEvent
    subscription_id: str
    attempt: int = 1
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    priority: int = 0  # Higher = more urgent

class WebhookStats(BaseModel):
    """Webhook service statistics."""
    total_subscriptions: int
    active_subscriptions: int
    total_events_processed: int
    successful_deliveries: int
    failed_deliveries: int
    pending_retries: int
    avg_delivery_time_ms: float
    events_by_type: Dict[str, int]

class TestWebhookRequest(BaseModel):
    """Request to test a webhook endpoint."""
    url: HttpUrl
    secret: Optional[str] = None
    event_type: EventType = EventType.RELEASE_STARTED

# =============================================================================
# Webhook Engine
# =============================================================================

class WebhookEngine:
    """
    Core webhook engine handling subscription management,
    event delivery, retries, and monitoring.
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=Config.DELIVERY_TIMEOUT)
        
        # In-memory storage (use Redis/Postgres in production)
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._delivery_queue: List[DeliveryQueue] = []
        self._delivery_history: List[DeliveryAttempt] = []
        self._rate_limiters: Dict[str, List[datetime]] = defaultdict(list)
        
        # Background tasks
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._events_processed = 0
        self._successful_deliveries = 0
        self._failed_deliveries = 0
    
    async def start(self):
        """Start the webhook processor."""
        self._processing = True
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("Webhook processor started")
    
    async def stop(self):
        """Stop the webhook processor."""
        self._processing = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        await self.http_client.aclose()
        logger.info("Webhook processor stopped")
    
    # -------------------------------------------------------------------------
    # Subscription Management
    # -------------------------------------------------------------------------
    
    async def create_subscription(
        self,
        request: CreateSubscriptionRequest,
        created_by: Optional[str] = None
    ) -> WebhookSubscription:
        """Create a new webhook subscription."""
        
        subscription = WebhookSubscription(
            name=request.name,
            url=request.url,
            events=request.events,
            project_filter=request.project_filter,
            team_filter=request.team_filter,
            severity_filter=request.severity_filter,
            rate_limit=request.rate_limit,
            description=request.description,
            created_by=created_by
        )
        
        self._subscriptions[subscription.id] = subscription
        
        # Update metrics
        for event_type in subscription.events:
            ACTIVE_SUBSCRIPTIONS.labels(event_type=event_type.value).inc()
        
        logger.info(f"Created subscription {subscription.id} for {subscription.url}")
        
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get a subscription by ID."""
        return self._subscriptions.get(subscription_id)
    
    async def list_subscriptions(
        self,
        active_only: bool = False,
        event_type: Optional[EventType] = None
    ) -> List[WebhookSubscription]:
        """List all subscriptions with optional filtering."""
        
        subs = list(self._subscriptions.values())
        
        if active_only:
            subs = [s for s in subs if s.active]
        
        if event_type:
            subs = [s for s in subs if event_type in s.events]
        
        return subs
    
    async def update_subscription(
        self,
        subscription_id: str,
        request: UpdateSubscriptionRequest
    ) -> WebhookSubscription:
        """Update an existing subscription."""
        
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(sub, key, value)
        
        sub.updated_at = datetime.utcnow()
        
        logger.info(f"Updated subscription {subscription_id}")
        
        return sub
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription."""
        
        sub = self._subscriptions.pop(subscription_id, None)
        if not sub:
            return False
        
        # Update metrics
        for event_type in sub.events:
            ACTIVE_SUBSCRIPTIONS.labels(event_type=event_type.value).dec()
        
        logger.info(f"Deleted subscription {subscription_id}")
        
        return True
    
    async def rotate_secret(self, subscription_id: str) -> str:
        """Rotate the webhook secret for a subscription."""
        
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub.secret = secrets.token_hex(32)
        sub.updated_at = datetime.utcnow()
        
        logger.info(f"Rotated secret for subscription {subscription_id}")
        
        return sub.secret
    
    # -------------------------------------------------------------------------
    # Event Publishing
    # -------------------------------------------------------------------------
    
    async def publish_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Publish an event to all matching subscriptions.
        Returns delivery status for each subscription.
        """
        
        self._events_processed += 1
        
        # Find matching subscriptions
        matching_subs = await self._find_matching_subscriptions(event)
        
        results = {
            "event_id": event.id,
            "event_type": event.type.value,
            "subscriptions_matched": len(matching_subs),
            "deliveries": []
        }
        
        for sub in matching_subs:
            # Check rate limit
            if not self._check_rate_limit(sub.id, sub.rate_limit):
                results["deliveries"].append({
                    "subscription_id": sub.id,
                    "status": "rate_limited"
                })
                continue
            
            # Queue for delivery
            delivery = DeliveryQueue(
                event=event,
                subscription_id=sub.id,
                attempt=1
            )
            self._delivery_queue.append(delivery)
            
            results["deliveries"].append({
                "subscription_id": sub.id,
                "status": "queued"
            })
        
        WEBHOOK_QUEUE_SIZE.set(len(self._delivery_queue))
        
        logger.info(f"Published event {event.id} ({event.type}) to {len(matching_subs)} subscribers")
        
        return results
    
    async def _find_matching_subscriptions(
        self,
        event: WebhookEvent
    ) -> List[WebhookSubscription]:
        """Find subscriptions matching the event."""
        
        matching = []
        
        for sub in self._subscriptions.values():
            if not sub.active:
                continue
            
            # Check event type
            if event.type not in sub.events:
                continue
            
            # Check project filter
            if sub.project_filter:
                event_project = event.data.get("project") or event.metadata.get("project")
                if event_project and event_project != sub.project_filter:
                    continue
            
            # Check team filter
            if sub.team_filter:
                event_team = event.data.get("team") or event.metadata.get("team")
                if event_team and event_team != sub.team_filter:
                    continue
            
            # Check severity filter
            if sub.severity_filter:
                event_severity = event.data.get("severity")
                if event_severity and event_severity not in sub.severity_filter:
                    continue
            
            matching.append(sub)
        
        return matching
    
    def _check_rate_limit(self, subscription_id: str, limit: int) -> bool:
        """Check if subscription is within rate limit."""
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self._rate_limiters[subscription_id] = [
            t for t in self._rate_limiters[subscription_id]
            if t > minute_ago
        ]
        
        # Check limit
        if len(self._rate_limiters[subscription_id]) >= limit:
            return False
        
        # Record this request
        self._rate_limiters[subscription_id].append(now)
        
        return True
    
    # -------------------------------------------------------------------------
    # Delivery Processing
    # -------------------------------------------------------------------------
    
    async def _process_queue(self):
        """Background task to process delivery queue."""
        
        while self._processing:
            try:
                # Get next delivery
                if not self._delivery_queue:
                    await asyncio.sleep(0.1)
                    continue
                
                # Sort by priority and scheduled time
                self._delivery_queue.sort(
                    key=lambda d: (-d.priority, d.scheduled_at)
                )
                
                # Get next ready delivery
                now = datetime.utcnow()
                ready = [d for d in self._delivery_queue if d.scheduled_at <= now]
                
                if not ready:
                    await asyncio.sleep(0.5)
                    continue
                
                delivery = ready[0]
                self._delivery_queue.remove(delivery)
                
                WEBHOOK_QUEUE_SIZE.set(len(self._delivery_queue))
                
                # Process delivery
                await self._deliver(delivery)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing delivery queue: {e}")
                await asyncio.sleep(1)
    
    async def _deliver(self, delivery: DeliveryQueue):
        """Attempt to deliver a webhook."""
        
        sub = self._subscriptions.get(delivery.subscription_id)
        if not sub:
            logger.warning(f"Subscription {delivery.subscription_id} not found, skipping delivery")
            return
        
        event = delivery.event
        
        # Prepare payload
        payload = event.to_payload()
        payload_json = json.dumps(payload, default=str)
        
        # Generate signature
        timestamp = datetime.utcnow().isoformat()
        signature = self._generate_signature(sub.secret, timestamp, payload_json)
        
        # Prepare headers
        headers = {
            "Content-Type": sub.content_type,
            "User-Agent": "Nexus-Webhook/2.0",
            Config.SIGNATURE_HEADER: f"sha256={signature}",
            Config.TIMESTAMP_HEADER: timestamp,
            Config.DELIVERY_ID_HEADER: str(uuid.uuid4()),
            "X-Nexus-Event": event.type.value,
        }
        
        # Record attempt
        attempt = DeliveryAttempt(
            subscription_id=sub.id,
            event_id=event.id,
            event_type=event.type.value,
            attempt_number=delivery.attempt,
            status="pending",
            request_url=str(sub.url),
            request_headers=headers,
            request_body=payload_json
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Make request
            response = await self.http_client.post(
                str(sub.url),
                content=payload_json,
                headers=headers
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            attempt.response_status = response.status_code
            attempt.response_body = response.text[:1000] if response.text else None
            attempt.response_time_ms = int(elapsed)
            attempt.completed_at = datetime.utcnow()
            
            # Check success (2xx status codes)
            if 200 <= response.status_code < 300:
                attempt.status = "success"
                sub.successful_deliveries += 1
                self._successful_deliveries += 1
                
                WEBHOOK_DELIVERIES.labels(
                    event_type=event.type.value,
                    status="success"
                ).inc()
                
                logger.info(
                    f"Delivered {event.type} to {sub.url} "
                    f"(attempt {delivery.attempt}, {elapsed:.0f}ms)"
                )
            else:
                # Failed - schedule retry
                await self._handle_failure(delivery, attempt, f"HTTP {response.status_code}")
                
        except httpx.TimeoutException:
            await self._handle_failure(delivery, attempt, "Timeout")
        except httpx.ConnectError:
            await self._handle_failure(delivery, attempt, "Connection failed")
        except Exception as e:
            await self._handle_failure(delivery, attempt, str(e))
        
        # Update subscription stats
        sub.total_deliveries += 1
        sub.last_delivery_at = datetime.utcnow()
        sub.last_delivery_status = attempt.status
        
        # Record attempt
        self._delivery_history.append(attempt)
        
        # Keep history limited
        if len(self._delivery_history) > 10000:
            self._delivery_history = self._delivery_history[-5000:]
        
        # Update metrics
        WEBHOOK_LATENCY.labels(subscriber_id=sub.id).observe(
            (attempt.response_time_ms or 0) / 1000
        )
    
    async def _handle_failure(
        self,
        delivery: DeliveryQueue,
        attempt: DeliveryAttempt,
        error: str
    ):
        """Handle a failed delivery attempt."""
        
        sub = self._subscriptions.get(delivery.subscription_id)
        
        attempt.status = "failed"
        attempt.error_message = error
        attempt.completed_at = datetime.utcnow()
        
        WEBHOOK_DELIVERIES.labels(
            event_type=delivery.event.type.value,
            status="failed"
        ).inc()
        
        # Check if we should retry
        if delivery.attempt < Config.MAX_RETRIES:
            # Calculate next retry delay (exponential backoff)
            delay = min(
                Config.INITIAL_RETRY_DELAY * (2 ** (delivery.attempt - 1)),
                Config.MAX_RETRY_DELAY
            )
            
            next_attempt = DeliveryQueue(
                event=delivery.event,
                subscription_id=delivery.subscription_id,
                attempt=delivery.attempt + 1,
                scheduled_at=datetime.utcnow() + timedelta(seconds=delay)
            )
            
            self._delivery_queue.append(next_attempt)
            attempt.status = "retrying"
            attempt.next_retry_at = next_attempt.scheduled_at
            
            WEBHOOK_RETRIES.labels(event_type=delivery.event.type.value).inc()
            
            logger.warning(
                f"Delivery failed ({error}), scheduling retry "
                f"{delivery.attempt + 1}/{Config.MAX_RETRIES} in {delay}s"
            )
        else:
            sub.failed_deliveries += 1
            self._failed_deliveries += 1
            
            logger.error(
                f"Delivery to {sub.url} failed after {Config.MAX_RETRIES} attempts: {error}"
            )
    
    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    
    def _generate_signature(
        self,
        secret: str,
        timestamp: str,
        payload: str
    ) -> str:
        """Generate HMAC-SHA256 signature for payload."""
        
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(
        self,
        secret: str,
        timestamp: str,
        payload: str,
        provided_signature: str
    ) -> bool:
        """Verify webhook signature (for incoming webhooks)."""
        
        expected = self._generate_signature(secret, timestamp, payload)
        return hmac.compare_digest(expected, provided_signature)
    
    # -------------------------------------------------------------------------
    # Delivery History
    # -------------------------------------------------------------------------
    
    async def get_delivery_history(
        self,
        subscription_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[DeliveryAttempt]:
        """Get delivery history with filtering."""
        
        history = self._delivery_history.copy()
        
        if subscription_id:
            history = [h for h in history if h.subscription_id == subscription_id]
        
        if event_type:
            history = [h for h in history if h.event_type == event_type.value]
        
        if status:
            history = [h for h in history if h.status == status]
        
        # Sort by created_at descending
        history.sort(key=lambda h: h.created_at, reverse=True)
        
        return history[:limit]
    
    async def get_pending_retries(self) -> List[DeliveryQueue]:
        """Get all pending retry deliveries."""
        return [d for d in self._delivery_queue if d.attempt > 1]
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    async def get_stats(self) -> WebhookStats:
        """Get webhook service statistics."""
        
        event_counts = defaultdict(int)
        for attempt in self._delivery_history:
            event_counts[attempt.event_type] += 1
        
        # Calculate average delivery time
        successful_times = [
            a.response_time_ms for a in self._delivery_history
            if a.response_time_ms and a.status == "success"
        ]
        avg_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        pending = [d for d in self._delivery_queue if d.attempt > 1]
        
        return WebhookStats(
            total_subscriptions=len(self._subscriptions),
            active_subscriptions=len([s for s in self._subscriptions.values() if s.active]),
            total_events_processed=self._events_processed,
            successful_deliveries=self._successful_deliveries,
            failed_deliveries=self._failed_deliveries,
            pending_retries=len(pending),
            avg_delivery_time_ms=round(avg_time, 2),
            events_by_type=dict(event_counts)
        )
    
    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------
    
    async def test_webhook(self, request: TestWebhookRequest) -> Dict[str, Any]:
        """Send a test webhook to verify endpoint."""
        
        test_event = WebhookEvent(
            type=request.event_type,
            source="nexus.webhook.test",
            data={
                "message": "This is a test webhook from Nexus",
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata={"test": True}
        )
        
        payload = test_event.to_payload()
        payload_json = json.dumps(payload, default=str)
        
        secret = request.secret or secrets.token_hex(32)
        timestamp = datetime.utcnow().isoformat()
        signature = self._generate_signature(secret, timestamp, payload_json)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Nexus-Webhook/2.0 (Test)",
            Config.SIGNATURE_HEADER: f"sha256={signature}",
            Config.TIMESTAMP_HEADER: timestamp,
            Config.DELIVERY_ID_HEADER: f"test-{uuid.uuid4()}",
            "X-Nexus-Event": test_event.type.value,
        }
        
        start_time = datetime.utcnow()
        
        try:
            response = await self.http_client.post(
                str(request.url),
                content=payload_json,
                headers=headers
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_ms": int(elapsed),
                "response_body": response.text[:500] if response.text else None,
                "headers_sent": headers,
                "signature_secret": secret if not request.secret else "[provided]"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "headers_sent": headers
            }


# =============================================================================
# FastAPI Application
# =============================================================================

webhook_engine: Optional[WebhookEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global webhook_engine
    
    logger.info("🚀 Starting Nexus Webhook Service...")
    webhook_engine = WebhookEngine()
    await webhook_engine.start()
    
    # Create some demo subscriptions
    await _create_demo_subscriptions()
    
    logger.info("✅ Webhook Service ready!")
    
    yield
    
    # Cleanup
    if webhook_engine:
        await webhook_engine.stop()
    logger.info("👋 Webhook Service shutdown complete")

async def _create_demo_subscriptions():
    """Create demo subscriptions for testing."""
    
    demo_subs = [
        CreateSubscriptionRequest(
            name="CI/CD Pipeline Notifier",
            url="https://hooks.example.com/cicd",
            events=[
                EventType.BUILD_STARTED,
                EventType.BUILD_COMPLETED,
                EventType.BUILD_FAILED,
                EventType.DEPLOYMENT_COMPLETED
            ],
            description="Notifies CI/CD dashboard of build events"
        ),
        CreateSubscriptionRequest(
            name="Release Tracker",
            url="https://hooks.example.com/releases",
            events=[
                EventType.RELEASE_CREATED,
                EventType.RELEASE_STARTED,
                EventType.RELEASE_COMPLETED,
                EventType.RELEASE_FAILED
            ],
            description="Tracks release lifecycle events"
        ),
        CreateSubscriptionRequest(
            name="Security Alerts",
            url="https://hooks.example.com/security",
            events=[
                EventType.SECURITY_SCAN_COMPLETED,
                EventType.VULNERABILITY_DETECTED
            ],
            severity_filter=["critical", "high"],
            description="High-priority security notifications"
        )
    ]
    
    for sub_request in demo_subs:
        await webhook_engine.create_subscription(sub_request, created_by="system")

app = FastAPI(
    title="Nexus Webhook Service",
    description="Enterprise webhook system for external integrations",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "webhooks",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# -----------------------------------------------------------------------------
# Subscription Management
# -----------------------------------------------------------------------------

@app.post("/api/v1/subscriptions", response_model=WebhookSubscription)
async def create_subscription(
    request: CreateSubscriptionRequest,
    x_user_id: Optional[str] = Header(None)
):
    """
    Create a new webhook subscription.
    
    The response includes a secret key for signature verification.
    Store this securely - it cannot be retrieved later.
    """
    return await webhook_engine.create_subscription(request, created_by=x_user_id)

@app.get("/api/v1/subscriptions", response_model=List[WebhookSubscription])
async def list_subscriptions(
    active_only: bool = Query(False),
    event_type: Optional[EventType] = Query(None)
):
    """List all webhook subscriptions."""
    subs = await webhook_engine.list_subscriptions(active_only, event_type)
    
    # Hide secrets in list response
    for sub in subs:
        sub.secret = "[hidden]"
    
    return subs

@app.get("/api/v1/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def get_subscription(subscription_id: str):
    """Get a specific webhook subscription."""
    sub = await webhook_engine.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(404, f"Subscription {subscription_id} not found")
    
    sub.secret = "[hidden]"
    return sub

@app.patch("/api/v1/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest
):
    """Update an existing webhook subscription."""
    try:
        sub = await webhook_engine.update_subscription(subscription_id, request)
        sub.secret = "[hidden]"
        return sub
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.delete("/api/v1/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Delete a webhook subscription."""
    if not await webhook_engine.delete_subscription(subscription_id):
        raise HTTPException(404, f"Subscription {subscription_id} not found")
    
    return {"status": "deleted", "subscription_id": subscription_id}

@app.post("/api/v1/subscriptions/{subscription_id}/rotate-secret")
async def rotate_subscription_secret(subscription_id: str):
    """
    Rotate the secret for a subscription.
    
    Returns the new secret - store this securely!
    """
    try:
        new_secret = await webhook_engine.rotate_secret(subscription_id)
        return {
            "subscription_id": subscription_id,
            "new_secret": new_secret,
            "message": "Store this secret securely - it cannot be retrieved again"
        }
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/api/v1/subscriptions/{subscription_id}/toggle")
async def toggle_subscription(subscription_id: str):
    """Enable or disable a subscription."""
    sub = await webhook_engine.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(404, f"Subscription {subscription_id} not found")
    
    sub.active = not sub.active
    sub.updated_at = datetime.utcnow()
    
    return {
        "subscription_id": subscription_id,
        "active": sub.active
    }

# -----------------------------------------------------------------------------
# Event Publishing
# -----------------------------------------------------------------------------

@app.post("/api/v1/events")
async def publish_event(event: WebhookEvent):
    """
    Publish an event to all matching subscriptions.
    
    This endpoint is typically called by internal Nexus services.
    """
    return await webhook_engine.publish_event(event)

@app.post("/api/v1/events/batch")
async def publish_events_batch(events: List[WebhookEvent]):
    """Publish multiple events at once."""
    results = []
    for event in events:
        result = await webhook_engine.publish_event(event)
        results.append(result)
    
    return {
        "total_events": len(events),
        "results": results
    }

# -----------------------------------------------------------------------------
# Delivery Management
# -----------------------------------------------------------------------------

@app.get("/api/v1/deliveries", response_model=List[DeliveryAttempt])
async def get_delivery_history(
    subscription_id: Optional[str] = Query(None),
    event_type: Optional[EventType] = Query(None),
    status: Optional[str] = Query(None, regex="^(pending|success|failed|retrying)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get webhook delivery history."""
    return await webhook_engine.get_delivery_history(
        subscription_id, event_type, status, limit
    )

@app.get("/api/v1/deliveries/pending")
async def get_pending_retries():
    """Get all pending retry deliveries."""
    pending = await webhook_engine.get_pending_retries()
    return {
        "count": len(pending),
        "pending": [
            {
                "event_id": p.event.id,
                "event_type": p.event.type.value,
                "subscription_id": p.subscription_id,
                "attempt": p.attempt,
                "scheduled_at": p.scheduled_at.isoformat()
            }
            for p in pending
        ]
    }

@app.post("/api/v1/deliveries/{delivery_id}/retry")
async def retry_delivery(delivery_id: str):
    """Manually retry a failed delivery."""
    # Find in history
    for attempt in webhook_engine._delivery_history:
        if attempt.id == delivery_id and attempt.status == "failed":
            # Re-queue the event
            sub = await webhook_engine.get_subscription(attempt.subscription_id)
            if not sub:
                raise HTTPException(404, "Subscription not found")
            
            # Create a new event from the recorded data
            event = WebhookEvent(
                id=attempt.event_id,
                type=EventType(attempt.event_type),
                source="manual_retry",
                data=json.loads(attempt.request_body).get("data", {})
            )
            
            delivery = DeliveryQueue(
                event=event,
                subscription_id=sub.id,
                attempt=1,
                priority=1  # Higher priority for manual retries
            )
            webhook_engine._delivery_queue.append(delivery)
            
            return {"status": "queued", "delivery_id": delivery_id}
    
    raise HTTPException(404, f"Delivery {delivery_id} not found or not failed")

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

@app.post("/api/v1/test")
async def test_webhook(request: TestWebhookRequest):
    """
    Send a test webhook to verify an endpoint.
    
    Useful for validating webhook configuration before creating a subscription.
    """
    return await webhook_engine.test_webhook(request)

@app.post("/api/v1/subscriptions/{subscription_id}/test")
async def test_subscription(subscription_id: str):
    """Send a test event to a specific subscription."""
    sub = await webhook_engine.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(404, f"Subscription {subscription_id} not found")
    
    # Use first event type from subscription
    event_type = sub.events[0] if sub.events else EventType.RELEASE_STARTED
    
    return await webhook_engine.test_webhook(TestWebhookRequest(
        url=sub.url,
        secret=sub.secret,
        event_type=event_type
    ))

# -----------------------------------------------------------------------------
# Statistics & Monitoring
# -----------------------------------------------------------------------------

@app.get("/api/v1/stats", response_model=WebhookStats)
async def get_stats():
    """Get webhook service statistics."""
    return await webhook_engine.get_stats()

@app.get("/api/v1/event-types")
async def list_event_types():
    """List all available event types."""
    return {
        "event_types": [
            {
                "type": e.value,
                "category": e.value.split(".")[0],
                "description": e.name.replace("_", " ").title()
            }
            for e in EventType
        ]
    }

# -----------------------------------------------------------------------------
# Signature Verification Helper
# -----------------------------------------------------------------------------

@app.post("/api/v1/verify-signature")
async def verify_signature(
    payload: str,
    timestamp: str = Query(...),
    signature: str = Query(...),
    secret: str = Query(...)
):
    """
    Verify a webhook signature.
    
    Helper endpoint for debugging signature verification issues.
    """
    # Remove 'sha256=' prefix if present
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    is_valid = webhook_engine.verify_signature(secret, timestamp, payload, signature)
    
    return {
        "valid": is_valid,
        "timestamp": timestamp,
        "signature_provided": signature[:16] + "..."
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8007")),
        reload=os.getenv("ENV", "development") == "development"
    )


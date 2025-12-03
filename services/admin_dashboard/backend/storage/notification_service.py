"""
Notification Service for Feature Requests

Provides:
- Slack notifications
- Email notifications (via webhook)
- Webhook notifications to external systems
- Notification templates
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications"""
    SLACK = "slack"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class NotificationConfig:
    """Notification service configuration"""
    
    # Slack
    slack_enabled: bool = field(default_factory=lambda: os.getenv("NEXUS_SLACK_NOTIFY", "true").lower() == "true")
    slack_webhook_url: str = field(default_factory=lambda: os.getenv("NEXUS_SLACK_WEBHOOK", ""))
    slack_channel: str = field(default_factory=lambda: os.getenv("NEXUS_SLACK_CHANNEL", "#nexus-requests"))
    
    # External webhook
    webhook_enabled: bool = field(default_factory=lambda: os.getenv("NEXUS_WEBHOOK_NOTIFY", "false").lower() == "true")
    webhook_url: str = field(default_factory=lambda: os.getenv("NEXUS_NOTIFICATION_WEBHOOK", ""))
    webhook_secret: str = field(default_factory=lambda: os.getenv("NEXUS_WEBHOOK_SECRET", ""))
    
    # Component owners for notifications
    component_owners: Dict[str, str] = field(default_factory=lambda: {
        "orchestrator": os.getenv("NEXUS_ORCHESTRATOR_SLACK", ""),
        "jira-agent": os.getenv("NEXUS_JIRA_AGENT_SLACK", ""),
        "git-ci-agent": os.getenv("NEXUS_GIT_AGENT_SLACK", ""),
        "slack-agent": os.getenv("NEXUS_SLACK_AGENT_SLACK", ""),
        "admin-dashboard": os.getenv("NEXUS_ADMIN_SLACK", ""),
        "infrastructure": os.getenv("NEXUS_INFRA_SLACK", ""),
    })


class NotificationService:
    """
    Service for sending notifications when feature requests are submitted.
    
    Supports:
    - Slack notifications with rich formatting
    - Webhook notifications for external integrations
    - Component-based owner mentions
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # =========================================================================
    # Main Notification Methods
    # =========================================================================
    
    async def notify_new_request(
        self,
        feature_request: Dict[str, Any],
        jira_data: Optional[Dict] = None,
    ) -> Dict[str, bool]:
        """
        Send notifications for a new feature request.
        
        Returns dict of notification type -> success status.
        """
        results = {}
        
        # Slack notification
        if self.config.slack_enabled and self.config.slack_webhook_url:
            results["slack"] = await self._send_slack_notification(feature_request, jira_data)
        
        # External webhook
        if self.config.webhook_enabled and self.config.webhook_url:
            results["webhook"] = await self._send_webhook_notification(feature_request, jira_data)
        
        return results
    
    async def notify_status_change(
        self,
        feature_request: Dict[str, Any],
        old_status: str,
        new_status: str,
        changed_by: str,
    ) -> Dict[str, bool]:
        """Send notifications for status changes."""
        results = {}
        
        # Only notify on significant status changes
        significant_statuses = ["completed", "rejected", "in_progress"]
        if new_status not in significant_statuses:
            return results
        
        if self.config.slack_enabled and self.config.slack_webhook_url:
            results["slack"] = await self._send_slack_status_update(
                feature_request, old_status, new_status, changed_by
            )
        
        return results
    
    # =========================================================================
    # Slack Notifications
    # =========================================================================
    
    async def _send_slack_notification(
        self,
        feature_request: Dict,
        jira_data: Optional[Dict],
    ) -> bool:
        """Send Slack notification for new feature request."""
        try:
            client = await self._get_client()
            
            # Build Slack message
            message = self._build_slack_message(feature_request, jira_data)
            
            response = await client.post(
                self.config.slack_webhook_url,
                json=message,
            )
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent for request {feature_request.get('id')}")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _build_slack_message(
        self,
        feature_request: Dict,
        jira_data: Optional[Dict],
    ) -> Dict:
        """Build Slack Block Kit message."""
        req_type = feature_request.get("type", "feature_request")
        priority = feature_request.get("priority", "medium")
        component = feature_request.get("component")
        
        # Type emoji
        type_emojis = {
            "feature_request": "💡",
            "bug_report": "🐛",
            "improvement": "⚡",
            "documentation": "📚",
            "question": "❓",
        }
        type_emoji = type_emojis.get(req_type, "📝")
        
        # Priority emoji
        priority_emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        priority_emoji = priority_emojis.get(priority, "⚪")
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{type_emoji} New {req_type.replace('_', ' ').title()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{feature_request.get('title', 'Untitled')}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{priority_emoji} {priority.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Component:*\n{component or 'Not specified'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Submitter:*\n{feature_request.get('submitter_name', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Request ID:*\n`{feature_request.get('id', 'N/A')}`"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{self._truncate(feature_request.get('description', ''), 500)}"
                }
            },
        ]
        
        # Add Jira link if available
        if jira_data and jira_data.get("key"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Jira Ticket Created:* <{jira_data.get('url')}|{jira_data.get('key')}>"
                }
            })
        
        # Add component owner mention
        if component and component in self.config.component_owners:
            owner = self.config.component_owners[component]
            if owner:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📢 Component owner: <@{owner}>"
                        }
                    ]
                })
        
        # Action buttons
        actions = []
        
        if jira_data and jira_data.get("url"):
            actions.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "View in Jira"},
                "url": jira_data["url"],
            })
        
        actions.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "View in Dashboard"},
            "url": f"{os.getenv('NEXUS_FRONTEND_URL', 'http://localhost:5173')}/feature-requests",
        })
        
        if actions:
            blocks.append({
                "type": "actions",
                "elements": actions
            })
        
        return {
            "channel": self.config.slack_channel,
            "blocks": blocks,
            "text": f"New {req_type.replace('_', ' ')}: {feature_request.get('title', 'Untitled')}",
        }
    
    async def _send_slack_status_update(
        self,
        feature_request: Dict,
        old_status: str,
        new_status: str,
        changed_by: str,
    ) -> bool:
        """Send Slack notification for status change."""
        try:
            client = await self._get_client()
            
            # Status emojis
            status_emojis = {
                "completed": "✅",
                "rejected": "❌",
                "in_progress": "🔄",
            }
            emoji = status_emojis.get(new_status, "📝")
            
            message = {
                "channel": self.config.slack_channel,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"{emoji} *Status Update*\n\n"
                                f"*{feature_request.get('title', 'Untitled')}*\n"
                                f"Status changed: `{old_status}` → `{new_status}`\n"
                                f"Changed by: {changed_by}"
                            )
                        }
                    }
                ],
                "text": f"Status update: {feature_request.get('title', 'Untitled')} is now {new_status}",
            }
            
            response = await client.post(
                self.config.slack_webhook_url,
                json=message,
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send Slack status update: {e}")
            return False
    
    # =========================================================================
    # Webhook Notifications
    # =========================================================================
    
    async def _send_webhook_notification(
        self,
        feature_request: Dict,
        jira_data: Optional[Dict],
    ) -> bool:
        """Send webhook notification to external system."""
        try:
            client = await self._get_client()
            
            payload = {
                "event": "feature_request.created",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "feature_request": feature_request,
                    "jira": jira_data,
                },
            }
            
            headers = {
                "Content-Type": "application/json",
            }
            
            # Add signature if secret configured
            if self.config.webhook_secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    self.config.webhook_secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Nexus-Signature"] = f"sha256={signature}"
            
            response = await client.post(
                self.config.webhook_url,
                json=payload,
                headers=headers,
            )
            
            if response.status_code < 300:
                logger.info(f"Webhook notification sent for request {feature_request.get('id')}")
                return True
            else:
                logger.error(f"Webhook notification failed: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    # =========================================================================
    # Utilities
    # =========================================================================
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


# Singleton instance
_notification_service: Optional[NotificationService] = None


async def get_notification_service() -> NotificationService:
    """Get or create notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


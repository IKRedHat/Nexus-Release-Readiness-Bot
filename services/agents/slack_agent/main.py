"""
Nexus Slack Agent
Handles Slack interactions including slash commands, Block Kit modals, and notifications
"""
import os
import sys
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    TaskStatus,
    AgentType,
    SlackUser,
    SlackCommand,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import (
    setup_tracing,
    track_tool_usage,
    create_metrics_endpoint,
)
from nexus_lib.utils import AsyncHttpClient, generate_task_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.slack-agent")


# ============================================================================
# SLACK CLIENT WRAPPER
# ============================================================================

class SlackClient:
    """
    Wrapper for Slack Web API and interactions
    """
    
    def __init__(self):
        self.mock_mode = os.environ.get("SLACK_MOCK_MODE", "true").lower() == "true"
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        self.http_client = AsyncHttpClient(
            base_url="https://slack.com/api",
            headers={"Authorization": f"Bearer {self.bot_token}"} if self.bot_token else {}
        )
        
        if self.mock_mode:
            logger.info("Slack client running in MOCK mode")
        else:
            logger.info("Slack client initialized in LIVE mode")
    
    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post a message to a Slack channel"""
        if self.mock_mode:
            logger.info(f"[MOCK] Posted to {channel}: {text[:50]}...")
            return {"ok": True, "ts": "mock.ts", "channel": channel}
        
        payload = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        return await self.http_client.post("/chat.postMessage", json_body=payload)
    
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Update an existing Slack message"""
        if self.mock_mode:
            logger.info(f"[MOCK] Updated message in {channel}")
            return {"ok": True, "ts": ts, "channel": channel}
        
        payload = {
            "channel": channel,
            "ts": ts,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        
        return await self.http_client.post("/chat.update", json_body=payload)
    
    async def open_modal(
        self,
        trigger_id: str,
        view: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Open a Block Kit modal"""
        if self.mock_mode:
            logger.info(f"[MOCK] Opened modal with trigger {trigger_id}")
            return {"ok": True, "view": {"id": "mock-view-id"}}
        
        payload = {
            "trigger_id": trigger_id,
            "view": view
        }
        return await self.http_client.post("/views.open", json_body=payload)
    
    async def update_modal(
        self,
        view_id: str,
        view: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing modal"""
        if self.mock_mode:
            logger.info(f"[MOCK] Updated modal {view_id}")
            return {"ok": True, "view": {"id": view_id}}
        
        payload = {
            "view_id": view_id,
            "view": view
        }
        return await self.http_client.post("/views.update", json_body=payload)
    
    async def respond_to_slash_command(
        self,
        response_url: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        response_type: str = "in_channel"
    ) -> Dict[str, Any]:
        """Respond to a slash command via response_url"""
        if self.mock_mode:
            logger.info(f"[MOCK] Responded to command: {text[:50]}...")
            return {"ok": True}
        
        payload = {
            "text": text,
            "response_type": response_type
        }
        if blocks:
            payload["blocks"] = blocks
        
        async with AsyncHttpClient() as client:
            return await client.post(response_url, json_body=payload)
    
    async def lookup_user_by_email(self, email: str) -> Optional[str]:
        """Look up a Slack user ID by email address"""
        if self.mock_mode:
            logger.info(f"[MOCK] Looking up user by email: {email}")
            return f"U_MOCK_{email.split('@')[0].upper()}"
        
        try:
            result = await self.http_client.post(
                "/users.lookupByEmail",
                json_body={"email": email}
            )
            if result.get("ok"):
                return result.get("user", {}).get("id")
            return None
        except Exception as e:
            logger.error(f"Failed to lookup user by email {email}: {e}")
            return None
    
    async def open_dm_channel(self, user_id: str) -> Optional[str]:
        """Open a DM channel with a user"""
        if self.mock_mode:
            logger.info(f"[MOCK] Opening DM channel with user: {user_id}")
            return f"D_MOCK_{user_id}"
        
        try:
            result = await self.http_client.post(
                "/conversations.open",
                json_body={"users": user_id}
            )
            if result.get("ok"):
                return result.get("channel", {}).get("id")
            return None
        except Exception as e:
            logger.error(f"Failed to open DM channel with {user_id}: {e}")
            return None
    
    async def send_dm(
        self,
        email: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a direct message to a user by email"""
        # Look up user by email
        user_id = await self.lookup_user_by_email(email)
        if not user_id:
            return {"ok": False, "error": f"User not found for email: {email}"}
        
        # Open DM channel
        channel_id = await self.open_dm_channel(user_id)
        if not channel_id:
            return {"ok": False, "error": f"Failed to open DM channel for user: {user_id}"}
        
        # Send the message
        return await self.post_message(
            channel=channel_id,
            text=text,
            blocks=blocks
        )


# ============================================================================
# BLOCK KIT BUILDERS
# ============================================================================

class BlockKitBuilder:
    """Helper class to build Slack Block Kit components"""
    
    @staticmethod
    def header(text: str) -> Dict:
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": text, "emoji": True}
        }
    
    @staticmethod
    def section(text: str, accessory: Optional[Dict] = None) -> Dict:
        block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        }
        if accessory:
            block["accessory"] = accessory
        return block
    
    @staticmethod
    def divider() -> Dict:
        return {"type": "divider"}
    
    @staticmethod
    def context(elements: List[str]) -> Dict:
        return {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": e} for e in elements]
        }
    
    @staticmethod
    def actions(elements: List[Dict]) -> Dict:
        return {"type": "actions", "elements": elements}
    
    @staticmethod
    def button(
        text: str,
        action_id: str,
        value: str = "",
        style: Optional[str] = None
    ) -> Dict:
        btn = {
            "type": "button",
            "text": {"type": "plain_text", "text": text, "emoji": True},
            "action_id": action_id,
            "value": value
        }
        if style:
            btn["style"] = style  # "primary" or "danger"
        return btn
    
    @staticmethod
    def input_block(
        label: str,
        block_id: str,
        action_id: str,
        placeholder: str = "",
        optional: bool = False,
        multiline: bool = False
    ) -> Dict:
        return {
            "type": "input",
            "block_id": block_id,
            "optional": optional,
            "element": {
                "type": "plain_text_input",
                "action_id": action_id,
                "placeholder": {"type": "plain_text", "text": placeholder},
                "multiline": multiline
            },
            "label": {"type": "plain_text", "text": label, "emoji": True}
        }
    
    @staticmethod
    def select_block(
        label: str,
        block_id: str,
        action_id: str,
        options: List[Dict[str, str]],
        placeholder: str = "Select an option"
    ) -> Dict:
        return {
            "type": "input",
            "block_id": block_id,
            "element": {
                "type": "static_select",
                "action_id": action_id,
                "placeholder": {"type": "plain_text", "text": placeholder},
                "options": [
                    {
                        "text": {"type": "plain_text", "text": opt["text"]},
                        "value": opt["value"]
                    }
                    for opt in options
                ]
            },
            "label": {"type": "plain_text", "text": label, "emoji": True}
        }
    
    @staticmethod
    def status_message(
        title: str,
        status: str,
        details: List[str],
        decision: Optional[str] = None
    ) -> List[Dict]:
        """Build a release status message"""
        status_emoji = {
            "success": "✅",
            "failure": "❌",
            "pending": "⏳",
            "in_progress": "🔄"
        }.get(status.lower(), "ℹ️")
        
        decision_emoji = {
            "GO": "🟢 GO",
            "NO_GO": "🔴 NO-GO",
            "CONDITIONAL": "🟡 CONDITIONAL",
            "PENDING": "⚪ PENDING"
        }.get(decision, "")
        
        blocks = [
            BlockKitBuilder.header(f"{status_emoji} {title}"),
            BlockKitBuilder.divider()
        ]
        
        for detail in details:
            blocks.append(BlockKitBuilder.section(detail))
        
        if decision:
            blocks.append(BlockKitBuilder.divider())
            blocks.append(BlockKitBuilder.section(f"*Release Decision:* {decision_emoji}"))
        
        blocks.append(BlockKitBuilder.context([f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"]))
        
        return blocks


# ============================================================================
# MODAL VIEWS
# ============================================================================

def build_jira_update_modal() -> Dict:
    """Build Jira ticket update modal"""
    return {
        "type": "modal",
        "callback_id": "jira_update_submission",
        "title": {"type": "plain_text", "text": "Update Jira Ticket"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            BlockKitBuilder.input_block(
                label="Ticket Key",
                block_id="ticket_key",
                action_id="ticket_key_input",
                placeholder="e.g., PROJ-123"
            ),
            BlockKitBuilder.select_block(
                label="New Status",
                block_id="new_status",
                action_id="status_select",
                options=[
                    {"text": "To Do", "value": "To Do"},
                    {"text": "In Progress", "value": "In Progress"},
                    {"text": "In Review", "value": "In Review"},
                    {"text": "Done", "value": "Done"},
                    {"text": "Blocked", "value": "Blocked"}
                ]
            ),
            BlockKitBuilder.input_block(
                label="Comment (optional)",
                block_id="comment",
                action_id="comment_input",
                placeholder="Add a comment to the ticket...",
                optional=True,
                multiline=True
            )
        ]
    }


def build_release_check_modal() -> Dict:
    """Build release readiness check modal"""
    return {
        "type": "modal",
        "callback_id": "release_check_submission",
        "title": {"type": "plain_text", "text": "Release Readiness Check"},
        "submit": {"type": "plain_text", "text": "Run Check"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            BlockKitBuilder.section("Configure the release readiness check parameters:"),
            BlockKitBuilder.divider(),
            BlockKitBuilder.input_block(
                label="Release Version",
                block_id="release_version",
                action_id="version_input",
                placeholder="e.g., v2.0.0"
            ),
            BlockKitBuilder.input_block(
                label="Epic/Project Key",
                block_id="epic_key",
                action_id="epic_input",
                placeholder="e.g., PROJ-100"
            ),
            BlockKitBuilder.input_block(
                label="Repository",
                block_id="repo_name",
                action_id="repo_input",
                placeholder="e.g., org/repo-name"
            ),
            BlockKitBuilder.select_block(
                label="Environment",
                block_id="environment",
                action_id="env_select",
                options=[
                    {"text": "Development", "value": "dev"},
                    {"text": "Staging", "value": "staging"},
                    {"text": "Production", "value": "prod"}
                ]
            )
        ]
    }


def build_report_modal() -> Dict:
    """Build report generation modal"""
    return {
        "type": "modal",
        "callback_id": "report_submission",
        "title": {"type": "plain_text", "text": "Generate Report"},
        "submit": {"type": "plain_text", "text": "Generate"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            BlockKitBuilder.select_block(
                label="Report Type",
                block_id="report_type",
                action_id="type_select",
                options=[
                    {"text": "Release Readiness", "value": "release"},
                    {"text": "Sprint Summary", "value": "sprint"},
                    {"text": "Security Scan", "value": "security"}
                ]
            ),
            BlockKitBuilder.input_block(
                label="Release Version",
                block_id="version",
                action_id="version_input",
                placeholder="e.g., v2.0.0"
            ),
            BlockKitBuilder.input_block(
                label="Confluence Page ID (optional)",
                block_id="page_id",
                action_id="page_input",
                placeholder="Leave empty to create new page",
                optional=True
            )
        ]
    }


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

slack_client: Optional[SlackClient] = None
orchestrator_client: Optional[AsyncHttpClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global slack_client, orchestrator_client
    
    # Startup
    setup_tracing("slack-agent", service_version="1.0.0")
    slack_client = SlackClient()
    orchestrator_client = AsyncHttpClient(
        base_url=os.environ.get("ORCHESTRATOR_URL", "http://localhost:8080")
    )
    logger.info("Slack Agent started")
    
    yield
    
    # Shutdown
    await orchestrator_client.close()
    logger.info("Slack Agent shutting down")


app = FastAPI(
    title="Nexus Slack Agent",
    description="Agent for Slack interactions in the Nexus release automation system",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware, agent_type="slack")

# Add metrics endpoint
create_metrics_endpoint(app)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def forward_to_orchestrator(query: str, user_context: Dict) -> Dict:
    """Forward a request to the orchestrator"""
    request = AgentTaskRequest(
        task_id=generate_task_id("slack"),
        action="process_query",
        payload={"query": query},
        user_context=user_context
    )
    
    return await orchestrator_client.post("/execute", json_body=request.model_dump(mode="json"))


async def handle_command_async(command: str, text: str, user: Dict, channel: str, response_url: str):
    """Handle slash command asynchronously"""
    try:
        # Send initial acknowledgment
        await slack_client.respond_to_slash_command(
            response_url,
            f"🧠 Nexus is processing your request: `{text}`...",
            response_type="ephemeral"
        )
        
        # Forward to orchestrator
        result = await forward_to_orchestrator(
            f"{command} {text}",
            {
                "user_id": user.get("id", "unknown"),
                "channel_id": channel,
                "team_id": user.get("team_id", "unknown")
            }
        )
        
        # Build response blocks
        if result.get("status") == "success":
            data = result.get("data", {})
            blocks = BlockKitBuilder.status_message(
                title=f"Result for: {text}",
                status="success",
                details=[
                    f"*Plan:* {data.get('plan', 'N/A')}",
                    f"*Result:* {data.get('result', 'Completed')}",
                    f"*Steps:* {data.get('steps', 0)} iterations"
                ],
                decision=data.get("decision")
            )
        else:
            blocks = BlockKitBuilder.status_message(
                title="Request Failed",
                status="failure",
                details=[f"Error: {result.get('error', 'Unknown error')}"]
            )
        
        # Send final response
        await slack_client.post_message(
            channel=channel,
            text=f"Nexus result for: {text}",
            blocks=blocks
        )
        
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        await slack_client.respond_to_slash_command(
            response_url,
            f"❌ Error processing request: {str(e)}",
            response_type="ephemeral"
        )


# ============================================================================
# JIRA HYGIENE FIX MODAL HELPERS
# ============================================================================

async def build_hygiene_fix_modal(violation_data_json: str) -> Dict[str, Any]:
    """
    Build a Slack modal for fixing Jira ticket hygiene violations
    
    Args:
        violation_data_json: JSON string containing ticket violations
    
    Returns:
        Slack Block Kit modal view
    """
    try:
        violation_data = json.loads(violation_data_json)
    except json.JSONDecodeError:
        violation_data = {"tickets": [], "check_id": "unknown"}
    
    tickets = violation_data.get("tickets", [])
    
    # Build blocks for each ticket
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔧 Fix Jira Ticket Hygiene",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Update the missing fields for {len(tickets)} ticket(s) below. "
                        f"Fields marked with * are required for hygiene compliance."
            }
        },
        {"type": "divider"}
    ]
    
    # Add input blocks for each ticket
    for i, ticket in enumerate(tickets[:5]):  # Limit to 5 tickets per modal
        ticket_key = ticket.get("key", f"TICKET-{i}")
        missing_fields = ticket.get("missing_fields", [])
        summary = ticket.get("summary", "No summary")
        
        # Ticket header
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{ticket_key}*: {summary}\n_Missing: {', '.join(missing_fields)}_"
            }
        })
        
        # Add input for each missing field
        if "Labels" in missing_fields:
            blocks.append({
                "type": "input",
                "block_id": f"labels_{ticket_key}",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "labels_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., backend, api, security (comma-separated)"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "🏷️ Labels",
                    "emoji": True
                }
            })
        
        if "Fix Version" in missing_fields:
            blocks.append({
                "type": "input",
                "block_id": f"fixversion_{ticket_key}",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "fixversion_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., v2.0.0, 2024-Q1"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "📦 Fix Version",
                    "emoji": True
                }
            })
        
        if "Affected Version" in missing_fields:
            blocks.append({
                "type": "input",
                "block_id": f"affectedversion_{ticket_key}",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "affectedversion_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., v1.9.0"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "🔍 Affected Version",
                    "emoji": True
                }
            })
        
        if "Story Points" in missing_fields:
            blocks.append({
                "type": "input",
                "block_id": f"storypoints_{ticket_key}",
                "optional": True,
                "element": {
                    "type": "static_select",
                    "action_id": "storypoints_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select story points"
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": str(p)}, "value": str(p)}
                        for p in [1, 2, 3, 5, 8, 13, 21]
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "📊 Story Points",
                    "emoji": True
                }
            })
        
        if "Team/Contributors" in missing_fields:
            blocks.append({
                "type": "input",
                "block_id": f"team_{ticket_key}",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "team_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., Platform Team, API Team"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "👥 Team/Contributors",
                    "emoji": True
                }
            })
        
        # Add divider between tickets
        if i < len(tickets) - 1:
            blocks.append({"type": "divider"})
    
    # Build the modal view
    modal = {
        "type": "modal",
        "callback_id": "hygiene_fix_submission",
        "private_metadata": violation_data_json,
        "title": {
            "type": "plain_text",
            "text": "Fix Ticket Hygiene",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Update Tickets",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": blocks
    }
    
    return modal


async def process_hygiene_fix_submission(
    values: Dict[str, Any],
    user: Dict[str, Any],
    private_metadata: str,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Process the hygiene fix modal submission
    
    Args:
        values: Form values from the modal
        user: Slack user info
        private_metadata: Original violation data
        background_tasks: FastAPI background tasks
    
    Returns:
        Response action for Slack
    """
    try:
        violation_data = json.loads(private_metadata)
    except json.JSONDecodeError:
        violation_data = {"tickets": []}
    
    tickets = violation_data.get("tickets", [])
    updates = []
    
    # Process each ticket's field updates
    for ticket in tickets:
        ticket_key = ticket.get("key")
        if not ticket_key:
            continue
        
        update = {"ticket_key": ticket_key, "fields": {}}
        
        # Extract label values
        labels_block = values.get(f"labels_{ticket_key}", {})
        labels_value = labels_block.get("labels_input", {}).get("value")
        if labels_value:
            update["fields"]["labels"] = [l.strip() for l in labels_value.split(",")]
        
        # Extract fix version
        fixversion_block = values.get(f"fixversion_{ticket_key}", {})
        fixversion_value = fixversion_block.get("fixversion_input", {}).get("value")
        if fixversion_value:
            update["fields"]["fixVersions"] = [{"name": fixversion_value.strip()}]
        
        # Extract affected version
        affected_block = values.get(f"affectedversion_{ticket_key}", {})
        affected_value = affected_block.get("affectedversion_input", {}).get("value")
        if affected_value:
            update["fields"]["versions"] = [{"name": affected_value.strip()}]
        
        # Extract story points
        points_block = values.get(f"storypoints_{ticket_key}", {})
        points_option = points_block.get("storypoints_select", {}).get("selected_option")
        if points_option:
            update["fields"]["customfield_10016"] = float(points_option.get("value", 0))
        
        # Extract team
        team_block = values.get(f"team_{ticket_key}", {})
        team_value = team_block.get("team_input", {}).get("value")
        if team_value:
            update["fields"]["customfield_10001"] = {"name": team_value.strip()}
        
        # Only add if there are field updates
        if update["fields"]:
            updates.append(update)
    
    logger.info(f"Processing hygiene fix for {len(updates)} tickets from {user.get('username')}")
    
    # Forward updates to Jira Agent in background
    if updates:
        background_tasks.add_task(
            apply_jira_hygiene_updates,
            updates=updates,
            user=user
        )
    
    # Return response that updates the modal to show success
    return JSONResponse({
        "response_action": "update",
        "view": {
            "type": "modal",
            "callback_id": "hygiene_fix_complete",
            "title": {
                "type": "plain_text",
                "text": "Updates Submitted",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Done",
                "emoji": True
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Success!*\n\nYour updates for *{len(updates)} ticket(s)* have been submitted to Jira.\n\n"
                                f"The changes will be reflected shortly. You can close this modal."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🤖 Processed by Nexus Jira Hygiene Agent"
                        }
                    ]
                }
            ]
        }
    })


async def apply_jira_hygiene_updates(updates: List[Dict], user: Dict[str, Any]):
    """
    Apply hygiene updates to Jira tickets via the Jira Agent
    
    Args:
        updates: List of ticket updates with fields
        user: Slack user who submitted the updates
    """
    jira_agent_url = os.environ.get("JIRA_AGENT_URL", "http://jira-agent:8081")
    
    http_client = AsyncHttpClient(timeout=30)
    
    try:
        results = []
        for update in updates:
            ticket_key = update.get("ticket_key")
            fields = update.get("fields", {})
            
            if not ticket_key or not fields:
                continue
            
            try:
                # Call Jira Agent to update the ticket
                response = await http_client.post(
                    f"{jira_agent_url}/update-ticket",
                    json_body={
                        "ticket_key": ticket_key,
                        "fields": fields,
                        "updated_by": user.get("username", "unknown")
                    }
                )
                
                results.append({
                    "ticket": ticket_key,
                    "success": response.get("status") == "success",
                    "error": response.get("error_message")
                })
                
                logger.info(f"Updated {ticket_key}: {response.get('status')}")
                
            except Exception as e:
                logger.error(f"Failed to update {ticket_key}: {e}")
                results.append({
                    "ticket": ticket_key,
                    "success": False,
                    "error": str(e)
                })
        
        # Send confirmation DM to user
        success_count = sum(1 for r in results if r["success"])
        failure_count = len(results) - success_count
        
        if user.get("id"):
            channel_id = await slack_client.open_dm_channel(user["id"])
            if channel_id:
                if failure_count == 0:
                    message = f"✅ Successfully updated all {success_count} Jira ticket(s)!"
                else:
                    message = (
                        f"⚠️ Completed hygiene updates:\n"
                        f"• ✅ {success_count} ticket(s) updated successfully\n"
                        f"• ❌ {failure_count} ticket(s) failed\n\n"
                        f"Failed tickets: {', '.join(r['ticket'] for r in results if not r['success'])}"
                    )
                
                await slack_client.post_message(channel_id, message)
    
    finally:
        await http_client.close()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "slack-agent",
        "mock_mode": slack_client.mock_mode if slack_client else True
    }


@app.post("/slack/commands")
async def handle_slash_command(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Slack slash commands
    """
    form = await request.form()
    
    command = form.get("command", "")
    text = form.get("text", "")
    user_id = form.get("user_id", "")
    user_name = form.get("user_name", "")
    channel_id = form.get("channel_id", "")
    team_id = form.get("team_id", "")
    trigger_id = form.get("trigger_id", "")
    response_url = form.get("response_url", "")
    
    logger.info(f"Received command: {command} {text} from {user_name}")
    
    user = {"id": user_id, "name": user_name, "team_id": team_id}
    
    # Handle different commands
    if command == "/nexus":
        # General Nexus query - process asynchronously
        background_tasks.add_task(
            handle_command_async,
            command, text, user, channel_id, response_url
        )
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"🧠 Processing: `{text}`..."
        })
    
    elif command == "/jira-update" or (command == "/jira" and "update" in text.lower()):
        # Open Jira update modal
        await slack_client.open_modal(trigger_id, build_jira_update_modal())
        return JSONResponse({"response_type": "ephemeral", "text": ""})
    
    elif command == "/nexus-release" or (command == "/nexus" and "release" in text.lower()):
        # Open release check modal
        await slack_client.open_modal(trigger_id, build_release_check_modal())
        return JSONResponse({"response_type": "ephemeral", "text": ""})
    
    elif command == "/nexus-report" or (command == "/nexus" and "report" in text.lower()):
        # Open report modal
        await slack_client.open_modal(trigger_id, build_report_modal())
        return JSONResponse({"response_type": "ephemeral", "text": ""})
    
    elif command == "/nexus" and text.lower() in ["help", ""]:
        # Show help message
        help_blocks = [
            BlockKitBuilder.header("🤖 Nexus Release Bot - Help"),
            BlockKitBuilder.divider(),
            BlockKitBuilder.section("*Available Commands:*"),
            BlockKitBuilder.section(
                "• `/nexus status <project>` - Check release readiness status\n"
                "• `/nexus report` - Generate a release report\n"
                "• `/nexus release` - Run release readiness check\n"
                "• `/jira-update` - Update a Jira ticket\n"
                "• `/nexus help` - Show this help message"
            ),
            BlockKitBuilder.divider(),
            BlockKitBuilder.section("*Natural Language Queries:*"),
            BlockKitBuilder.section(
                "You can also ask questions like:\n"
                "• `What's the status of PROJ-123?`\n"
                "• `Is the release ready?`\n"
                "• `Show me blockers for v2.0`"
            ),
            BlockKitBuilder.context(["Powered by Nexus Multi-Agent System"])
        ]
        return JSONResponse({
            "response_type": "ephemeral",
            "blocks": help_blocks,
            "text": "Nexus Help"
        })
    
    else:
        # Forward unknown commands to orchestrator
        background_tasks.add_task(
            handle_command_async,
            command, text, user, channel_id, response_url
        )
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"🧠 Processing: `{text}`..."
        })


@app.post("/slack/interactions")
async def handle_interaction(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Slack Block Kit interactions (button clicks, modal submissions)
    """
    form = await request.form()
    payload = json.loads(form.get("payload", "{}"))
    
    interaction_type = payload.get("type")
    user = payload.get("user", {})
    trigger_id = payload.get("trigger_id")
    
    logger.info(f"Received interaction: {interaction_type} from {user.get('username')}")
    
    if interaction_type == "view_submission":
        # Modal submission
        callback_id = payload.get("view", {}).get("callback_id")
        values = payload.get("view", {}).get("state", {}).get("values", {})
        
        if callback_id == "jira_update_submission":
            # Process Jira update
            ticket_key = values.get("ticket_key", {}).get("ticket_key_input", {}).get("value", "")
            status = values.get("new_status", {}).get("status_select", {}).get("selected_option", {}).get("value", "")
            comment = values.get("comment", {}).get("comment_input", {}).get("value", "")
            
            # Forward to orchestrator
            background_tasks.add_task(
                forward_to_orchestrator,
                f"Update Jira ticket {ticket_key} to status {status}" + (f" with comment: {comment}" if comment else ""),
                {"user_id": user.get("id"), "user_name": user.get("username")}
            )
            
            return JSONResponse({"response_action": "clear"})
        
        elif callback_id == "release_check_submission":
            # Process release check
            version = values.get("release_version", {}).get("version_input", {}).get("value", "")
            epic_key = values.get("epic_key", {}).get("epic_input", {}).get("value", "")
            repo = values.get("repo_name", {}).get("repo_input", {}).get("value", "")
            env = values.get("environment", {}).get("env_select", {}).get("selected_option", {}).get("value", "")
            
            background_tasks.add_task(
                forward_to_orchestrator,
                f"Run release readiness check for version {version}, epic {epic_key}, repo {repo}, environment {env}",
                {"user_id": user.get("id"), "user_name": user.get("username")}
            )
            
            return JSONResponse({"response_action": "clear"})
        
        elif callback_id == "report_submission":
            # Process report generation
            report_type = values.get("report_type", {}).get("type_select", {}).get("selected_option", {}).get("value", "")
            version = values.get("version", {}).get("version_input", {}).get("value", "")
            page_id = values.get("page_id", {}).get("page_input", {}).get("value", "")
            
            background_tasks.add_task(
                forward_to_orchestrator,
                f"Generate {report_type} report for version {version}" + (f" to page {page_id}" if page_id else ""),
                {"user_id": user.get("id"), "user_name": user.get("username")}
            )
            
            return JSONResponse({"response_action": "clear"})
    
        elif callback_id == "hygiene_fix_submission":
            # Process hygiene fix modal submission
            result = await process_hygiene_fix_submission(
                values=values,
                user=user,
                private_metadata=payload.get("view", {}).get("private_metadata", "{}"),
                background_tasks=background_tasks
            )
            return result
    
    elif interaction_type == "block_actions":
        # Button/select actions
        actions = payload.get("actions", [])
        for action in actions:
            action_id = action.get("action_id")
            value = action.get("value")
            
            logger.info(f"Action: {action_id} = {value}")
            
            # Handle hygiene fix modal button
            if action_id == "open_hygiene_fix_modal":
                modal = await build_hygiene_fix_modal(value)
                await slack_client.open_modal(trigger_id, modal)
                return JSONResponse({"ok": True})
            
            # Handle snooze reminder
            elif action_id == "snooze_hygiene_reminder":
                try:
                    snooze_data = json.loads(value)
                    # TODO: Store snooze preference (could use Redis)
                    logger.info(f"Snoozed hygiene reminder for {snooze_data.get('assignee_email')}")
                    
                    # Update the message to acknowledge snooze
                    channel_id = payload.get("channel", {}).get("id")
                    message_ts = payload.get("message", {}).get("ts")
                    
                    if channel_id and message_ts:
                        await slack_client.update_message(
                            channel=channel_id,
                            ts=message_ts,
                            text="✅ Reminder snoozed. We'll remind you again in 24 hours.",
                            blocks=[
                                BlockKitBuilder.section("⏰ *Reminder Snoozed*\n\nWe'll remind you again in 24 hours about your Jira ticket hygiene."),
                                BlockKitBuilder.context(["🤖 Nexus Jira Hygiene Agent"])
                            ]
                        )
                except Exception as e:
                    logger.error(f"Failed to process snooze: {e}")
    
    return JSONResponse({"ok": True})


@app.post("/slack/events")
async def handle_event(request: Request):
    """
    Handle Slack Events API
    """
    body = await request.json()
    
    # Handle URL verification challenge
    if body.get("type") == "url_verification":
        return JSONResponse({"challenge": body.get("challenge")})
    
    # Handle events
    event = body.get("event", {})
    event_type = event.get("type")
    
    if event_type == "app_mention":
        # Bot was mentioned
        channel = event.get("channel")
        text = event.get("text", "")
        user = event.get("user")
        
        # Remove bot mention from text
        text = text.split(">", 1)[-1].strip() if ">" in text else text
        
        # Process the message
        asyncio.create_task(
            handle_command_async("/nexus", text, {"id": user}, channel, "")
        )
    
    elif event_type == "app_home_opened":
        # User opened the App Home tab
        user_id = event.get("user")
        logger.info(f"App Home opened by user: {user_id}")
        
        # Build and publish App Home view in background
        asyncio.create_task(
            publish_app_home(user_id)
        )
    
    return JSONResponse({"ok": True})


@app.post("/notify", response_model=AgentTaskResponse)
@track_tool_usage("send_notification", agent_type="slack")
async def send_notification(
    channel: str,
    message: str,
    blocks: Optional[List[Dict]] = None,
    thread_ts: Optional[str] = None
):
    """
    Send a notification to a Slack channel
    """
    task_id = generate_task_id("notify")
    
    try:
        result = await slack_client.post_message(
            channel=channel,
            text=message,
            blocks=blocks,
            thread_ts=thread_ts
        )
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=result,
            agent_type=AgentType.SLACK
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.SLACK
        )


from pydantic import BaseModel as PydanticBaseModel

# Import App Home builder
from app_home import AppHomeBuilder


async def publish_app_home(user_id: str):
    """
    Build and publish the App Home view for a user
    """
    try:
        builder = AppHomeBuilder()
        view = await builder.build_home_view(user_id)
        await builder.close()
        
        # Publish via Slack API
        result = await slack_client.http_client.post(
            "/views.publish",
            json_body={
                "user_id": user_id,
                "view": view
            }
        )
        
        if result.get("ok"):
            logger.info(f"Published App Home for user {user_id}")
        else:
            logger.warning(f"Failed to publish App Home: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error publishing App Home: {e}")


class SendDMRequest(PydanticBaseModel):
    """Request body for send-dm endpoint"""
    email: str
    message: str
    blocks: Optional[List[Dict]] = None


@app.post("/send-dm", response_model=AgentTaskResponse)
@track_tool_usage("send_dm", agent_type="slack")
async def send_dm(request: SendDMRequest):
    """
    Send a direct message to a user by email
    
    This endpoint is called by other agents (e.g., Jira Hygiene Agent)
    to send notifications to specific users.
    
    - **email**: The user's email address
    - **message**: The message text
    - **blocks**: Optional Block Kit blocks for rich formatting
    """
    task_id = generate_task_id("dm")
    
    try:
        result = await slack_client.send_dm(
            email=request.email,
            text=request.message,
            blocks=request.blocks
        )
        
        if result.get("ok"):
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                data={
                    "email": request.email,
                    "sent": True,
                    "channel": result.get("channel"),
                    "ts": result.get("ts")
                },
                agent_type=AgentType.SLACK
            )
        else:
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=result.get("error", "Unknown error"),
                agent_type=AgentType.SLACK
            )
            
    except Exception as e:
        logger.error(f"Failed to send DM to {request.email}: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.SLACK
        )


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Generic task execution endpoint for orchestrator integration
    """
    action = request.action
    payload = request.payload
    
    if action == "notify":
        return await send_notification(
            channel=payload.get("channel"),
            message=payload.get("message"),
            blocks=payload.get("blocks"),
            thread_ts=payload.get("thread_ts")
        )
    elif action == "send_dm":
        dm_request = SendDMRequest(
            email=payload.get("email"),
            message=payload.get("message"),
            blocks=payload.get("blocks")
        )
        return await send_dm(dm_request)
    else:
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Unknown action: {action}",
            agent_type=AgentType.SLACK
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)

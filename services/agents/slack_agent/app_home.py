"""
Slack App Home Dashboard
Provides a rich summary view with widgets when users open the Nexus app
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.utils import AsyncHttpClient

logger = logging.getLogger("nexus.slack.app_home")


class AppHomeBuilder:
    """
    Builds the Slack App Home view with summary widgets
    """
    
    def __init__(self):
        self.http_client = AsyncHttpClient(timeout=10)
    
    async def build_home_view(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build the complete App Home view for a user
        
        Args:
            user_id: Slack user ID
            user_email: User's email for Jira lookups
            project_key: Optional project to focus on
        
        Returns:
            Slack Block Kit view payload
        """
        blocks = []
        
        # Header section
        blocks.extend(self._build_header(user_id))
        
        # Quick actions section
        blocks.extend(self._build_quick_actions())
        
        # Status overview (mock data for now, would fetch from orchestrator)
        status_data = await self._fetch_status_overview(project_key)
        blocks.extend(self._build_status_overview(status_data))
        
        # Hygiene summary
        hygiene_data = await self._fetch_hygiene_summary(user_email)
        blocks.extend(self._build_hygiene_widget(hygiene_data))
        
        # Recent activity
        activity = await self._fetch_recent_activity(user_id)
        blocks.extend(self._build_activity_widget(activity))
        
        # Recommendations preview
        recommendations = await self._fetch_recommendations()
        blocks.extend(self._build_recommendations_widget(recommendations))
        
        # Footer
        blocks.extend(self._build_footer())
        
        return {
            "type": "home",
            "blocks": blocks
        }
    
    def _build_header(self, user_id: str) -> List[Dict]:
        """Build the header section"""
        now = datetime.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 Nexus Release Automation",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{greeting}! Here's your release management dashboard."
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {now.strftime('%A, %B %d, %Y')} | Last updated: {now.strftime('%I:%M %p')}"
                    }
                ]
            },
            {"type": "divider"}
        ]
    
    def _build_quick_actions(self) -> List[Dict]:
        """Build quick action buttons"""
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*⚡ Quick Actions*"
                }
            },
            {
                "type": "actions",
                "block_id": "quick_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 Release Status",
                            "emoji": True
                        },
                        "action_id": "quick_release_status",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔧 Run Hygiene Check",
                            "emoji": True
                        },
                        "action_id": "quick_hygiene_check"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📝 Generate Report",
                            "emoji": True
                        },
                        "action_id": "quick_generate_report"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❓ Help",
                            "emoji": True
                        },
                        "action_id": "quick_help"
                    }
                ]
            },
            {"type": "divider"}
        ]
    
    def _build_status_overview(self, data: Dict[str, Any]) -> List[Dict]:
        """Build the release status overview widget"""
        # Determine status color and emoji
        decision = data.get("decision", "PENDING")
        status_config = {
            "GO": {"emoji": "🟢", "color": "#28a745"},
            "NO_GO": {"emoji": "🔴", "color": "#dc3545"},
            "CONDITIONAL": {"emoji": "🟡", "color": "#ffc107"},
            "PENDING": {"emoji": "⚪", "color": "#6c757d"},
        }
        config = status_config.get(decision, status_config["PENDING"])
        
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📈 Release Status Overview*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Release:*\n{data.get('version', 'v2.0.0')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Decision:*\n{config['emoji']} {decision}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticket Completion:*\n{data.get('completion_rate', 85)}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Build Status:*\n{'✅' if data.get('build_passing', True) else '❌'} {'Passing' if data.get('build_passing', True) else 'Failing'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Security Score:*\n{data.get('security_score', 85)}/100"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Active Blockers:*\n{data.get('blockers', 0)}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Target date: {data.get('target_date', 'Not set')}_"
                    }
                ]
            },
            {"type": "divider"}
        ]
    
    def _build_hygiene_widget(self, data: Dict[str, Any]) -> List[Dict]:
        """Build the hygiene score widget"""
        score = data.get("score", 0)
        
        # Determine score color
        if score >= 90:
            score_indicator = "🟢"
            score_text = "Excellent"
        elif score >= 70:
            score_indicator = "🟡"
            score_text = "Good"
        elif score >= 50:
            score_indicator = "🟠"
            score_text = "Needs Improvement"
        else:
            score_indicator = "🔴"
            score_text = "Critical"
        
        # Build progress bar
        filled = int(score / 10)
        empty = 10 - filled
        progress_bar = "█" * filled + "░" * empty
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 Jira Hygiene*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Details",
                        "emoji": True
                    },
                    "action_id": "view_hygiene_details"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{score_indicator} *{score:.0f}%* - {score_text}\n`{progress_bar}`"
                }
            }
        ]
        
        # Add violations if any
        your_violations = data.get("your_violations", 0)
        if your_violations > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ You have *{your_violations} ticket(s)* needing attention"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Fix Now",
                        "emoji": True
                    },
                    "action_id": "fix_my_hygiene_issues",
                    "style": "primary"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _build_activity_widget(self, activities: List[Dict]) -> List[Dict]:
        """Build the recent activity widget"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 Recent Activity*"
                }
            }
        ]
        
        if not activities:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No recent activity_"
                }
            })
        else:
            activity_lines = []
            for activity in activities[:5]:
                icon = activity.get("icon", "•")
                text = activity.get("text", "")
                time = activity.get("time", "")
                activity_lines.append(f"{icon} {text} _({time})_")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(activity_lines)
                }
            })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _build_recommendations_widget(self, recommendations: List[Dict]) -> List[Dict]:
        """Build the AI recommendations widget"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💡 AI Recommendations*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View All",
                        "emoji": True
                    },
                    "action_id": "view_all_recommendations"
                }
            }
        ]
        
        if not recommendations:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✨ _No recommendations at this time. Everything looks good!_"
                }
            })
        else:
            for rec in recommendations[:3]:
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "ℹ️",
                }.get(rec.get("priority", "info"), "ℹ️")
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{priority_emoji} *{rec.get('title', 'Recommendation')}*\n{rec.get('description', '')[:100]}..."
                    }
                })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _build_footer(self) -> List[Dict]:
        """Build the footer section"""
        return [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🤖 Powered by Nexus Release Automation | <https://github.com/IKRedHat/Nexus-Release-Readiness-Bot|GitHub> | `/nexus help` for commands"
                    }
                ]
            }
        ]
    
    async def _fetch_status_overview(self, project_key: Optional[str]) -> Dict[str, Any]:
        """Fetch release status data (mock for now)"""
        # TODO: Fetch real data from orchestrator
        return {
            "version": "v2.0.0",
            "decision": "CONDITIONAL",
            "completion_rate": 87,
            "build_passing": True,
            "security_score": 75,
            "blockers": 2,
            "target_date": "Dec 15, 2025",
        }
    
    async def _fetch_hygiene_summary(self, user_email: Optional[str]) -> Dict[str, Any]:
        """Fetch hygiene data (mock for now)"""
        # TODO: Fetch real data from hygiene agent
        return {
            "score": 78,
            "your_violations": 3,
            "total_violations": 12,
        }
    
    async def _fetch_recent_activity(self, user_id: str) -> List[Dict]:
        """Fetch recent activity (mock for now)"""
        # TODO: Fetch real activity from memory/logs
        return [
            {"icon": "✅", "text": "Release readiness check completed", "time": "2h ago"},
            {"icon": "🔧", "text": "Fixed 2 hygiene violations", "time": "5h ago"},
            {"icon": "📝", "text": "Generated v1.9 release report", "time": "1d ago"},
            {"icon": "🔍", "text": "Security scan completed", "time": "2d ago"},
        ]
    
    async def _fetch_recommendations(self) -> List[Dict]:
        """Fetch AI recommendations (mock for now)"""
        # TODO: Fetch real recommendations from recommendation engine
        return [
            {
                "priority": "high",
                "title": "Address blocking issues before release",
                "description": "2 blocking issues need resolution to proceed with the v2.0 release.",
            },
            {
                "priority": "medium",
                "title": "Improve hygiene score to 90%+",
                "description": "Current score of 78% is below target. 5 tickets need field updates.",
            },
            {
                "priority": "low",
                "title": "Consider releasing mid-week",
                "description": "Historical data shows Tuesday releases have 40% lower incident rates.",
            },
        ]
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.close()


async def handle_app_home_opened(
    client,
    event: Dict[str, Any],
    logger
):
    """
    Handle the app_home_opened event
    
    This is called when a user opens the Nexus app in Slack
    """
    user_id = event.get("user")
    
    try:
        # Build the home view
        builder = AppHomeBuilder()
        view = await builder.build_home_view(user_id)
        await builder.close()
        
        # Publish the view
        await client.views_publish(
            user_id=user_id,
            view=view
        )
        
        logger.info(f"Published App Home view for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish App Home view: {e}")
        
        # Publish error view
        error_view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ *Error loading dashboard*\n\nPlease try again in a few moments."
                    }
                }
            ]
        }
        
        try:
            await client.views_publish(user_id=user_id, view=error_view)
        except:
            pass


async def handle_app_home_action(
    ack,
    action: Dict[str, Any],
    client,
    body: Dict[str, Any],
    logger
):
    """
    Handle button clicks from the App Home
    """
    await ack()
    
    action_id = action.get("action_id")
    user_id = body.get("user", {}).get("id")
    trigger_id = body.get("trigger_id")
    
    logger.info(f"App Home action: {action_id} from user {user_id}")
    
    if action_id == "quick_release_status":
        # Open release status modal
        await client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Release Status"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Enter a project or version to check status.\n\nOr use `/nexus status <version>` in any channel."
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "project_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "project_value",
                            "placeholder": {"type": "plain_text", "text": "e.g., PROJ or v2.0.0"}
                        },
                        "label": {"type": "plain_text", "text": "Project/Version"}
                    }
                ],
                "submit": {"type": "plain_text", "text": "Check Status"}
            }
        )
    
    elif action_id == "quick_hygiene_check":
        # Trigger hygiene check
        await client.chat_postMessage(
            channel=user_id,
            text="🔧 Running hygiene check... I'll send you the results shortly!"
        )
        # TODO: Actually trigger hygiene check
    
    elif action_id == "quick_generate_report":
        # Open report generation modal
        await client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Generate Report"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "submit": {"type": "plain_text", "text": "Generate"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "report_version",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "version_value",
                            "placeholder": {"type": "plain_text", "text": "e.g., v2.0.0"}
                        },
                        "label": {"type": "plain_text", "text": "Release Version"}
                    },
                    {
                        "type": "input",
                        "block_id": "report_type",
                        "element": {
                            "type": "static_select",
                            "action_id": "type_value",
                            "options": [
                                {"text": {"type": "plain_text", "text": "Release Readiness"}, "value": "readiness"},
                                {"text": {"type": "plain_text", "text": "Sprint Summary"}, "value": "sprint"},
                                {"text": {"type": "plain_text", "text": "Security Report"}, "value": "security"},
                            ]
                        },
                        "label": {"type": "plain_text", "text": "Report Type"}
                    }
                ]
            }
        )
    
    elif action_id == "quick_help":
        # Send help message
        await client.chat_postMessage(
            channel=user_id,
            text="📚 *Nexus Help*\n\nHere are the available commands:\n\n"
                 "• `/nexus status <version>` - Check release readiness\n"
                 "• `/nexus ticket <key>` - Get ticket details\n"
                 "• `/nexus blockers` - List blocking issues\n"
                 "• `/nexus report` - Generate a report\n"
                 "• `/jira-update` - Update a Jira ticket\n"
                 "• `/nexus help` - Show this help\n\n"
                 "You can also ask questions in natural language!"
        )
    
    elif action_id == "fix_my_hygiene_issues":
        # TODO: Open hygiene fix modal for user's tickets
        await client.chat_postMessage(
            channel=user_id,
            text="🔧 Opening hygiene fix interface..."
        )
    
    elif action_id == "view_all_recommendations":
        # Send full recommendations
        await client.chat_postMessage(
            channel=user_id,
            text="💡 *AI Recommendations*\n\n"
                 "Use `/nexus recommendations` to see all AI-powered suggestions for improving your release process."
        )


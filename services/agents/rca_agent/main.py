"""
Nexus RCA (Root Cause Analysis) Agent
=====================================

Specialized agent for analyzing failed builds to determine:
- Why the build failed
- Which commit/code change caused it
- Suggested fixes

Features:
- Auto-triggers on build failures via Jenkins webhook
- Sends Slack notifications to release channel
- Tags PR owner in notifications

Uses LLM (Google Gemini) to correlate error logs with git diffs.

Now with dynamic configuration via ConfigManager - supports live mode switching from Admin Dashboard.

Author: Nexus Team
Version: 2.3.0
"""

import asyncio
import logging
import os
import sys
import re
import time
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.config import ConfigManager, ConfigKeys, is_mock_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """
    RCA Agent configuration.
    
    Now uses ConfigManager for dynamic configuration.
    Mode can be switched live via Admin Dashboard.
    """
    # Analysis settings (static, not dynamically configured)
    MAX_LOG_CHARS = int(os.getenv("RCA_MAX_LOG_CHARS", "100000"))
    MAX_DIFF_CHARS = int(os.getenv("RCA_MAX_DIFF_CHARS", "50000"))
    
    # Service settings
    PORT = int(os.getenv("PORT", "8006"))
    WEBHOOK_SECRET = os.getenv("RCA_WEBHOOK_SECRET", "")
    
    # Defaults (used as fallback)
    DEFAULT_SLACK_CHANNEL = "#release-notifications"
    DEFAULT_LLM_MODEL = "gemini-1.5-pro"
    
    @classmethod
    async def get_jenkins_url(cls) -> str:
        return await ConfigManager.get(ConfigKeys.JENKINS_URL) or "http://jenkins:8080"
    
    @classmethod
    async def get_jenkins_username(cls) -> str:
        return await ConfigManager.get(ConfigKeys.JENKINS_USERNAME) or ""
    
    @classmethod
    async def get_jenkins_token(cls) -> str:
        return await ConfigManager.get(ConfigKeys.JENKINS_API_TOKEN) or ""
    
    @classmethod
    async def get_github_token(cls) -> str:
        return await ConfigManager.get(ConfigKeys.GITHUB_TOKEN) or ""
    
    @classmethod
    async def get_github_org(cls) -> str:
        return await ConfigManager.get(ConfigKeys.GITHUB_ORG) or ""
    
    @classmethod
    async def get_gemini_api_key(cls) -> str:
        return await ConfigManager.get(ConfigKeys.GEMINI_API_KEY) or ""
    
    @classmethod
    async def get_llm_model(cls) -> str:
        return await ConfigManager.get(ConfigKeys.LLM_MODEL) or cls.DEFAULT_LLM_MODEL
    
    @classmethod
    async def get_slack_agent_url(cls) -> str:
        return await ConfigManager.get(ConfigKeys.SLACK_AGENT_URL) or "http://slack-agent:8084"
    
    @classmethod
    async def get_slack_channel(cls) -> str:
        return os.getenv("SLACK_RELEASE_CHANNEL", cls.DEFAULT_SLACK_CHANNEL)
    
    @classmethod
    async def is_mock_mode(cls) -> bool:
        return await is_mock_mode()
    
    @classmethod
    async def notify_on_failure(cls) -> bool:
        return os.getenv("SLACK_NOTIFY_ON_FAILURE", "true").lower() == "true"
    
    @classmethod
    async def auto_analyze_enabled(cls) -> bool:
        return os.getenv("RCA_AUTO_ANALYZE", "true").lower() == "true"
    
    # Backward compatibility properties for static access (reads env vars)
    JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins:8080")
    JENKINS_USERNAME = os.getenv("JENKINS_USERNAME", "")
    JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
    JENKINS_MOCK_MODE = os.getenv("JENKINS_MOCK_MODE", "true").lower() == "true"
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_ORG = os.getenv("GITHUB_ORG", "")
    GITHUB_MOCK_MODE = os.getenv("GITHUB_MOCK_MODE", "true").lower() == "true"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    LLM_MODEL = os.getenv("RCA_LLM_MODEL", "gemini-1.5-pro")
    LLM_MOCK_MODE = os.getenv("LLM_MOCK_MODE", "true").lower() == "true"
    SLACK_AGENT_URL = os.getenv("SLACK_AGENT_URL", "http://slack-agent:8084")
    SLACK_RELEASE_CHANNEL = os.getenv("SLACK_RELEASE_CHANNEL", "#release-notifications")
    SLACK_NOTIFY_ON_FAILURE = os.getenv("SLACK_NOTIFY_ON_FAILURE", "true").lower() == "true"
    SLACK_MOCK_MODE = os.getenv("SLACK_MOCK_MODE", "true").lower() == "true"
    AUTO_ANALYZE_ENABLED = os.getenv("RCA_AUTO_ANALYZE", "true").lower() == "true"

# =============================================================================
# Prometheus Metrics
# =============================================================================

RCA_REQUESTS = Counter(
    "nexus_rca_requests_total",
    "Total RCA analysis requests",
    ["status", "error_type", "trigger"]  # trigger: manual, webhook, auto
)
RCA_DURATION = Histogram(
    "nexus_rca_duration_seconds",
    "RCA analysis duration",
    ["job_name"]
)
RCA_CONFIDENCE = Histogram(
    "nexus_rca_confidence_score",
    "Distribution of RCA confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)
LLM_TOKENS_RCA = Counter(
    "nexus_llm_tokens_total",
    "LLM tokens used for RCA",
    ["model", "task_type"]
)
ACTIVE_ANALYSES = Gauge(
    "nexus_rca_active_analyses",
    "Number of RCA analyses currently running"
)
RCA_WEBHOOKS = Counter(
    "nexus_rca_webhooks_total",
    "Total Jenkins webhooks received",
    ["job_name", "status"]
)
RCA_NOTIFICATIONS = Counter(
    "nexus_rca_notifications_total",
    "Total Slack notifications sent",
    ["channel", "status"]
)


def track_llm_usage(task_type: str = "rca"):
    """Decorator to track LLM usage for RCA tasks."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # Extract token usage if available
                if isinstance(result, dict) and "tokens_used" in result:
                    LLM_TOKENS_RCA.labels(
                        model=Config.LLM_MODEL,
                        task_type=task_type
                    ).inc(result["tokens_used"])
                
                return result
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"LLM call ({task_type}) took {duration:.2f}s")
        return wrapper
    return decorator


# =============================================================================
# Pydantic Models (local copies for request/response)
# =============================================================================

class RcaRequest(BaseModel):
    """Request for Root Cause Analysis."""
    job_name: str
    build_number: int
    build_url: Optional[str] = None
    repo_name: Optional[str] = None
    branch: Optional[str] = None
    pr_id: Optional[int] = None
    commit_sha: Optional[str] = None
    include_git_diff: bool = True
    include_test_output: bool = True
    max_log_lines: int = 5000


class RcaFileChange(BaseModel):
    """File that may have caused the issue."""
    file_path: str
    change_type: str
    lines_added: int = 0
    lines_deleted: int = 0
    relevant_lines: Optional[List[int]] = None
    code_snippet: Optional[str] = None


class RcaTestFailure(BaseModel):
    """Test failure details."""
    test_name: str
    test_class: Optional[str] = None
    error_message: str
    stack_trace: Optional[str] = None


class RcaAnalysis(BaseModel):
    """RCA Analysis result."""
    analysis_id: str
    root_cause_summary: str
    error_type: str
    error_message: str
    confidence_score: float
    confidence_level: str
    suspected_commit: Optional[str] = None
    suspected_author: Optional[str] = None
    suspected_files: List[RcaFileChange] = []
    test_failures: List[RcaTestFailure] = []
    error_log_excerpt: str = ""
    fix_suggestion: str
    fix_code_snippet: Optional[str] = None
    # Notification tracking
    notification_sent: bool = False
    notification_channel: Optional[str] = None
    pr_owner_tagged: Optional[str] = None


class JenkinsWebhookPayload(BaseModel):
    """Jenkins Generic Webhook Trigger payload."""
    job_name: str = Field(..., alias="name")
    build_number: int = Field(..., alias="number")
    build_url: Optional[str] = Field(None, alias="url")
    build_result: str = Field(..., alias="result")  # SUCCESS, FAILURE, UNSTABLE, ABORTED
    
    # Git/SCM info (if available)
    git_url: Optional[str] = None
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    
    # PR info (if available)
    pr_number: Optional[int] = None
    pr_author: Optional[str] = None
    pr_author_email: Optional[str] = None
    
    # Custom fields
    project_key: Optional[str] = None
    release_channel: Optional[str] = None
    
    class Config:
        populate_by_name = True


class SlackRcaNotification(BaseModel):
    """Slack notification for RCA results."""
    channel: str
    analysis: RcaAnalysis
    pr_owner_slack_id: Optional[str] = None
    additional_mentions: List[str] = []


# =============================================================================
# Slack Notification Client
# =============================================================================

class SlackNotificationClient:
    """Client for sending RCA notifications to Slack."""
    
    def __init__(self):
        self.mock_mode = Config.SLACK_MOCK_MODE
        self.slack_agent_url = Config.SLACK_AGENT_URL
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    async def lookup_user_by_email(self, email: str) -> Optional[str]:
        """Look up Slack user ID by email address."""
        if self.mock_mode:
            logger.info(f"[MOCK] Looking up Slack user for email: {email}")
            return f"U{email.split('@')[0].upper()[:8]}"  # Mock user ID
        
        try:
            response = await self.http_client.post(
                f"{self.slack_agent_url}/lookup-user",
                json={"email": email}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("user_id")
        except Exception as e:
            logger.warning(f"Failed to lookup Slack user: {e}")
        
        return None
    
    async def send_rca_notification(
        self,
        analysis: "RcaAnalysis",
        channel: str,
        pr_owner_email: Optional[str] = None,
        build_url: Optional[str] = None
    ) -> bool:
        """
        Send RCA analysis result to Slack channel with PR owner mention.
        
        Args:
            analysis: The RCA analysis result
            channel: Slack channel to post to
            pr_owner_email: Email of the PR owner to tag
            build_url: URL to the failed build
        
        Returns:
            True if notification was sent successfully
        """
        # Look up PR owner's Slack ID
        pr_owner_slack_id = None
        if pr_owner_email:
            pr_owner_slack_id = await self.lookup_user_by_email(pr_owner_email)
        
        # Build the notification blocks
        blocks = self._build_rca_blocks(analysis, pr_owner_slack_id, build_url)
        
        if self.mock_mode:
            logger.info(f"[MOCK] Would send RCA notification to {channel}")
            logger.info(f"[MOCK] PR Owner: {pr_owner_email} -> {pr_owner_slack_id}")
            logger.info(f"[MOCK] Summary: {analysis.root_cause_summary[:100]}...")
            RCA_NOTIFICATIONS.labels(channel=channel, status="mock").inc()
            return True
        
        try:
            # Send to Slack agent
            response = await self.http_client.post(
                f"{self.slack_agent_url}/notify",
                json={
                    "channel": channel,
                    "text": f"🔍 RCA Alert: Build failure in {analysis.analysis_id}",
                    "blocks": blocks
                }
            )
            
            if response.status_code == 200:
                RCA_NOTIFICATIONS.labels(channel=channel, status="success").inc()
                logger.info(f"RCA notification sent to {channel}")
                return True
            else:
                RCA_NOTIFICATIONS.labels(channel=channel, status="error").inc()
                logger.error(f"Failed to send notification: {response.status_code}")
                return False
                
        except Exception as e:
            RCA_NOTIFICATIONS.labels(channel=channel, status="error").inc()
            logger.error(f"Failed to send RCA notification: {e}")
            return False
    
    def _build_rca_blocks(
        self,
        analysis: "RcaAnalysis",
        pr_owner_slack_id: Optional[str],
        build_url: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Build Slack Block Kit blocks for RCA notification."""
        
        # Confidence emoji
        conf_emoji = "🟢" if analysis.confidence_level == "high" else "🟡" if analysis.confidence_level == "medium" else "🔴"
        
        # Error type emoji
        error_emoji = {
            "test_failure": "🧪",
            "compilation_error": "🔧",
            "dependency_error": "📦",
            "configuration_error": "⚙️",
            "infrastructure_error": "🏗️",
            "timeout_error": "⏱️",
        }.get(analysis.error_type, "❓")
        
        # Build mention string
        mention = f"<@{pr_owner_slack_id}>" if pr_owner_slack_id else ""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 Build Failure Analysis",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Analysis ID:* `{analysis.analysis_id}`\n"
                            f"*Build:* {build_url or 'N/A'}\n"
                            f"*Analyzed:* {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{error_emoji} *Error Type:* {analysis.error_type.replace('_', ' ').title()}\n\n"
                            f"*Root Cause:*\n{analysis.root_cause_summary}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"{conf_emoji} *Confidence:* {analysis.confidence_score:.0%} ({analysis.confidence_level})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Suspected Author:* {mention or analysis.suspected_author or 'Unknown'}"
                    }
                ]
            }
        ]
        
        # Add suspected files
        if analysis.suspected_files:
            files_text = "\n".join([
                f"• `{f.file_path}` (lines: {f.relevant_lines or 'N/A'})"
                for f in analysis.suspected_files[:3]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📁 Suspected Files:*\n{files_text}"
                }
            })
        
        # Add fix suggestion
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💡 Suggested Fix:*\n{analysis.fix_suggestion[:500]}{'...' if len(analysis.fix_suggestion) > 500 else ''}"
            }
        })
        
        # Add code snippet if available
        if analysis.fix_code_snippet:
            snippet = analysis.fix_code_snippet[:300]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{snippet}{'...' if len(analysis.fix_code_snippet) > 300 else ''}```"
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📋 View Full Analysis", "emoji": True},
                    "url": f"http://rca-agent:8006/analysis/{analysis.analysis_id}",
                    "action_id": "view_rca_analysis"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Re-run Analysis", "emoji": True},
                    "action_id": "rerun_rca_analysis",
                    "value": analysis.analysis_id
                }
            ]
        })
        
        # Add footer with recommendations
        if analysis.additional_recommendations:
            recs = " | ".join(analysis.additional_recommendations[:3])
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💡 _Additional: {recs}_"
                    }
                ]
            })
        
        return blocks


# =============================================================================
# Jenkins Client
# =============================================================================

class JenkinsClient:
    """Client for fetching Jenkins build information and console logs."""
    
    def __init__(self):
        self.mock_mode = Config.JENKINS_MOCK_MODE
        self._client = None
        
        if not self.mock_mode:
            try:
                import jenkins
                self._client = jenkins.Jenkins(
                    Config.JENKINS_URL,
                    username=Config.JENKINS_USERNAME,
                    password=Config.JENKINS_API_TOKEN
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Jenkins client: {e}")
                self.mock_mode = True
    
    async def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get build information."""
        if self.mock_mode:
            return self._mock_build_info(job_name, build_number)
        
        try:
            info = self._client.get_build_info(job_name, build_number)
            return {
                "job_name": job_name,
                "build_number": build_number,
                "result": info.get("result", "UNKNOWN"),
                "url": info.get("url", ""),
                "timestamp": info.get("timestamp", 0),
                "duration": info.get("duration", 0),
                "building": info.get("building", False),
                "actions": info.get("actions", [])
            }
        except Exception as e:
            logger.error(f"Failed to get build info: {e}")
            raise
    
    async def get_console_output(self, job_name: str, build_number: int) -> str:
        """Get console output/logs from a build."""
        if self.mock_mode:
            return self._mock_console_output(job_name, build_number)
        
        try:
            output = self._client.get_build_console_output(job_name, build_number)
            return output
        except Exception as e:
            logger.error(f"Failed to get console output: {e}")
            raise
    
    def _mock_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Generate mock build info for testing."""
        return {
            "job_name": job_name,
            "build_number": build_number,
            "result": "FAILURE",
            "url": f"http://jenkins:8080/job/{job_name}/{build_number}/",
            "timestamp": int(time.time() * 1000),
            "duration": 125000,
            "building": False,
            "culprits": [{"fullName": "developer@example.com"}],
            "changeSet": {
                "items": [
                    {
                        "commitId": "a1b2c3d4e5f6789",
                        "author": {"fullName": "developer@example.com"},
                        "msg": "feat: add new user validation",
                        "paths": [
                            {"editType": "edit", "file": "src/api/users.py"},
                            {"editType": "add", "file": "tests/test_users.py"}
                        ]
                    }
                ]
            }
        }
    
    def _mock_console_output(self, job_name: str, build_number: int) -> str:
        """Generate mock console output with realistic error patterns."""
        return """Started by user admin
Building in workspace /var/jenkins_home/workspace/nexus-pipeline
Cloning repository https://github.com/example/nexus-backend.git
Checking out Revision a1b2c3d4e5f6789 (refs/remotes/origin/main)
 > git checkout -f a1b2c3d4e5f6789
Commit message: "feat: add new user validation"

[Pipeline] stage
[Pipeline] { (Build)
[Pipeline] sh
+ python -m pip install -r requirements.txt
Successfully installed all dependencies

[Pipeline] stage  
[Pipeline] { (Test)
[Pipeline] sh
+ python -m pytest tests/ -v

============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.0
collected 45 items

tests/test_auth.py::TestAuth::test_login PASSED                          [  2%]
tests/test_auth.py::TestAuth::test_logout PASSED                         [  4%]
tests/test_users.py::TestUserService::test_create_user PASSED            [  6%]
tests/test_users.py::TestUserService::test_get_user PASSED               [  9%]
tests/test_users.py::TestUserService::test_validate_email FAILED         [ 11%]

=================================== FAILURES ===================================
_________________________ TestUserService.test_validate_email __________________________

self = <tests.test_users.TestUserService object at 0x7f8b8c0d5a90>

    def test_validate_email(self):
        \"\"\"Test email validation for new users.\"\"\"
        user_service = UserService()
        
        # Test with valid email
        result = user_service.validate_user_email("test@example.com")
>       assert result.is_valid == True
E       AttributeError: 'NoneType' object has no attribute 'is_valid'

tests/test_users.py:42: AttributeError
----------------------------- Captured log call -------------------------------
ERROR    src.api.users:users.py:87 Failed to validate email: test@example.com
=========================== short test summary info ============================
FAILED tests/test_users.py::TestUserService::test_validate_email - AttributeError: 'NoneType' object has no attribute 'is_valid'
============================= 1 failed, 44 passed in 12.34s ====================

[Pipeline] }
[Pipeline] // stage
[Pipeline] }
[Pipeline] // node
[Pipeline] End of Pipeline
ERROR: script returned exit code 1
Finished: FAILURE
"""


# =============================================================================
# GitHub Client
# =============================================================================

class GitHubClient:
    """Client for fetching GitHub commit and diff information."""
    
    def __init__(self):
        self.mock_mode = Config.GITHUB_MOCK_MODE
        self._github = None
        
        if not self.mock_mode and Config.GITHUB_TOKEN:
            try:
                from github import Github
                self._github = Github(Config.GITHUB_TOKEN)
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub client: {e}")
                self.mock_mode = True
    
    async def get_commit_diff(
        self, 
        repo_name: str, 
        commit_sha: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Get the diff for a specific commit."""
        if self.mock_mode:
            return self._mock_commit_diff(repo_name, commit_sha)
        
        try:
            repo = self._github.get_repo(f"{Config.GITHUB_ORG}/{repo_name}")
            commit = repo.get_commit(commit_sha)
            
            files = []
            diff_text = []
            
            for file in commit.files:
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch or ""
                })
                if file.patch:
                    diff_text.append(f"=== {file.filename} ===\n{file.patch}")
            
            return "\n\n".join(diff_text), files
            
        except Exception as e:
            logger.error(f"Failed to get commit diff: {e}")
            raise
    
    async def get_pr_diff(self, repo_name: str, pr_number: int) -> Tuple[str, List[Dict[str, Any]]]:
        """Get the diff for a pull request."""
        if self.mock_mode:
            return self._mock_commit_diff(repo_name, f"pr-{pr_number}")
        
        try:
            repo = self._github.get_repo(f"{Config.GITHUB_ORG}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            files = []
            diff_text = []
            
            for file in pr.get_files():
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch or ""
                })
                if file.patch:
                    diff_text.append(f"=== {file.filename} ===\n{file.patch}")
            
            return "\n\n".join(diff_text), files
            
        except Exception as e:
            logger.error(f"Failed to get PR diff: {e}")
            raise
    
    def _mock_commit_diff(self, repo_name: str, ref: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate mock commit diff for testing."""
        diff_text = """=== src/api/users.py ===
@@ -82,10 +82,15 @@ class UserService:
     def validate_user_email(self, email: str) -> Optional[ValidationResult]:
         \"\"\"Validate a user's email address.\"\"\"
+        if not email:
+            logger.error(f"Failed to validate email: {email}")
+            return None
+        
         try:
             # Check email format
             if not self._is_valid_email_format(email):
-                return ValidationResult(is_valid=False, error="Invalid format")
+                logger.error(f"Failed to validate email: {email}")
+                return None
             
             # Check if email already exists
             if self._email_exists(email):

=== tests/test_users.py ===
@@ -38,6 +38,10 @@ class TestUserService:
     def test_validate_email(self):
         \"\"\"Test email validation for new users.\"\"\"
         user_service = UserService()
         
         # Test with valid email
         result = user_service.validate_user_email("test@example.com")
+        assert result.is_valid == True
+        
+        # Test with invalid email
+        result = user_service.validate_user_email("")
         assert result.is_valid == True
"""
        files = [
            {
                "filename": "src/api/users.py",
                "status": "modified",
                "additions": 6,
                "deletions": 1,
                "patch": diff_text.split("=== tests/test_users.py ===")[0]
            },
            {
                "filename": "tests/test_users.py", 
                "status": "modified",
                "additions": 4,
                "deletions": 0,
                "patch": "=== tests/test_users.py ===" + diff_text.split("=== tests/test_users.py ===")[1]
            }
        ]
        
        return diff_text, files


# =============================================================================
# LLM Client for RCA
# =============================================================================

class RcaLLMClient:
    """LLM client specialized for Root Cause Analysis."""
    
    SYSTEM_PROMPT = """You are a Senior DevOps Debugger and Root Cause Analysis expert. Your task is to analyze build failures by correlating error logs with code changes.

Given:
1. **Build Console Output**: The full or truncated log from a failed CI/CD build
2. **Git Diff**: The code changes that were part of this build

Your analysis should:
1. **Identify the Root Cause**: Pinpoint the exact error and why it occurred
2. **Map to Code Changes**: Correlate the error to specific lines in the provided diffs
3. **Suggest a Fix**: Provide a concrete code fix

Response Format (JSON):
{
    "root_cause_summary": "Brief 1-2 sentence summary of what went wrong",
    "error_type": "One of: compilation_error, test_failure, dependency_error, configuration_error, infrastructure_error, timeout_error, unknown",
    "error_message": "The primary error message from logs",
    "suspected_file": "Path to the file most likely causing the issue",
    "suspected_lines": [line_numbers],
    "confidence_score": 0.0-1.0,
    "fix_suggestion": "Detailed explanation of how to fix the issue",
    "fix_code_snippet": "Actual code fix if applicable",
    "additional_recommendations": ["List of other suggestions"]
}

Important:
- Be specific about file paths and line numbers
- If you're unsure, indicate lower confidence
- Focus on actionable fixes
- Consider both the error logs AND the code changes together"""

    def __init__(self):
        self.mock_mode = Config.LLM_MOCK_MODE
        self._model = None
        
        if not self.mock_mode and Config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(Config.LLM_MODEL)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
                self.mock_mode = True
    
    @track_llm_usage(task_type="rca")
    async def analyze(
        self,
        error_logs: str,
        git_diff: str,
        build_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze build failure using LLM."""
        
        if self.mock_mode:
            return self._mock_analysis(error_logs, git_diff, build_info)
        
        # Construct the prompt
        user_prompt = f"""Analyze this build failure:

## Build Information
- Job: {build_info.get('job_name', 'unknown')}
- Build Number: {build_info.get('build_number', 'unknown')}
- Result: {build_info.get('result', 'FAILURE')}

## Console Output (Error Logs)
```
{error_logs}
```

## Git Diff (Code Changes)
```diff
{git_diff}
```

Please analyze and provide your response in the JSON format specified."""

        try:
            response = await asyncio.to_thread(
                self._model.generate_content,
                [
                    {"role": "user", "parts": [self.SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["I understand. I'll analyze build failures and provide structured JSON responses with root cause analysis, suspected files, and fix suggestions."]},
                    {"role": "user", "parts": [user_prompt]}
                ]
            )
            
            # Parse JSON from response
            response_text = response.text
            
            # Extract JSON from potential markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)
            
            import json
            result = json.loads(response_text)
            
            # Add token usage
            result["tokens_used"] = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            result["model_used"] = Config.LLM_MODEL
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._fallback_analysis(error_logs, git_diff, str(e))
    
    def _mock_analysis(
        self,
        error_logs: str,
        git_diff: str,
        build_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock analysis for testing."""
        return {
            "root_cause_summary": "Test failure in TestUserService.test_validate_email due to validate_user_email() returning None instead of ValidationResult when email format check fails.",
            "error_type": "test_failure",
            "error_message": "AttributeError: 'NoneType' object has no attribute 'is_valid'",
            "suspected_file": "src/api/users.py",
            "suspected_lines": [87, 88, 89],
            "confidence_score": 0.92,
            "fix_suggestion": "The validate_user_email method returns None when the email is invalid or empty, but the test expects a ValidationResult object. Modify the method to always return a ValidationResult object, even for invalid emails, or update the test to handle None returns.",
            "fix_code_snippet": """def validate_user_email(self, email: str) -> ValidationResult:
    \"\"\"Validate a user's email address.\"\"\"
    if not email:
        return ValidationResult(is_valid=False, error="Email cannot be empty")
    
    if not self._is_valid_email_format(email):
        return ValidationResult(is_valid=False, error="Invalid email format")
    
    # ... rest of validation
    return ValidationResult(is_valid=True, error=None)""",
            "additional_recommendations": [
                "Add type hints to ensure consistent return types",
                "Consider adding more edge case tests for email validation",
                "The error logging should not replace proper return values"
            ],
            "tokens_used": 1250,
            "model_used": "gemini-1.5-pro (mock)"
        }
    
    def _fallback_analysis(
        self,
        error_logs: str,
        git_diff: str,
        error: str
    ) -> Dict[str, Any]:
        """Fallback analysis using regex patterns when LLM fails."""
        
        # Try to extract error information using patterns
        from nexus_lib.utils import extract_error_summary, parse_stack_trace, identify_failing_test
        
        errors = extract_error_summary(error_logs, max_errors=5)
        stack_trace = parse_stack_trace(error_logs)
        failing_test = identify_failing_test(error_logs)
        
        root_cause = "Unable to perform full LLM analysis. "
        if errors:
            root_cause += f"Detected errors: {errors[0]}"
        
        suspected_file = None
        if stack_trace and stack_trace.get("top_frame"):
            suspected_file = stack_trace["top_frame"].get("file")
        
        return {
            "root_cause_summary": root_cause,
            "error_type": "test_failure" if failing_test else "unknown",
            "error_message": errors[0] if errors else "Unknown error",
            "suspected_file": suspected_file,
            "suspected_lines": [],
            "confidence_score": 0.3,
            "fix_suggestion": "Please review the error logs manually. LLM analysis failed: " + error,
            "fix_code_snippet": None,
            "additional_recommendations": ["Review the full build log", "Check recent commits"],
            "tokens_used": 0,
            "model_used": "fallback-regex"
        }


# =============================================================================
# RCA Engine
# =============================================================================

class RcaEngine:
    """
    Core RCA engine that orchestrates the analysis process:
    1. Fetch build logs from Jenkins
    2. Fetch git diff from GitHub  
    3. Process and truncate logs for LLM context
    4. Send to LLM for analysis
    5. Return structured RCA result
    6. (Optional) Send Slack notification with PR owner tag
    """
    
    def __init__(self):
        self.jenkins = JenkinsClient()
        self.github = GitHubClient()
        self.llm = RcaLLMClient()
        self.slack = SlackNotificationClient()
    
    async def close(self):
        """Clean up resources."""
        await self.slack.close()
    
    async def analyze_build(
        self,
        request: RcaRequest,
        notify: bool = False,
        channel: Optional[str] = None,
        pr_owner_email: Optional[str] = None,
        trigger: str = "manual"
    ) -> RcaAnalysis:
        """Perform complete RCA analysis on a failed build."""
        
        start_time = time.time()
        ACTIVE_ANALYSES.inc()
        
        try:
            # Step 1: Fetch build info and console output
            logger.info(f"Fetching build info for {request.job_name}#{request.build_number}")
            build_info = await self.jenkins.get_build_info(request.job_name, request.build_number)
            
            logger.info(f"Fetching console output for {request.job_name}#{request.build_number}")
            console_output = await self.jenkins.get_console_output(request.job_name, request.build_number)
            
            # Step 2: Truncate logs for LLM context window
            from nexus_lib.utils import truncate_build_log
            truncated_logs = truncate_build_log(
                console_output,
                max_total_chars=Config.MAX_LOG_CHARS
            )
            
            # Step 3: Fetch git diff if available
            git_diff = ""
            changed_files = []
            
            if request.include_git_diff:
                if request.commit_sha:
                    git_diff, changed_files = await self.github.get_commit_diff(
                        request.repo_name or request.job_name,
                        request.commit_sha
                    )
                elif request.pr_id:
                    git_diff, changed_files = await self.github.get_pr_diff(
                        request.repo_name or request.job_name,
                        request.pr_id
                    )
                elif "changeSet" in build_info:
                    # Extract commit from build info
                    changes = build_info.get("changeSet", {}).get("items", [])
                    if changes:
                        commit = changes[0].get("commitId")
                        if commit:
                            git_diff, changed_files = await self.github.get_commit_diff(
                                request.repo_name or request.job_name,
                                commit
                            )
                
                # Truncate diff if too long
                if len(git_diff) > Config.MAX_DIFF_CHARS:
                    git_diff = git_diff[:Config.MAX_DIFF_CHARS] + "\n[... diff truncated ...]"
            
            # Step 4: Send to LLM for analysis
            logger.info("Sending to LLM for analysis...")
            llm_result = await self.llm.analyze(truncated_logs, git_diff, build_info)
            
            # Step 5: Build RcaAnalysis response
            analysis_duration = time.time() - start_time
            
            # Convert file changes
            suspected_files = []
            suspected_file = llm_result.get("suspected_file")
            if suspected_file:
                for cf in changed_files:
                    if cf["filename"] == suspected_file or suspected_file in cf["filename"]:
                        suspected_files.append(RcaFileChange(
                            file_path=cf["filename"],
                            change_type=cf["status"],
                            lines_added=cf.get("additions", 0),
                            lines_deleted=cf.get("deletions", 0),
                            relevant_lines=llm_result.get("suspected_lines")
                        ))
            
            # Determine confidence level
            confidence = llm_result.get("confidence_score", 0.5)
            if confidence >= 0.8:
                confidence_level = "high"
            elif confidence >= 0.5:
                confidence_level = "medium"
            elif confidence >= 0.3:
                confidence_level = "low"
            else:
                confidence_level = "uncertain"
            
            # Extract culprit info
            culprits = build_info.get("culprits", [])
            suspected_author = culprits[0].get("fullName") if culprits else None
            
            # Get suspected commit
            changes = build_info.get("changeSet", {}).get("items", [])
            suspected_commit = changes[0].get("commitId") if changes else request.commit_sha
            
            analysis = RcaAnalysis(
                analysis_id=f"rca-{request.job_name}-{request.build_number}-{int(time.time())}",
                root_cause_summary=llm_result.get("root_cause_summary", "Unknown"),
                error_type=llm_result.get("error_type", "unknown"),
                error_message=llm_result.get("error_message", ""),
                confidence_score=confidence,
                confidence_level=confidence_level,
                suspected_commit=suspected_commit,
                suspected_author=suspected_author,
                suspected_files=suspected_files,
                test_failures=[],  # Would be parsed from logs
                error_log_excerpt=truncated_logs[:2000] if len(truncated_logs) > 2000 else truncated_logs,
                fix_suggestion=llm_result.get("fix_suggestion", ""),
                fix_code_snippet=llm_result.get("fix_code_snippet"),
                additional_recommendations=llm_result.get("additional_recommendations", []),
                analyzed_at=datetime.utcnow(),
                analysis_duration_seconds=analysis_duration,
                model_used=llm_result.get("model_used"),
                tokens_used=llm_result.get("tokens_used", 0)
            )
            
            # Record metrics
            RCA_REQUESTS.labels(status="success", error_type=analysis.error_type, trigger=trigger).inc()
            RCA_DURATION.labels(job_name=request.job_name).observe(analysis_duration)
            RCA_CONFIDENCE.observe(confidence)
            
            logger.info(f"RCA complete for {request.job_name}#{request.build_number} in {analysis_duration:.2f}s")
            
            # Step 6: Send Slack notification if enabled
            if notify and Config.SLACK_NOTIFY_ON_FAILURE:
                notification_channel = channel or Config.SLACK_RELEASE_CHANNEL
                
                # Use pr_owner_email or try to get from suspected_author
                owner_email = pr_owner_email or suspected_author
                
                logger.info(f"Sending RCA notification to {notification_channel}")
                notification_sent = await self.slack.send_rca_notification(
                    analysis=analysis,
                    channel=notification_channel,
                    pr_owner_email=owner_email,
                    build_url=request.build_url or build_info.get("url")
                )
                
                if notification_sent:
                    analysis.notification_sent = True
                    analysis.notification_channel = notification_channel
                    analysis.pr_owner_tagged = owner_email
            
            return analysis
            
        except Exception as e:
            RCA_REQUESTS.labels(status="error", error_type="exception", trigger=trigger).inc()
            logger.error(f"RCA failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            ACTIVE_ANALYSES.dec()


# =============================================================================
# FastAPI Application
# =============================================================================

rca_engine: Optional[RcaEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global rca_engine
    
    logger.info("🔍 Starting Nexus RCA Agent...")
    rca_engine = RcaEngine()
    
    logger.info("✅ RCA Agent ready!")
    logger.info(f"   Jenkins Mock Mode: {Config.JENKINS_MOCK_MODE}")
    logger.info(f"   GitHub Mock Mode: {Config.GITHUB_MOCK_MODE}")
    logger.info(f"   LLM Mock Mode: {Config.LLM_MOCK_MODE}")
    logger.info(f"   Slack Mock Mode: {Config.SLACK_MOCK_MODE}")
    logger.info(f"   Auto-Analyze: {Config.AUTO_ANALYZE_ENABLED}")
    logger.info(f"   Release Channel: {Config.SLACK_RELEASE_CHANNEL}")
    
    yield
    
    # Cleanup
    if rca_engine:
        await rca_engine.close()
    logger.info("👋 RCA Agent shutdown complete")


app = FastAPI(
    title="Nexus RCA Agent",
    description="Smart Root Cause Analysis for build failures with auto-trigger and Slack notifications",
    version="2.2.0",
    lifespan=lifespan
)

# CORS
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
        "service": "rca-agent",
        "version": "2.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "jenkins_mock": Config.JENKINS_MOCK_MODE,
            "github_mock": Config.GITHUB_MOCK_MODE,
            "llm_mock": Config.LLM_MOCK_MODE,
            "llm_model": Config.LLM_MODEL,
            "slack_mock": Config.SLACK_MOCK_MODE,
            "auto_analyze": Config.AUTO_ANALYZE_ENABLED,
            "release_channel": Config.SLACK_RELEASE_CHANNEL
        }
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class AnalyzeRequest(BaseModel):
    """Extended analyze request with notification options."""
    job_name: str
    build_number: int
    build_url: Optional[str] = None
    repo_name: Optional[str] = None
    branch: Optional[str] = None
    pr_id: Optional[int] = None
    commit_sha: Optional[str] = None
    include_git_diff: bool = True
    include_test_output: bool = True
    max_log_lines: int = 5000
    
    # Notification options
    notify: bool = False
    channel: Optional[str] = None
    pr_owner_email: Optional[str] = None


@app.post("/analyze", response_model=RcaAnalysis)
async def analyze_build_failure(request: AnalyzeRequest):
    """
    Analyze a failed build to determine root cause.
    
    This endpoint:
    1. Fetches the build console output from Jenkins
    2. Fetches git diffs for commits in the build
    3. Uses LLM to correlate errors with code changes
    4. Returns structured root cause analysis with fix suggestions
    5. Optionally sends Slack notification with PR owner tag
    
    Set `notify=true` to send Slack notification to the release channel.
    """
    rca_request = RcaRequest(
        job_name=request.job_name,
        build_number=request.build_number,
        build_url=request.build_url,
        repo_name=request.repo_name,
        branch=request.branch,
        pr_id=request.pr_id,
        commit_sha=request.commit_sha,
        include_git_diff=request.include_git_diff,
        include_test_output=request.include_test_output,
        max_log_lines=request.max_log_lines
    )
    
    return await rca_engine.analyze_build(
        request=rca_request,
        notify=request.notify,
        channel=request.channel,
        pr_owner_email=request.pr_owner_email,
        trigger="manual"
    )


@app.post("/webhook/jenkins")
async def jenkins_webhook(
    payload: JenkinsWebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for Jenkins to trigger automatic RCA on build failures.
    
    Configure in Jenkins with Generic Webhook Trigger plugin:
    - URL: http://rca-agent:8006/webhook/jenkins
    - Content-Type: application/json
    - Filter: Only trigger on FAILURE or UNSTABLE
    
    The RCA analysis runs in background and sends Slack notification.
    """
    # Only analyze failures
    if payload.build_result not in ("FAILURE", "UNSTABLE"):
        RCA_WEBHOOKS.labels(job_name=payload.job_name, status="skipped").inc()
        return {
            "status": "skipped",
            "reason": f"Build result is {payload.build_result}, not a failure",
            "job": payload.job_name,
            "build": payload.build_number
        }
    
    if not Config.AUTO_ANALYZE_ENABLED:
        RCA_WEBHOOKS.labels(job_name=payload.job_name, status="disabled").inc()
        return {
            "status": "disabled",
            "reason": "Auto-analyze is disabled",
            "job": payload.job_name,
            "build": payload.build_number
        }
    
    RCA_WEBHOOKS.labels(job_name=payload.job_name, status="queued").inc()
    
    # Extract repo name from git_url if available
    repo_name = None
    if payload.git_url:
        # Parse repo name from URL like https://github.com/org/repo.git
        match = re.search(r'/([^/]+/[^/]+?)(?:\.git)?$', payload.git_url)
        if match:
            repo_name = match.group(1).split('/')[-1]
    
    # Queue background analysis
    background_tasks.add_task(
        _background_analyze_and_notify,
        job_name=payload.job_name,
        build_number=payload.build_number,
        build_url=payload.build_url,
        repo_name=repo_name,
        branch=payload.git_branch,
        commit_sha=payload.git_commit,
        pr_id=payload.pr_number,
        pr_owner_email=payload.pr_author_email,
        channel=payload.release_channel
    )
    
    return {
        "status": "queued",
        "message": "RCA analysis queued, Slack notification will be sent",
        "job": payload.job_name,
        "build": payload.build_number,
        "channel": payload.release_channel or Config.SLACK_RELEASE_CHANNEL
    }


async def _background_analyze_and_notify(
    job_name: str,
    build_number: int,
    build_url: Optional[str] = None,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    commit_sha: Optional[str] = None,
    pr_id: Optional[int] = None,
    pr_owner_email: Optional[str] = None,
    channel: Optional[str] = None
):
    """Background task to analyze build failure and send notification."""
    try:
        logger.info(f"[BACKGROUND] Starting RCA for {job_name}#{build_number}")
        
        request = RcaRequest(
            job_name=job_name,
            build_number=build_number,
            build_url=build_url,
            repo_name=repo_name,
            branch=branch,
            commit_sha=commit_sha,
            pr_id=pr_id
        )
        
        analysis = await rca_engine.analyze_build(
            request=request,
            notify=True,
            channel=channel,
            pr_owner_email=pr_owner_email,
            trigger="webhook"
        )
        
        logger.info(f"[BACKGROUND] RCA complete for {job_name}#{build_number}: {analysis.root_cause_summary[:50]}...")
        
    except Exception as e:
        logger.error(f"[BACKGROUND] RCA failed for {job_name}#{build_number}: {e}")


@app.post("/execute")
async def execute_task(request: Dict[str, Any]):
    """
    Generic execute endpoint for orchestrator integration.
    Maps actions to specific RCA functions.
    """
    action = request.get("action", "")
    payload = request.get("payload", {})
    
    if action == "analyze_build_failure":
        rca_request = RcaRequest(**payload)
        notify = payload.get("notify", True)  # Default to notify from orchestrator
        analysis = await rca_engine.analyze_build(
            request=rca_request,
            notify=notify,
            trigger="orchestrator"
        )
        return {"status": "success", "data": analysis.model_dump()}
    
    elif action == "health":
        return {"status": "success", "data": await health_check()}
    
    else:
        raise HTTPException(400, f"Unknown action: {action}")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=os.getenv("ENV", "development") == "development"
    )


"""
Nexus Git/CI Agent - MCP Server Implementation
===============================================

GitHub and Jenkins integration agent exposed via Model Context Protocol (MCP) over SSE.
Provides tools for repository health, PR status, build management, and security scans.

Architecture: MCP Server with SSE Transport
Port: 8082
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import random

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from pydantic import BaseModel
import uvicorn
import httpx

# Add shared lib path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'shared'))

try:
    from nexus_lib.config import ConfigManager, ConfigKeys
    from nexus_lib.schemas.agent_contract import (
        BuildStatus, PRStatus, RepositoryHealth, SecurityScanResult,
        BuildResult, SeverityLevel, Vulnerability
    )
except ImportError:
    ConfigManager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.git-ci-agent")

# =============================================================================
# Configuration
# =============================================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_ORG = os.getenv("GITHUB_ORG", "nexus-org")
JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins:8080")
JENKINS_USERNAME = os.getenv("JENKINS_USERNAME", "")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
GITHUB_MOCK_MODE = os.getenv("GITHUB_MOCK_MODE", "true").lower() == "true"
JENKINS_MOCK_MODE = os.getenv("JENKINS_MOCK_MODE", "true").lower() == "true"
PORT = int(os.getenv("GIT_CI_AGENT_PORT", "8082"))

# =============================================================================
# Mock Data Generators
# =============================================================================

class MockGitHubData:
    """Generates realistic mock GitHub data."""
    
    BRANCHES = ["main", "develop", "feature/auth", "feature/api-v2", "fix/bug-123", "release/v2.0"]
    AUTHORS = ["alice", "bob", "carol", "david", "eve"]
    
    @classmethod
    def generate_repo_health(cls, repo_name: str) -> Dict[str, Any]:
        """Generate mock repository health."""
        return {
            "repo_name": repo_name,
            "default_branch": "main",
            "latest_commit_sha": f"{''.join(random.choices('0123456789abcdef', k=40))}",
            "latest_commit_status": random.choice(["success", "success", "success", "failure", "pending"]),
            "branch_protection_enabled": random.choice([True, True, False]),
            "required_reviews": random.choice([1, 2, 2]),
            "open_prs": random.randint(2, 15),
            "stale_prs": random.randint(0, 3),
            "open_issues": random.randint(5, 50),
            "last_successful_build": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "build_frequency_per_week": round(random.uniform(10, 50), 1),
            "average_build_duration_minutes": round(random.uniform(5, 25), 1)
        }
    
    @classmethod
    def generate_pr_status(cls, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Generate mock PR status."""
        state = random.choice(["open", "open", "merged", "closed"])
        return {
            "pr_number": pr_number,
            "title": f"[{repo_name}] Feature: Sample PR #{pr_number}",
            "state": state,
            "author": random.choice(cls.AUTHORS),
            "base_branch": "main",
            "head_branch": random.choice(cls.BRANCHES[2:]),
            "url": f"https://github.com/{GITHUB_ORG}/{repo_name}/pull/{pr_number}",
            "mergeable": random.choice([True, True, True, False]) if state == "open" else None,
            "merged": state == "merged",
            "merged_by": random.choice(cls.AUTHORS) if state == "merged" else None,
            "merged_at": datetime.utcnow().isoformat() if state == "merged" else None,
            "ci_status": random.choice(["success", "success", "failure", "pending"]),
            "required_checks_passed": random.choice([True, True, False]),
            "approvals": random.randint(0, 3),
            "changes_requested": random.choice([False, False, True]),
            "additions": random.randint(10, 500),
            "deletions": random.randint(5, 200),
            "changed_files": random.randint(1, 20),
            "commits": random.randint(1, 10),
            "comments": random.randint(0, 15),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 14))).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def generate_security_scan(cls, repo_name: str, branch: str = "main") -> Dict[str, Any]:
        """Generate mock security scan results."""
        critical = random.choices([0, 0, 0, 1], weights=[70, 20, 5, 5])[0]
        high = random.randint(0, 5)
        medium = random.randint(0, 10)
        low = random.randint(0, 15)
        
        risk_score = min(100, critical * 40 + high * 15 + medium * 5 + low * 1)
        
        vulnerabilities = []
        for i in range(critical + high + medium + low):
            severity = "critical" if i < critical else "high" if i < critical + high else "medium" if i < critical + high + medium else "low"
            vulnerabilities.append({
                "id": f"CVE-2024-{random.randint(10000, 99999)}",
                "title": f"Sample vulnerability in dependency",
                "severity": severity,
                "cvss_score": {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.5}[severity],
                "package_name": random.choice(["lodash", "axios", "express", "react", "webpack"]),
                "package_version": f"{random.randint(1, 10)}.{random.randint(0, 20)}.{random.randint(0, 10)}",
                "fixed_in_version": f"{random.randint(1, 10)}.{random.randint(0, 20)}.{random.randint(11, 30)}",
                "exploitable": severity in ["critical", "high"] and random.choice([True, False])
            })
        
        return {
            "scan_id": f"scan-{random.randint(10000, 99999)}",
            "repo_name": repo_name,
            "branch": branch,
            "commit_sha": f"{''.join(random.choices('0123456789abcdef', k=40))}",
            "scanner_name": "nexus-security-scanner",
            "scan_timestamp": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "risk_level": "critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium" if risk_score >= 40 else "low",
            "critical_vulnerabilities": critical,
            "high_vulnerabilities": high,
            "medium_vulnerabilities": medium,
            "low_vulnerabilities": low,
            "info_vulnerabilities": random.randint(0, 5),
            "vulnerabilities": vulnerabilities,
            "total_dependencies": random.randint(50, 300),
            "vulnerable_dependencies": critical + high + medium + low,
            "outdated_dependencies": random.randint(5, 30),
            "secrets_detected": random.choice([0, 0, 0, 1]),
            "compliant": risk_score < 60
        }


class MockJenkinsData:
    """Generates realistic mock Jenkins data."""
    
    @classmethod
    def generate_build_status(cls, job_name: str, build_number: Optional[int] = None) -> Dict[str, Any]:
        """Generate mock build status."""
        build_num = build_number or random.randint(100, 999)
        status = random.choices(
            ["SUCCESS", "FAILURE", "UNSTABLE", "BUILDING"],
            weights=[70, 15, 10, 5]
        )[0]
        
        test_passed = random.randint(200, 500)
        test_failed = random.randint(0, 10) if status != "SUCCESS" else 0
        
        return {
            "job_name": job_name,
            "build_number": build_num,
            "status": status,
            "url": f"{JENKINS_URL}/job/{job_name}/{build_num}",
            "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(0, 48))).isoformat(),
            "duration_seconds": random.uniform(120, 900),
            "queued_duration_seconds": random.uniform(5, 60),
            "branch": random.choice(["main", "develop", "feature/test"]),
            "commit_sha": f"{''.join(random.choices('0123456789abcdef', k=40))}",
            "commit_message": f"feat: Add new feature for {job_name}",
            "commit_author": random.choice(["alice@example.com", "bob@example.com", "carol@example.com"]),
            "triggered_by": random.choice(["SCM change", "User: admin", "Timer"]),
            "test_results": {
                "total_tests": test_passed + test_failed,
                "passed": test_passed,
                "failed": test_failed,
                "skipped": random.randint(0, 5),
                "duration_seconds": random.uniform(60, 300),
                "coverage_percentage": round(random.uniform(70, 95), 1),
                "failed_test_names": [f"test_case_{i}" for i in range(test_failed)]
            },
            "artifacts": [
                {"name": f"{job_name}-{build_num}.jar", "path": "target/", "size_bytes": random.randint(1000000, 50000000)},
                {"name": "test-report.html", "path": "reports/", "size_bytes": random.randint(10000, 100000)}
            ] if status == "SUCCESS" else [],
            "console_log_url": f"{JENKINS_URL}/job/{job_name}/{build_num}/console"
        }
    
    @classmethod
    def generate_build_history(cls, job_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate mock build history."""
        builds = []
        for i in range(limit):
            build_num = 999 - i
            builds.append(cls.generate_build_status(job_name, build_num))
        return builds

# =============================================================================
# GitHub API Client
# =============================================================================

class GitHubClient:
    """GitHub REST API client with mock fallback."""
    
    def __init__(self, token: str, org: str, mock_mode: bool = False):
        self.token = token
        self.org = org
        self.mock_mode = mock_mode
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}" if self.token else "",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            self._client = httpx.AsyncClient(
                base_url="https://api.github.com",
                headers=headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_repo_health(self, repo_name: str) -> Dict[str, Any]:
        """Get repository health metrics."""
        if self.mock_mode:
            return MockGitHubData.generate_repo_health(repo_name)
        
        client = await self._get_client()
        
        # Fetch repo info
        repo_response = await client.get(f"/repos/{self.org}/{repo_name}")
        repo_response.raise_for_status()
        repo_data = repo_response.json()
        
        # Fetch latest commit
        commits_response = await client.get(f"/repos/{self.org}/{repo_name}/commits", params={"per_page": 1})
        commits_data = commits_response.json()
        
        # Fetch branch protection
        try:
            protection_response = await client.get(f"/repos/{self.org}/{repo_name}/branches/{repo_data['default_branch']}/protection")
            protection_enabled = protection_response.status_code == 200
            protection_data = protection_response.json() if protection_enabled else {}
        except:
            protection_enabled = False
            protection_data = {}
        
        # Fetch open PRs
        prs_response = await client.get(f"/repos/{self.org}/{repo_name}/pulls", params={"state": "open"})
        open_prs = len(prs_response.json())
        
        return {
            "repo_name": repo_name,
            "default_branch": repo_data.get("default_branch", "main"),
            "latest_commit_sha": commits_data[0]["sha"] if commits_data else "",
            "latest_commit_status": "success",  # Would need status check API
            "branch_protection_enabled": protection_enabled,
            "required_reviews": protection_data.get("required_pull_request_reviews", {}).get("required_approving_review_count", 0),
            "open_prs": open_prs,
            "stale_prs": 0,
            "open_issues": repo_data.get("open_issues_count", 0)
        }
    
    async def get_pr_status(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Get pull request status."""
        if self.mock_mode:
            return MockGitHubData.generate_pr_status(repo_name, pr_number)
        
        client = await self._get_client()
        
        pr_response = await client.get(f"/repos/{self.org}/{repo_name}/pulls/{pr_number}")
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        
        # Get reviews
        reviews_response = await client.get(f"/repos/{self.org}/{repo_name}/pulls/{pr_number}/reviews")
        reviews = reviews_response.json()
        approvals = sum(1 for r in reviews if r["state"] == "APPROVED")
        changes_requested = any(r["state"] == "CHANGES_REQUESTED" for r in reviews)
        
        return {
            "pr_number": pr_number,
            "title": pr_data["title"],
            "state": pr_data["state"],
            "author": pr_data["user"]["login"],
            "base_branch": pr_data["base"]["ref"],
            "head_branch": pr_data["head"]["ref"],
            "url": pr_data["html_url"],
            "mergeable": pr_data.get("mergeable"),
            "merged": pr_data.get("merged", False),
            "merged_by": pr_data.get("merged_by", {}).get("login") if pr_data.get("merged") else None,
            "merged_at": pr_data.get("merged_at"),
            "approvals": approvals,
            "changes_requested": changes_requested,
            "additions": pr_data["additions"],
            "deletions": pr_data["deletions"],
            "changed_files": pr_data["changed_files"],
            "commits": pr_data["commits"],
            "comments": pr_data["comments"],
            "created_at": pr_data["created_at"],
            "updated_at": pr_data["updated_at"]
        }
    
    async def get_security_scan(self, repo_name: str, branch: str = "main") -> Dict[str, Any]:
        """Get security scan results (uses Dependabot alerts)."""
        if self.mock_mode:
            return MockGitHubData.generate_security_scan(repo_name, branch)
        
        client = await self._get_client()
        
        # Fetch Dependabot alerts
        alerts_response = await client.get(
            f"/repos/{self.org}/{repo_name}/dependabot/alerts",
            params={"state": "open"}
        )
        
        if alerts_response.status_code != 200:
            # Dependabot might not be enabled
            return MockGitHubData.generate_security_scan(repo_name, branch)
        
        alerts = alerts_response.json()
        
        # Count by severity
        critical = sum(1 for a in alerts if a["security_vulnerability"]["severity"] == "critical")
        high = sum(1 for a in alerts if a["security_vulnerability"]["severity"] == "high")
        medium = sum(1 for a in alerts if a["security_vulnerability"]["severity"] == "medium")
        low = sum(1 for a in alerts if a["security_vulnerability"]["severity"] == "low")
        
        risk_score = min(100, critical * 40 + high * 15 + medium * 5 + low * 1)
        
        return {
            "scan_id": f"scan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "repo_name": repo_name,
            "branch": branch,
            "scanner_name": "github-dependabot",
            "scan_timestamp": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "risk_level": "critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium" if risk_score >= 40 else "low",
            "critical_vulnerabilities": critical,
            "high_vulnerabilities": high,
            "medium_vulnerabilities": medium,
            "low_vulnerabilities": low,
            "compliant": risk_score < 60
        }

# =============================================================================
# Jenkins API Client
# =============================================================================

class JenkinsClient:
    """Jenkins REST API client with mock fallback."""
    
    def __init__(self, base_url: str, username: str, api_token: str, mock_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.mock_mode = mock_mode
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = (self.username, self.api_token) if self.username and self.api_token else None
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_build_status(self, job_name: str, build_number: Optional[int] = None) -> Dict[str, Any]:
        """Get build status."""
        if self.mock_mode:
            return MockJenkinsData.generate_build_status(job_name, build_number)
        
        client = await self._get_client()
        
        # Get build info
        build_path = f"/job/{job_name}/{build_number or 'lastBuild'}/api/json"
        response = await client.get(build_path)
        response.raise_for_status()
        data = response.json()
        
        # Get test results
        test_results = None
        try:
            test_response = await client.get(f"/job/{job_name}/{data['number']}/testReport/api/json")
            if test_response.status_code == 200:
                test_data = test_response.json()
                test_results = {
                    "total_tests": test_data.get("totalCount", 0),
                    "passed": test_data.get("passCount", 0),
                    "failed": test_data.get("failCount", 0),
                    "skipped": test_data.get("skipCount", 0),
                    "duration_seconds": test_data.get("duration", 0)
                }
        except:
            pass
        
        return {
            "job_name": job_name,
            "build_number": data["number"],
            "status": data.get("result", "BUILDING"),
            "url": data["url"],
            "timestamp": datetime.fromtimestamp(data["timestamp"] / 1000).isoformat(),
            "duration_seconds": data.get("duration", 0) / 1000,
            "test_results": test_results
        }
    
    async def trigger_build(self, job_name: str, parameters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Trigger a Jenkins build."""
        if self.mock_mode:
            return {
                "success": True,
                "job_name": job_name,
                "message": f"Build triggered for {job_name}",
                "queue_id": random.randint(1000, 9999)
            }
        
        client = await self._get_client()
        
        if parameters:
            response = await client.post(
                f"/job/{job_name}/buildWithParameters",
                data=parameters
            )
        else:
            response = await client.post(f"/job/{job_name}/build")
        
        if response.status_code in [200, 201]:
            return {"success": True, "job_name": job_name, "message": "Build triggered"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def get_build_history(self, job_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get build history."""
        if self.mock_mode:
            return MockJenkinsData.generate_build_history(job_name, limit)
        
        client = await self._get_client()
        
        response = await client.get(f"/job/{job_name}/api/json", params={"tree": f"builds[number,result,url,timestamp,duration]{{0,{limit}}}"})
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                "build_number": b["number"],
                "status": b.get("result", "BUILDING"),
                "url": b["url"],
                "timestamp": datetime.fromtimestamp(b["timestamp"] / 1000).isoformat(),
                "duration_seconds": b.get("duration", 0) / 1000
            }
            for b in data.get("builds", [])
        ]
    
    async def get_console_log(self, job_name: str, build_number: int, tail_lines: int = 500) -> str:
        """Get console log output."""
        if self.mock_mode:
            return f"[MOCK] Console log for {job_name} #{build_number}\n" + "... mock log output ..." * 10
        
        client = await self._get_client()
        response = await client.get(f"/job/{job_name}/{build_number}/consoleText")
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            return '\n'.join(lines[-tail_lines:])
        return ""

# =============================================================================
# Initialize Clients
# =============================================================================

github_client = GitHubClient(
    token=GITHUB_TOKEN,
    org=GITHUB_ORG,
    mock_mode=GITHUB_MOCK_MODE
)

jenkins_client = JenkinsClient(
    base_url=JENKINS_URL,
    username=JENKINS_USERNAME,
    api_token=JENKINS_API_TOKEN,
    mock_mode=JENKINS_MOCK_MODE
)

# Create MCP server
mcp_server = Server("nexus-git-ci-agent")

# =============================================================================
# MCP Tool Definitions
# =============================================================================

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available Git/CI tools."""
    return [
        Tool(
            name="get_repo_health",
            description="Get health metrics for a GitHub repository including commit status, open PRs, branch protection, and build frequency.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (without org prefix)"
                    }
                },
                "required": ["repo_name"]
            }
        ),
        Tool(
            name="get_pr_status",
            description="Get detailed status of a GitHub pull request including approvals, CI status, and merge status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "pr_number": {
                        "type": "integer",
                        "description": "Pull request number"
                    }
                },
                "required": ["repo_name", "pr_number"]
            }
        ),
        Tool(
            name="get_security_scan",
            description="Get security scan results for a repository including vulnerability counts and risk score.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch to scan (default: main)",
                        "default": "main"
                    }
                },
                "required": ["repo_name"]
            }
        ),
        Tool(
            name="get_build_status",
            description="Get Jenkins build status for a job. Returns build result, test results, and artifacts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name"
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Specific build number (optional, defaults to latest)"
                    }
                },
                "required": ["job_name"]
            }
        ),
        Tool(
            name="trigger_build",
            description="Trigger a Jenkins build for a job. Can include build parameters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name to trigger"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Optional build parameters as key-value pairs"
                    }
                },
                "required": ["job_name"]
            }
        ),
        Tool(
            name="get_build_history",
            description="Get recent build history for a Jenkins job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of builds to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["job_name"]
            }
        ),
        Tool(
            name="get_console_log",
            description="Get console log output from a Jenkins build (last 500 lines by default).",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name"
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Build number"
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": "Number of lines from the end to return (default: 500)",
                        "default": 500
                    }
                },
                "required": ["job_name", "build_number"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a Git/CI tool."""
    logger.info(f"Tool call: {name} with args: {arguments}")
    
    try:
        if name == "get_repo_health":
            result = await github_client.get_repo_health(arguments["repo_name"])
        
        elif name == "get_pr_status":
            result = await github_client.get_pr_status(
                repo_name=arguments["repo_name"],
                pr_number=arguments["pr_number"]
            )
        
        elif name == "get_security_scan":
            result = await github_client.get_security_scan(
                repo_name=arguments["repo_name"],
                branch=arguments.get("branch", "main")
            )
        
        elif name == "get_build_status":
            result = await jenkins_client.get_build_status(
                job_name=arguments["job_name"],
                build_number=arguments.get("build_number")
            )
        
        elif name == "trigger_build":
            result = await jenkins_client.trigger_build(
                job_name=arguments["job_name"],
                parameters=arguments.get("parameters")
            )
        
        elif name == "get_build_history":
            result = await jenkins_client.get_build_history(
                job_name=arguments["job_name"],
                limit=arguments.get("limit", 10)
            )
        
        elif name == "get_console_log":
            log = await jenkins_client.get_console_log(
                job_name=arguments["job_name"],
                build_number=arguments["build_number"],
                tail_lines=arguments.get("tail_lines", 500)
            )
            result = {"console_log": log}
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# =============================================================================
# Starlette App
# =============================================================================

async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "nexus-git-ci-agent",
        "version": "2.0.0",
        "transport": "mcp-sse",
        "github_mock_mode": GITHUB_MOCK_MODE,
        "jenkins_mock_mode": JENKINS_MOCK_MODE,
        "timestamp": datetime.utcnow().isoformat()
    })

async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication."""
    transport = SseServerTransport("/messages")
    async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options()
        )

async def legacy_execute(request: Request) -> JSONResponse:
    """Legacy REST endpoint for backward compatibility."""
    try:
        body = await request.json()
        action = body.get("action", "")
        payload = body.get("payload", {})
        
        action_map = {
            "get_repo_health": ("get_repo_health", {"repo_name": payload.get("repo_name")}),
            "get_pr_status": ("get_pr_status", {"repo_name": payload.get("repo_name"), "pr_number": payload.get("pr_number")}),
            "get_security_scan": ("get_security_scan", {"repo_name": payload.get("repo_name"), "branch": payload.get("branch", "main")}),
            "get_build_status": ("get_build_status", {"job_name": payload.get("job_name"), "build_number": payload.get("build_number")}),
            "trigger_build": ("trigger_build", {"job_name": payload.get("job_name"), "parameters": payload.get("parameters")}),
            "get_build_history": ("get_build_history", {"job_name": payload.get("job_name"), "limit": payload.get("limit", 10)}),
        }
        
        if action not in action_map:
            return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)
        
        tool_name, tool_args = action_map[action]
        result = await call_tool(tool_name, tool_args)
        
        return JSONResponse({
            "status": "success",
            "data": json.loads(result[0].text) if result else {},
            "agent_type": "git_ci"
        })
    
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return JSONResponse({
            "status": "failed",
            "error_message": str(e),
            "agent_type": "git_ci"
        }, status_code=500)

async def shutdown():
    """Cleanup on shutdown."""
    await github_client.close()
    await jenkins_client.close()

app = Starlette(
    debug=os.getenv("NEXUS_ENV", "development") == "development",
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/execute", legacy_execute, methods=["POST"]),
        Route("/", health_check, methods=["GET"]),
    ],
    on_shutdown=[shutdown]
)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Starting Nexus Git/CI Agent (MCP over SSE) on port {PORT}")
    logger.info(f"📡 GitHub mock mode: {GITHUB_MOCK_MODE}")
    logger.info(f"📡 Jenkins mock mode: {JENKINS_MOCK_MODE}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )

"""
Nexus RCA (Root Cause Analysis) Agent - MCP Server
==================================================

MCP-based agent for analyzing failed builds to determine root causes.
Uses LLM to correlate error logs with git diffs and provide fix suggestions.

Architecture: MCP Server (replaces FastAPI REST endpoints)
Transport: SSE (Server-Sent Events)
Protocol: Model Context Protocol

Author: Nexus Team
Version: 3.0.0
"""

import asyncio
import logging
import os
import sys
import re
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps

import httpx
from pydantic import BaseModel, Field

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.mcp import NexusMCPServer, create_mcp_app
from nexus_lib.config import ConfigManager, ConfigKeys, is_mock_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.rca-agent")


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """RCA Agent configuration."""
    MAX_LOG_CHARS = int(os.getenv("RCA_MAX_LOG_CHARS", "100000"))
    MAX_DIFF_CHARS = int(os.getenv("RCA_MAX_DIFF_CHARS", "50000"))
    PORT = int(os.getenv("PORT", "8006"))
    DEFAULT_SLACK_CHANNEL = "#release-notifications"
    DEFAULT_LLM_MODEL = "gemini-1.5-pro"
    
    @classmethod
    async def get_jenkins_url(cls) -> str:
        return await ConfigManager.get(ConfigKeys.JENKINS_URL) or "http://jenkins:8080"
    
    @classmethod
    async def get_github_token(cls) -> str:
        return await ConfigManager.get(ConfigKeys.GITHUB_TOKEN) or ""
    
    @classmethod
    async def get_gemini_api_key(cls) -> str:
        return await ConfigManager.get(ConfigKeys.GEMINI_API_KEY) or ""
    
    @classmethod
    async def get_llm_model(cls) -> str:
        return await ConfigManager.get(ConfigKeys.LLM_MODEL) or cls.DEFAULT_LLM_MODEL


# ============================================================================
# DATA MODELS
# ============================================================================

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
    additional_recommendations: List[str] = []
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration_seconds: float = 0.0
    model_used: Optional[str] = None
    tokens_used: int = 0


# ============================================================================
# JENKINS CLIENT
# ============================================================================

class JenkinsClient:
    """Client for fetching Jenkins build information."""
    
    def __init__(self):
        self._last_mode = None
        self._client = None
    
    async def _ensure_initialized(self):
        self._last_mode = await is_mock_mode()
        
        if not self._last_mode:
            try:
                import jenkins
                url = await Config.get_jenkins_url()
                username = await ConfigManager.get(ConfigKeys.JENKINS_USERNAME)
                token = await ConfigManager.get(ConfigKeys.JENKINS_API_TOKEN)
                if url and username and token:
                    self._client = jenkins.Jenkins(url, username=username, password=token)
            except Exception as e:
                logger.warning(f"Failed to initialize Jenkins client: {e}")
                self._last_mode = True
    
    @property
    def mock_mode(self) -> bool:
        return self._last_mode if self._last_mode is not None else True
    
    async def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get build information."""
        await self._ensure_initialized()
        
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
                "culprits": info.get("culprits", []),
                "changeSet": info.get("changeSet", {})
            }
        except Exception as e:
            logger.error(f"Failed to get build info: {e}")
            raise
    
    async def get_console_output(self, job_name: str, build_number: int) -> str:
        """Get console output from a build."""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_console_output(job_name, build_number)
        
        try:
            return self._client.get_build_console_output(job_name, build_number)
        except Exception as e:
            logger.error(f"Failed to get console output: {e}")
            raise
    
    def _mock_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Generate mock build info."""
        return {
            "job_name": job_name,
            "build_number": build_number,
            "result": "FAILURE",
            "url": f"http://jenkins:8080/job/{job_name}/{build_number}/",
            "timestamp": int(time.time() * 1000),
            "duration": 125000,
            "culprits": [{"fullName": "developer@example.com"}],
            "changeSet": {
                "items": [{
                    "commitId": "a1b2c3d4e5f6789",
                    "author": {"fullName": "developer@example.com"},
                    "msg": "feat: add new user validation",
                    "paths": [
                        {"editType": "edit", "file": "src/api/users.py"},
                        {"editType": "add", "file": "tests/test_users.py"}
                    ]
                }]
            }
        }
    
    def _mock_console_output(self, job_name: str, build_number: int) -> str:
        """Generate mock console output."""
        return """Started by user admin
Building in workspace /var/jenkins_home/workspace/nexus-pipeline
[Pipeline] stage
[Pipeline] { (Test)
[Pipeline] sh
+ python -m pytest tests/ -v

============================= test session starts ==============================
tests/test_users.py::TestUserService::test_validate_email FAILED

=================================== FAILURES ===================================
_________________________ TestUserService.test_validate_email __________________________

    def test_validate_email(self):
        result = user_service.validate_user_email("test@example.com")
>       assert result.is_valid == True
E       AttributeError: 'NoneType' object has no attribute 'is_valid'

tests/test_users.py:42: AttributeError
============================= 1 failed, 44 passed in 12.34s ====================
Finished: FAILURE
"""


# ============================================================================
# GITHUB CLIENT
# ============================================================================

class GitHubClient:
    """Client for fetching GitHub commit and diff information."""
    
    def __init__(self):
        self._last_mode = None
        self._github = None
    
    async def _ensure_initialized(self):
        self._last_mode = await is_mock_mode()
        
        if not self._last_mode:
            try:
                from github import Github
                token = await Config.get_github_token()
                if token:
                    self._github = Github(token)
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub client: {e}")
                self._last_mode = True
    
    @property
    def mock_mode(self) -> bool:
        return self._last_mode if self._last_mode is not None else True
    
    async def get_commit_diff(self, repo_name: str, commit_sha: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Get the diff for a specific commit."""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_commit_diff(repo_name, commit_sha)
        
        try:
            github_org = await ConfigManager.get(ConfigKeys.GITHUB_ORG)
            repo = self._github.get_repo(f"{github_org}/{repo_name}")
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
    
    def _mock_commit_diff(self, repo_name: str, ref: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate mock commit diff."""
        diff_text = """=== src/api/users.py ===
@@ -82,10 +82,15 @@ class UserService:
     def validate_user_email(self, email: str):
+        if not email:
+            return None
+        
         try:
             if not self._is_valid_email_format(email):
-                return ValidationResult(is_valid=False, error="Invalid format")
+                return None
             return ValidationResult(is_valid=True, error=None)
"""
        files = [{
            "filename": "src/api/users.py",
            "status": "modified",
            "additions": 4,
            "deletions": 1,
            "patch": diff_text
        }]
        
        return diff_text, files


# ============================================================================
# LLM CLIENT FOR RCA
# ============================================================================

class RcaLLMClient:
    """LLM client for Root Cause Analysis."""
    
    SYSTEM_PROMPT = """You are a Senior DevOps Debugger. Analyze build failures by correlating error logs with code changes.

Response Format (JSON):
{
    "root_cause_summary": "Brief 1-2 sentence summary",
    "error_type": "One of: compilation_error, test_failure, dependency_error, configuration_error, infrastructure_error, timeout_error, unknown",
    "error_message": "Primary error message from logs",
    "suspected_file": "Path to file causing issue",
    "suspected_lines": [line_numbers],
    "confidence_score": 0.0-1.0,
    "fix_suggestion": "How to fix the issue",
    "fix_code_snippet": "Example code fix",
    "additional_recommendations": ["List of suggestions"]
}"""

    def __init__(self):
        self._last_mode = None
        self._model = None
    
    async def _ensure_initialized(self):
        self._last_mode = await is_mock_mode()
        
        if not self._last_mode:
            try:
                import google.generativeai as genai
                api_key = await Config.get_gemini_api_key()
                model_name = await Config.get_llm_model()
                if api_key:
                    genai.configure(api_key=api_key)
                    self._model = genai.GenerativeModel(model_name)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
                self._last_mode = True
    
    @property
    def mock_mode(self) -> bool:
        return self._last_mode if self._last_mode is not None else True
    
    async def analyze(
        self,
        error_logs: str,
        git_diff: str,
        build_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze build failure using LLM."""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_analysis(error_logs, git_diff, build_info)
        
        user_prompt = f"""Analyze this build failure:

## Build Information
- Job: {build_info.get('job_name', 'unknown')}
- Build Number: {build_info.get('build_number', 'unknown')}

## Console Output (Error Logs)
```
{error_logs[:Config.MAX_LOG_CHARS]}
```

## Git Diff (Code Changes)
```diff
{git_diff[:Config.MAX_DIFF_CHARS]}
```

Provide your response in JSON format."""

        try:
            response = await asyncio.to_thread(
                self._model.generate_content,
                [self.SYSTEM_PROMPT, user_prompt]
            )
            
            response_text = response.text
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            result["tokens_used"] = getattr(response, 'usage_metadata', {}).get('total_token_count', 0)
            result["model_used"] = await Config.get_llm_model()
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._fallback_analysis(error_logs, str(e))
    
    def _mock_analysis(self, error_logs: str, git_diff: str, build_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock analysis."""
        return {
            "root_cause_summary": "Test failure due to validate_user_email() returning None instead of ValidationResult",
            "error_type": "test_failure",
            "error_message": "AttributeError: 'NoneType' object has no attribute 'is_valid'",
            "suspected_file": "src/api/users.py",
            "suspected_lines": [87, 88, 89],
            "confidence_score": 0.92,
            "fix_suggestion": "Modify validate_user_email to always return ValidationResult",
            "fix_code_snippet": """def validate_user_email(self, email: str) -> ValidationResult:
    if not email:
        return ValidationResult(is_valid=False, error="Email required")
    return ValidationResult(is_valid=True, error=None)""",
            "additional_recommendations": ["Add type hints", "Add more edge case tests"],
            "tokens_used": 1250,
            "model_used": "gemini-1.5-pro (mock)"
        }
    
    def _fallback_analysis(self, error_logs: str, error: str) -> Dict[str, Any]:
        """Fallback analysis when LLM fails."""
        return {
            "root_cause_summary": "Unable to perform full LLM analysis",
            "error_type": "unknown",
            "error_message": error_logs[:500] if error_logs else "Unknown error",
            "suspected_file": None,
            "suspected_lines": [],
            "confidence_score": 0.3,
            "fix_suggestion": f"Please review logs manually. LLM analysis failed: {error}",
            "fix_code_snippet": None,
            "additional_recommendations": ["Review build log", "Check recent commits"],
            "tokens_used": 0,
            "model_used": "fallback-regex"
        }


# ============================================================================
# RCA ENGINE
# ============================================================================

class RcaEngine:
    """Core RCA engine that orchestrates analysis."""
    
    def __init__(self):
        self.jenkins = JenkinsClient()
        self.github = GitHubClient()
        self.llm = RcaLLMClient()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def analyze_build(
        self,
        job_name: str,
        build_number: int,
        repo_name: Optional[str] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        pr_id: Optional[int] = None,
        include_git_diff: bool = True
    ) -> RcaAnalysis:
        """Perform complete RCA analysis on a failed build."""
        start_time = time.time()
        
        # Fetch build info and console output
        logger.info(f"Fetching build info for {job_name}#{build_number}")
        build_info = await self.jenkins.get_build_info(job_name, build_number)
        console_output = await self.jenkins.get_console_output(job_name, build_number)
        
        # Truncate logs
        truncated_logs = console_output[:Config.MAX_LOG_CHARS]
        
        # Fetch git diff if available
        git_diff = ""
        changed_files = []
        
        if include_git_diff:
            if commit_sha:
                git_diff, changed_files = await self.github.get_commit_diff(
                    repo_name or job_name,
                    commit_sha
                )
            elif "changeSet" in build_info:
                changes = build_info.get("changeSet", {}).get("items", [])
                if changes:
                    commit = changes[0].get("commitId")
                    if commit:
                        git_diff, changed_files = await self.github.get_commit_diff(
                            repo_name or job_name,
                            commit
                        )
        
        # Run LLM analysis
        logger.info("Running LLM analysis...")
        llm_result = await self.llm.analyze(truncated_logs, git_diff, build_info)
        
        analysis_duration = time.time() - start_time
        
        # Build suspected files list
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
        
        changes = build_info.get("changeSet", {}).get("items", [])
        suspected_commit = changes[0].get("commitId") if changes else commit_sha
        
        analysis = RcaAnalysis(
            analysis_id=f"rca-{job_name}-{build_number}-{int(time.time())}",
            root_cause_summary=llm_result.get("root_cause_summary", "Unknown"),
            error_type=llm_result.get("error_type", "unknown"),
            error_message=llm_result.get("error_message", ""),
            confidence_score=confidence,
            confidence_level=confidence_level,
            suspected_commit=suspected_commit,
            suspected_author=suspected_author,
            suspected_files=suspected_files,
            test_failures=[],
            error_log_excerpt=truncated_logs[:2000],
            fix_suggestion=llm_result.get("fix_suggestion", ""),
            fix_code_snippet=llm_result.get("fix_code_snippet"),
            additional_recommendations=llm_result.get("additional_recommendations", []),
            analyzed_at=datetime.utcnow(),
            analysis_duration_seconds=analysis_duration,
            model_used=llm_result.get("model_used"),
            tokens_used=llm_result.get("tokens_used", 0)
        )
        
        logger.info(f"RCA complete for {job_name}#{build_number} in {analysis_duration:.2f}s")
        
        return analysis
    
    async def close(self):
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()


# ============================================================================
# MCP SERVER SETUP
# ============================================================================

rca_engine: Optional[RcaEngine] = None

mcp_server = NexusMCPServer(
    name="rca-agent",
    description="MCP server for Root Cause Analysis of build failures",
    version="3.0.0",
    port=int(os.environ.get("PORT", "8006")),
)


@mcp_server.on_startup
async def startup():
    """Initialize on startup."""
    global rca_engine
    rca_engine = RcaEngine()
    logger.info("RCA Agent MCP server started")


@mcp_server.on_shutdown
async def shutdown():
    """Cleanup on shutdown."""
    if rca_engine:
        await rca_engine.close()
    logger.info("RCA Agent MCP server shutdown")


# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp_server.tool(
    name="analyze_build_failure",
    description="Analyze a failed build to determine root cause and suggest fixes",
    category="analysis"
)
async def analyze_build_failure(
    job_name: str,
    build_number: int,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    commit_sha: Optional[str] = None,
    include_git_diff: bool = True
) -> Dict[str, Any]:
    """
    Analyze a failed build to determine root cause.
    
    Args:
        job_name: Jenkins job name
        build_number: Build number to analyze
        repo_name: Repository name (optional)
        branch: Git branch (optional)
        commit_sha: Specific commit to analyze (optional)
        include_git_diff: Include git diff in analysis
        
    Returns:
        RCA analysis with root cause, suspected files, and fix suggestions
    """
    analysis = await rca_engine.analyze_build(
        job_name=job_name,
        build_number=build_number,
        repo_name=repo_name,
        branch=branch,
        commit_sha=commit_sha,
        include_git_diff=include_git_diff
    )
    
    return analysis.model_dump(mode="json")


@mcp_server.tool(
    name="get_build_logs",
    description="Fetch console logs from a Jenkins build",
    category="data"
)
async def get_build_logs(
    job_name: str,
    build_number: int,
    max_lines: int = 500
) -> Dict[str, Any]:
    """
    Get console logs from a Jenkins build.
    
    Args:
        job_name: Jenkins job name
        build_number: Build number
        max_lines: Maximum lines to return
        
    Returns:
        Build logs and basic info
    """
    build_info = await rca_engine.jenkins.get_build_info(job_name, build_number)
    console_output = await rca_engine.jenkins.get_console_output(job_name, build_number)
    
    lines = console_output.split("\n")
    truncated = len(lines) > max_lines
    
    return {
        "job_name": job_name,
        "build_number": build_number,
        "result": build_info.get("result"),
        "url": build_info.get("url"),
        "logs": "\n".join(lines[-max_lines:]) if truncated else console_output,
        "truncated": truncated,
        "total_lines": len(lines)
    }


@mcp_server.tool(
    name="get_commit_changes",
    description="Fetch file changes from a git commit",
    category="data"
)
async def get_commit_changes(
    repo_name: str,
    commit_sha: str
) -> Dict[str, Any]:
    """
    Get file changes from a specific commit.
    
    Args:
        repo_name: Repository name
        commit_sha: Commit SHA
        
    Returns:
        List of changed files with diff information
    """
    diff_text, changed_files = await rca_engine.github.get_commit_diff(repo_name, commit_sha)
    
    return {
        "repo_name": repo_name,
        "commit_sha": commit_sha,
        "files_changed": len(changed_files),
        "files": changed_files,
        "diff_preview": diff_text[:5000] if len(diff_text) > 5000 else diff_text
    }


# ============================================================================
# APPLICATION
# ============================================================================

app = create_mcp_app(mcp_server, enable_health=True, enable_metrics=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8006")),
        reload=os.environ.get("DEBUG", "false").lower() == "true"
    )

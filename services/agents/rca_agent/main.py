"""
Nexus RCA (Root Cause Analysis) Agent
=====================================

Specialized agent for analyzing failed builds to determine:
- Why the build failed
- Which commit/code change caused it
- Suggested fixes

Uses LLM (Google Gemini) to correlate error logs with git diffs.

Author: Nexus Team
Version: 2.1.0
"""

import asyncio
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """RCA Agent configuration."""
    # Jenkins settings
    JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins:8080")
    JENKINS_USERNAME = os.getenv("JENKINS_USERNAME", "")
    JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
    JENKINS_MOCK_MODE = os.getenv("JENKINS_MOCK_MODE", "true").lower() == "true"
    
    # GitHub settings
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_ORG = os.getenv("GITHUB_ORG", "")
    GITHUB_MOCK_MODE = os.getenv("GITHUB_MOCK_MODE", "true").lower() == "true"
    
    # LLM settings (Gemini recommended for larger context)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    LLM_MODEL = os.getenv("RCA_LLM_MODEL", "gemini-1.5-pro")  # Pro has 1M token context
    LLM_MOCK_MODE = os.getenv("LLM_MOCK_MODE", "true").lower() == "true"
    
    # Analysis settings
    MAX_LOG_CHARS = int(os.getenv("RCA_MAX_LOG_CHARS", "100000"))
    MAX_DIFF_CHARS = int(os.getenv("RCA_MAX_DIFF_CHARS", "50000"))
    
    # Service settings
    PORT = int(os.getenv("PORT", "8006"))

# =============================================================================
# Prometheus Metrics
# =============================================================================

RCA_REQUESTS = Counter(
    "nexus_rca_requests_total",
    "Total RCA analysis requests",
    ["status", "error_type"]
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
    additional_recommendations: List[str] = []
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration_seconds: float = 0.0
    model_used: Optional[str] = None
    tokens_used: int = 0


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
    """
    
    def __init__(self):
        self.jenkins = JenkinsClient()
        self.github = GitHubClient()
        self.llm = RcaLLMClient()
    
    async def analyze_build(self, request: RcaRequest) -> RcaAnalysis:
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
            RCA_REQUESTS.labels(status="success", error_type=analysis.error_type).inc()
            RCA_DURATION.labels(job_name=request.job_name).observe(analysis_duration)
            RCA_CONFIDENCE.observe(confidence)
            
            logger.info(f"RCA complete for {request.job_name}#{request.build_number} in {analysis_duration:.2f}s")
            
            return analysis
            
        except Exception as e:
            RCA_REQUESTS.labels(status="error", error_type="exception").inc()
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
    
    yield
    
    logger.info("👋 RCA Agent shutdown complete")


app = FastAPI(
    title="Nexus RCA Agent",
    description="Smart Root Cause Analysis for build failures",
    version="2.1.0",
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
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "jenkins_mock": Config.JENKINS_MOCK_MODE,
            "github_mock": Config.GITHUB_MOCK_MODE,
            "llm_mock": Config.LLM_MOCK_MODE,
            "llm_model": Config.LLM_MODEL
        }
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/analyze", response_model=RcaAnalysis)
async def analyze_build_failure(request: RcaRequest):
    """
    Analyze a failed build to determine root cause.
    
    This endpoint:
    1. Fetches the build console output from Jenkins
    2. Fetches git diffs for commits in the build
    3. Uses LLM to correlate errors with code changes
    4. Returns structured root cause analysis with fix suggestions
    """
    return await rca_engine.analyze_build(request)


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
        analysis = await rca_engine.analyze_build(rca_request)
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


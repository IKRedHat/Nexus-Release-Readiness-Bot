"""
Nexus Git/CI Agent
Handles GitHub repository operations and Jenkins/CI pipeline management
"""
import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from prometheus_client import Counter

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    BuildStatus,
    BuildResult,
    BuildArtifact,
    BuildTestResult,
    PRStatus,
    RepositoryHealth,
    SecurityScanResult,
    Vulnerability,
    SeverityLevel,
    TaskStatus,
    AgentType,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import (
    setup_tracing,
    track_tool_usage,
    create_metrics_endpoint,
)
from nexus_lib.utils import generate_task_id, utc_now

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.git-ci-agent")


# ============================================================================
# GITHUB CLIENT WRAPPER
# ============================================================================

class GitHubClient:
    """
    Wrapper for GitHub API interactions using PyGithub
    """
    
    def __init__(self):
        self.mock_mode = os.environ.get("GITHUB_MOCK_MODE", "true").lower() == "true"
        self.github = None
        
        if not self.mock_mode:
            try:
                from github import Github, Auth
                
                token = os.environ.get("GITHUB_TOKEN")
                if token:
                    auth = Auth.Token(token)
                    self.github = Github(auth=auth)
                    # Verify connection
                    self.github.get_user().login
                    logger.info("GitHub client initialized in LIVE mode")
                else:
                    logger.warning("GITHUB_TOKEN not set, falling back to mock mode")
                    self.mock_mode = True
            except ImportError:
                logger.warning("PyGithub not installed, falling back to mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            logger.info("GitHub client running in MOCK mode")
    
    def get_repo_health(self, repo_name: str) -> RepositoryHealth:
        """Get repository health metrics"""
        if self.mock_mode:
            return self._mock_repo_health(repo_name)
        
        try:
            repo = self.github.get_repo(repo_name)
            default_branch = repo.default_branch
            
            # Get latest commit status
            branch = repo.get_branch(default_branch)
            commit = repo.get_commit(branch.commit.sha)
            
            # Get combined status
            status = commit.get_combined_status()
            status_state = status.state if status else "unknown"
            
            # Count PRs
            open_prs = repo.get_pulls(state="open")
            open_pr_count = open_prs.totalCount
            
            # Count stale PRs (> 7 days old)
            week_ago = datetime.now() - timedelta(days=7)
            stale_count = sum(1 for pr in open_prs if pr.created_at < week_ago)
            
            # Get branch protection
            protection = None
            try:
                protection = branch.get_protection()
            except:
                pass
            
            return RepositoryHealth(
                repo_name=repo_name,
                default_branch=default_branch,
                latest_commit_sha=branch.commit.sha,
                latest_commit_status=status_state,
                branch_protection_enabled=protection is not None,
                required_reviews=protection.required_pull_request_reviews.required_approving_review_count if protection and protection.required_pull_request_reviews else 0,
                open_prs=open_pr_count,
                stale_prs=stale_count,
                open_issues=repo.open_issues_count
            )
        except Exception as e:
            logger.error(f"Failed to get repo health: {e}")
            raise
    
    def get_pr_status(self, repo_name: str, pr_number: int) -> PRStatus:
        """Get pull request status and details"""
        if self.mock_mode:
            return self._mock_pr_status(repo_name, pr_number)
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get CI status
            commits = pr.get_commits()
            last_commit = list(commits)[-1] if commits.totalCount > 0 else None
            ci_status = None
            if last_commit:
                status = last_commit.get_combined_status()
                ci_status = status.state
            
            # Count approvals
            reviews = pr.get_reviews()
            approvals = sum(1 for r in reviews if r.state == "APPROVED")
            changes_requested = any(r.state == "CHANGES_REQUESTED" for r in reviews)
            
            return PRStatus(
                pr_number=pr_number,
                title=pr.title,
                state=pr.state,
                author=pr.user.login,
                base_branch=pr.base.ref,
                head_branch=pr.head.ref,
                url=pr.html_url,
                mergeable=pr.mergeable,
                merged=pr.merged,
                merged_by=pr.merged_by.login if pr.merged_by else None,
                merged_at=pr.merged_at,
                ci_status=ci_status,
                approvals=approvals,
                changes_requested=changes_requested,
                additions=pr.additions,
                deletions=pr.deletions,
                changed_files=pr.changed_files,
                commits=pr.commits,
                comments=pr.comments,
                created_at=pr.created_at,
                updated_at=pr.updated_at
            )
        except Exception as e:
            logger.error(f"Failed to get PR status: {e}")
            raise
    
    def list_open_prs(self, repo_name: str) -> List[PRStatus]:
        """List all open PRs for a repository"""
        if self.mock_mode:
            return [self._mock_pr_status(repo_name, i) for i in range(1, 4)]
        
        try:
            repo = self.github.get_repo(repo_name)
            prs = repo.get_pulls(state="open", sort="updated", direction="desc")
            
            return [
                PRStatus(
                    pr_number=pr.number,
                    title=pr.title,
                    state=pr.state,
                    author=pr.user.login,
                    base_branch=pr.base.ref,
                    head_branch=pr.head.ref,
                    url=pr.html_url,
                    created_at=pr.created_at,
                    updated_at=pr.updated_at
                )
                for pr in prs[:20]  # Limit to 20 PRs
            ]
        except Exception as e:
            logger.error(f"Failed to list PRs: {e}")
            raise
    
    def _mock_repo_health(self, repo_name: str) -> RepositoryHealth:
        """Generate mock repository health data"""
        return RepositoryHealth(
            repo_name=repo_name,
            default_branch="main",
            latest_commit_sha="abc1234def5678",
            latest_commit_status="success",
            branch_protection_enabled=True,
            required_reviews=2,
            open_prs=5,
            stale_prs=1,
            open_issues=12,
            last_successful_build=datetime.now() - timedelta(hours=2),
            build_frequency_per_week=15.5,
            average_build_duration_minutes=8.5
        )
    
    def _mock_pr_status(self, repo_name: str, pr_number: int) -> PRStatus:
        """Generate mock PR status"""
        return PRStatus(
            pr_number=pr_number,
            title=f"[Demo] Feature implementation PR #{pr_number}",
            state="open",
            author="developer",
            base_branch="main",
            head_branch=f"feature/demo-{pr_number}",
            url=f"https://github.com/{repo_name}/pull/{pr_number}",
            mergeable=True,
            merged=False,
            ci_status="success",
            required_checks_passed=True,
            approvals=2,
            changes_requested=False,
            additions=150,
            deletions=30,
            changed_files=8,
            commits=5,
            comments=3,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(hours=3)
        )


# ============================================================================
# JENKINS CLIENT WRAPPER
# ============================================================================

class JenkinsClient:
    """
    Wrapper for Jenkins API interactions using python-jenkins
    """
    
    def __init__(self):
        self.mock_mode = os.environ.get("JENKINS_MOCK_MODE", "true").lower() == "true"
        self.jenkins = None
        
        if not self.mock_mode:
            try:
                import jenkins
                
                url = os.environ.get("JENKINS_URL")
                username = os.environ.get("JENKINS_USERNAME")
                token = os.environ.get("JENKINS_API_TOKEN")
                
                if url and username and token:
                    self.jenkins = jenkins.Jenkins(url, username=username, password=token)
                    # Verify connection
                    self.jenkins.get_whoami()
                    logger.info("Jenkins client initialized in LIVE mode")
                else:
                    logger.warning("Jenkins credentials not set, falling back to mock mode")
                    self.mock_mode = True
            except ImportError:
                logger.warning("python-jenkins not installed, falling back to mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Jenkins client: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            logger.info("Jenkins client running in MOCK mode")
    
    def get_build_status(self, job_name: str, build_number: Optional[int] = None) -> BuildStatus:
        """Get build status for a job"""
        if self.mock_mode:
            return self._mock_build_status(job_name, build_number or 42)
        
        try:
            if build_number:
                build_info = self.jenkins.get_build_info(job_name, build_number)
            else:
                # Get last build
                job_info = self.jenkins.get_job_info(job_name)
                build_number = job_info["lastBuild"]["number"]
                build_info = self.jenkins.get_build_info(job_name, build_number)
            
            # Parse test results if available
            test_results = None
            for action in build_info.get("actions", []):
                if action.get("_class", "").endswith("TestResultAction"):
                    test_results = BuildTestResult(
                        total_tests=action.get("totalCount", 0),
                        passed=action.get("totalCount", 0) - action.get("failCount", 0) - action.get("skipCount", 0),
                        failed=action.get("failCount", 0),
                        skipped=action.get("skipCount", 0),
                        duration_seconds=build_info.get("duration", 0) / 1000
                    )
                    break
            
            # Parse artifacts
            artifacts = [
                BuildArtifact(
                    name=a["fileName"],
                    path=a["relativePath"],
                    url=f"{build_info['url']}artifact/{a['relativePath']}"
                )
                for a in build_info.get("artifacts", [])
            ]
            
            return BuildStatus(
                job_name=job_name,
                build_number=build_number,
                status=BuildResult[build_info.get("result", "BUILDING") or "BUILDING"],
                url=build_info["url"],
                timestamp=datetime.fromtimestamp(build_info["timestamp"] / 1000),
                duration_seconds=build_info.get("duration", 0) / 1000,
                triggered_by=build_info.get("displayName"),
                artifacts=artifacts,
                test_results=test_results,
                console_log_url=f"{build_info['url']}console"
            )
        except Exception as e:
            logger.error(f"Failed to get build status: {e}")
            raise
    
    def trigger_build(self, job_name: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Trigger a new build"""
        if self.mock_mode:
            logger.info(f"[MOCK] Triggered build for {job_name} with params: {parameters}")
            return {"queue_id": 12345, "message": "Build queued (mock)"}
        
        try:
            if parameters:
                queue_id = self.jenkins.build_job(job_name, parameters=parameters)
            else:
                queue_id = self.jenkins.build_job(job_name)
            
            return {
                "queue_id": queue_id,
                "message": f"Build queued for {job_name}"
            }
        except Exception as e:
            logger.error(f"Failed to trigger build: {e}")
            raise
    
    def get_job_history(self, job_name: str, limit: int = 10) -> List[BuildStatus]:
        """Get build history for a job"""
        if self.mock_mode:
            return [self._mock_build_status(job_name, 42 - i) for i in range(limit)]
        
        try:
            job_info = self.jenkins.get_job_info(job_name)
            builds = job_info.get("builds", [])[:limit]
            
            return [
                self.get_build_status(job_name, b["number"])
                for b in builds
            ]
        except Exception as e:
            logger.error(f"Failed to get job history: {e}")
            raise
    
    def _mock_build_status(self, job_name: str, build_number: int) -> BuildStatus:
        """Generate mock build status"""
        statuses = [BuildResult.SUCCESS, BuildResult.SUCCESS, BuildResult.SUCCESS, BuildResult.FAILURE, BuildResult.UNSTABLE]
        status = statuses[build_number % len(statuses)]
        
        return BuildStatus(
            job_name=job_name,
            build_number=build_number,
            status=status,
            url=f"https://jenkins.example.com/job/{job_name}/{build_number}/",
            timestamp=datetime.now() - timedelta(hours=build_number),
            duration_seconds=480.5,
            branch="main",
            commit_sha="abc1234def5678",
            commit_message="feat: Add new feature implementation",
            commit_author="developer@example.com",
            triggered_by="GitHub webhook",
            artifacts=[
                BuildArtifact(
                    name="app.jar",
                    path="target/app.jar",
                    url=f"https://jenkins.example.com/job/{job_name}/{build_number}/artifact/target/app.jar"
                )
            ],
            test_results=BuildTestResult(
                total_tests=245,
                passed=240 if status == BuildResult.SUCCESS else 220,
                failed=0 if status == BuildResult.SUCCESS else 25,
                skipped=5,
                duration_seconds=120.5,
                coverage_percentage=85.5
            ),
            console_log_url=f"https://jenkins.example.com/job/{job_name}/{build_number}/console"
        )


# ============================================================================
# SECURITY SCANNER CLIENT
# ============================================================================

class SecurityScannerClient:
    """Mock security scanner integration"""
    
    def __init__(self):
        self.mock_mode = True
        logger.info("Security scanner running in MOCK mode")
    
    def get_security_scan(self, repo_name: str, branch: str = "main") -> SecurityScanResult:
        """Get security scan results"""
        # In production, integrate with tools like:
        # - Snyk
        # - Dependabot
        # - SonarQube
        # - Trivy
        
        return SecurityScanResult(
            repo_name=repo_name,
            branch=branch,
            commit_sha="abc1234",
            scanner_name="nexus-security-scanner",
            scanner_version="1.0.0",
            scan_timestamp=datetime.now(),
            scan_duration_seconds=45.2,
            risk_score=25,
            risk_level=SeverityLevel.LOW,
            critical_vulnerabilities=0,
            high_vulnerabilities=2,
            medium_vulnerabilities=5,
            low_vulnerabilities=12,
            info_vulnerabilities=8,
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-12345",
                    title="Prototype Pollution in lodash",
                    severity=SeverityLevel.HIGH,
                    cvss_score=7.5,
                    package_name="lodash",
                    package_version="4.17.20",
                    fixed_in_version="4.17.21",
                    remediation="Upgrade lodash to version 4.17.21 or later"
                ),
                Vulnerability(
                    id="CVE-2023-67890",
                    title="SQL Injection in mysql driver",
                    severity=SeverityLevel.HIGH,
                    cvss_score=8.1,
                    package_name="mysql2",
                    package_version="2.3.0",
                    fixed_in_version="2.3.1"
                )
            ],
            total_dependencies=156,
            vulnerable_dependencies=3,
            outdated_dependencies=12,
            secrets_detected=0,
            compliant=True,
            report_url=f"https://security.example.com/reports/{repo_name}/latest"
        )


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

github_client: Optional[GitHubClient] = None
jenkins_client: Optional[JenkinsClient] = None
security_client: Optional[SecurityScannerClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global github_client, jenkins_client, security_client
    
    # Startup
    setup_tracing("git-ci-agent", service_version="1.0.0")
    github_client = GitHubClient()
    jenkins_client = JenkinsClient()
    security_client = SecurityScannerClient()
    logger.info("Git/CI Agent started")
    
    yield
    
    # Shutdown
    logger.info("Git/CI Agent shutting down")


app = FastAPI(
    title="Nexus Git/CI Agent",
    description="Agent for GitHub and Jenkins/CI operations in the Nexus release automation system",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware, agent_type="git_ci")
app.add_middleware(
    AuthMiddleware,
    secret_key=os.environ.get("NEXUS_JWT_SECRET"),
    require_auth=os.environ.get("NEXUS_REQUIRE_AUTH", "false").lower() == "true"
)

# Add metrics endpoint
create_metrics_endpoint(app)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "git-ci-agent",
        "github_mock": github_client.mock_mode if github_client else True,
        "jenkins_mock": jenkins_client.mock_mode if jenkins_client else True
    }


@app.get("/repo/{repo_name:path}/health", response_model=AgentTaskResponse)
@track_tool_usage("check_repo_health", agent_type="git_ci")
async def get_repo_health(repo_name: str):
    """
    Get repository health metrics
    """
    task_id = generate_task_id("git")
    
    try:
        health = github_client.get_repo_health(repo_name)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=health.model_dump(mode="json"),
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to get repo health: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.get("/repo/{repo_name:path}/pr/{pr_number}", response_model=AgentTaskResponse)
@track_tool_usage("check_pr_status", agent_type="git_ci")
async def get_pr_status(repo_name: str, pr_number: int):
    """
    Get pull request status
    """
    task_id = generate_task_id("git")
    
    try:
        pr_status = github_client.get_pr_status(repo_name, pr_number)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=pr_status.model_dump(mode="json"),
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to get PR status: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.get("/repo/{repo_name:path}/prs", response_model=AgentTaskResponse)
@track_tool_usage("list_open_prs", agent_type="git_ci")
async def list_open_prs(repo_name: str):
    """
    List open pull requests
    """
    task_id = generate_task_id("git")
    
    try:
        prs = github_client.list_open_prs(repo_name)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={"prs": [pr.model_dump(mode="json") for pr in prs]},
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to list PRs: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.post("/build/{job_name}", response_model=AgentTaskResponse)
@track_tool_usage("trigger_jenkins_build", agent_type="git_ci")
async def trigger_build(
    job_name: str,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Trigger a Jenkins build
    """
    task_id = generate_task_id("jenkins")
    
    try:
        result = jenkins_client.trigger_build(job_name, parameters)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=result,
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to trigger build: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.get("/build/{job_name}/status", response_model=AgentTaskResponse)
@track_tool_usage("get_build_status", agent_type="git_ci")
async def get_build_status(
    job_name: str,
    build_number: Optional[int] = Query(None, description="Build number (default: latest)")
):
    """
    Get build status
    """
    task_id = generate_task_id("jenkins")
    
    try:
        status = jenkins_client.get_build_status(job_name, build_number)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=status.model_dump(mode="json"),
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to get build status: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.get("/build/{job_name}/history", response_model=AgentTaskResponse)
@track_tool_usage("get_build_history", agent_type="git_ci")
async def get_build_history(
    job_name: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get build history for a job
    """
    task_id = generate_task_id("jenkins")
    
    try:
        history = jenkins_client.get_job_history(job_name, limit)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={"builds": [b.model_dump(mode="json") for b in history]},
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to get build history: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.get("/security/{repo_name:path}", response_model=AgentTaskResponse)
@track_tool_usage("get_security_scan", agent_type="git_ci")
async def get_security_scan(
    repo_name: str,
    branch: str = Query("main", description="Branch to scan")
):
    """
    Get security scan results for a repository
    """
    task_id = generate_task_id("security")
    
    try:
        scan = security_client.get_security_scan(repo_name, branch)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=scan.model_dump(mode="json"),
            agent_type=AgentType.GIT_CI
        )
    except Exception as e:
        logger.error(f"Failed to get security scan: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.GIT_CI
        )


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Generic task execution endpoint for orchestrator integration
    """
    action = request.action
    payload = request.payload
    
    # Route to appropriate handler
    if action == "repo_health":
        return await get_repo_health(payload.get("repo_name"))
    elif action == "pr_status":
        return await get_pr_status(payload.get("repo_name"), payload.get("pr_number"))
    elif action == "list_prs":
        return await list_open_prs(payload.get("repo_name"))
    elif action == "trigger_build":
        return await trigger_build(payload.get("job_name"), payload.get("parameters"))
    elif action == "build_status":
        return await get_build_status(payload.get("job_name"), payload.get("build_number"))
    elif action == "build_history":
        return await get_build_history(payload.get("job_name"), payload.get("limit", 10))
    elif action == "security_scan":
        return await get_security_scan(payload.get("repo_name"), payload.get("branch", "main"))
    else:
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Unknown action: {action}",
            agent_type=AgentType.GIT_CI
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

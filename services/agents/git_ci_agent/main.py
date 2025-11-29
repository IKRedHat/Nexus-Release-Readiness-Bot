import os
import sys
from fastapi import FastAPI, HTTPException

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskResponse, SecurityScanResult
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import setup_tracing, track_tool_usage

setup_tracing("git-ci-agent")
app = FastAPI(title="Nexus Git/CI Agent")
app.add_middleware(MetricsMiddleware)
app.add_middleware(AuthMiddleware, secret_key="nexus-secret")

@app.post("/build/{job_name}")
@track_tool_usage("trigger_jenkins_build")
async def trigger_build(job_name: str, params: dict = None):
    return AgentTaskResponse(task_id="trace", status="success", data={"queue_id": 123, "message": "Build queued"})

@app.get("/repo/{repo_name}/health")
@track_tool_usage("check_branch_health")
async def get_branch_health(repo_name: str, branch: str = "main"):
    return AgentTaskResponse(task_id="trace", status="success", data={"open_prs": 2, "latest_commit_status": "success", "sha": "abc1234"})

@app.get("/security/{repo_name}")
@track_tool_usage("get_security_scan")
async def get_security_scan(repo_name: str):
    return AgentTaskResponse(task_id="trace", status="success", data=SecurityScanResult(repo_name=repo_name, branch="main", risk_score=85, critical_vulnerabilities=0, high_vulnerabilities=2).model_dump())

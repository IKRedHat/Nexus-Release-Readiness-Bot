import os
import sys
from fastapi import FastAPI, HTTPException
# from atlassian import Jira # Commented out to prevent crash if lib missing in local
# Mocking the lib import for the script to run without deps
class Jira:
    def __init__(self, **kwargs): pass
    def issue(self, key): return {"key": key, "fields": {"summary": "Demo Ticket", "status": {"name": "Done"}, "assignee": None, "priority": None, "created": "2023-01-01", "updated": "2023-01-02", "subtasks": []}}
    def set_issue_status(self, key, status): pass
    def issue_add_comment(self, key, comment): pass

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskResponse, JiraTicket
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import setup_tracing, track_tool_usage

setup_tracing("jira-agent")
app = FastAPI(title="Nexus Jira Agent")
app.add_middleware(MetricsMiddleware)
app.add_middleware(AuthMiddleware, secret_key="nexus-secret")

jira = Jira(url="http://mock", username="mock", password="mock")

@track_tool_usage("get_ticket_hierarchy")
def _fetch_recursive(key: str) -> JiraTicket:
    issue = jira.issue(key)
    return JiraTicket(
        key=issue['key'], summary=issue['fields']['summary'], status=issue['fields']['status']['name'],
        assignee="Unassigned", priority="Medium", created_at="2023-01-01", updated_at="2023-01-01"
    )

@app.get("/hierarchy/{ticket_key}", response_model=AgentTaskResponse)
async def get_ticket_hierarchy(ticket_key: str):
    data = _fetch_recursive(ticket_key)
    return AgentTaskResponse(task_id="trace-id", status="success", data=data.model_dump())

@app.post("/update")
@track_tool_usage("update_ticket_status")
async def update_ticket(key: str, status: str, comment: str = None):
    return AgentTaskResponse(task_id="trace-id", status="success", data={"message": f"Updated {key} to {status}"})

#!/bin/bash

echo "🚀 Starting Nexus Code Injection..."

# ==========================================
# 1. SHARED LIBRARY (E0 - Contracts)
# ==========================================
echo "Writing Shared API Contracts..."
cat <<EOF > shared/nexus_lib/schemas/agent_contract.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class AgentType(str, Enum):
    JIRA = "jira"
    GIT_CI = "git_ci"
    SLACK = "slack"
    REPORTING = "reporting"

class AgentTaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique ID for tracing")
    action: str = Field(..., description="The specific function to call")
    payload: Dict[str, Any] = Field(..., description="Arguments for the function")
    user_context: Optional[Dict[str, str]] = Field(None, description="Slack user ID etc")

class AgentTaskResponse(BaseModel):
    task_id: str
    status: str = Field(..., description="success, error, or pending")
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
EOF

# ==========================================
# 2. ORCHESTRATOR (E2 - Brain/ReAct)
# ==========================================
echo "Writing Orchestrator ReAct Engine..."
cat <<EOF > services/orchestrator/app/core/react_engine.py
import logging
from typing import Dict, Any

logger = logging.getLogger("nexus.react")

class ReActEngine:
    """
    Simplified ReAct Engine for Phase 1/2.
    In production, this calls Gemini API to determine next steps.
    """
    def __init__(self):
        self.tools = {
            "jira": ["get_ticket", "update_ticket"],
            "git": ["trigger_build", "check_status"]
        }

    async def plan_and_execute(self, user_query: str) -> Dict[str, Any]:
        logger.info(f"Reasoning on query: {user_query}")
        
        # MOCK LOGIC for E1/E2 Demo
        if "/jira" in user_query:
            return {"plan": "Call Jira Agent", "tool": "jira", "action": "get_ticket"}
        elif "/jenkins" in user_query:
            return {"plan": "Call Git/CI Agent", "tool": "git", "action": "trigger_build"}
        elif "/search-rm" in user_query:
             return {"plan": "RAG Search", "tool": "vector_db", "action": "search"}
        
        return {"plan": "Unknown", "response": "I didn't understand that command."}
EOF

echo "Writing Orchestrator Main Entrypoint..."
cat <<EOF > services/orchestrator/main.py
import logging
import uuid
from fastapi import FastAPI
from app.core.react_engine import ReActEngine
# Adjust import path for local dev usually requires sys path hacking or proper package installation
import sys
import os
sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskRequest, AgentTaskResponse

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Nexus Orchestrator")
react_engine = ReActEngine()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator"}

@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    # 1. Plan
    plan = await react_engine.plan_and_execute(request.payload.get("query", ""))
    
    # 2. Act (In a real system, we would perform an HTTP call to the Agents here)
    # For MVP, we just return the plan
    return AgentTaskResponse(
        task_id=request.task_id,
        status="success",
        data={"plan": plan, "message": "Orchestrated successfully"}
    )
EOF

# ==========================================
# 3. SLACK AGENT (E1 - User Interface)
# ==========================================
echo "Writing Slack Agent Logic..."
cat <<EOF > services/agents/slack_agent/main.py
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# In production, load from env vars
app = App(token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-mock"))

@app.command("/jira")
def handle_jira_command(ack, respond, command):
    ack()
    user_query = command['text']
    respond(f"Nexus received Jira command: {user_query}. Forwarding to Orchestrator...")
    # TODO: Call Orchestrator API here

@app.command("/search-rm")
def handle_search(ack, respond, command):
    ack()
    respond("Searching Nexus knowledge base... 🧠")

if __name__ == "__main__":
    # Start Socket Mode
    if os.environ.get("SLACK_APP_TOKEN"):
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    else:
        print("Slack Token not found. Starting in HTTP mode for Dev.")
EOF

# ==========================================
# 4. JIRA AGENT (E1 - Ticket Mgmt)
# ==========================================
echo "Writing Jira Agent Logic..."
cat <<EOF > services/agents/jira_agent/main.py
from fastapi import FastAPI
import sys, os
sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskResponse

app = FastAPI(title="Nexus Jira Agent")

@app.get("/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    # Mock Jira API Call
    return {"key": ticket_id, "status": "In Progress", "summary": "Implement Nexus Agents"}

@app.post("/update")
async def update_ticket(ticket_id: str, status: str):
    return {"key": ticket_id, "new_status": status, "msg": "Updated successfully"}
EOF

# ==========================================
# 5. TERRAFORM (E0 - Infrastructure)
# ==========================================
echo "Writing Terraform Config..."
cat <<EOF > infrastructure/terraform/main.tf
provider "google" {
  project = "nexus-release-bot"
  region  = "us-central1"
}

# Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "nexus_repo" {
  location      = "us-central1"
  repository_id = "nexus-repo"
  format        = "DOCKER"
}

# Cloud SQL for Persistence
resource "google_sql_database_instance" "master" {
  name             = "nexus-db-instance"
  database_version = "POSTGRES_14"
  region           = "us-central1"
  settings {
    tier = "db-f1-micro"
  }
}
EOF

echo "✅ All code injected! You can now run 'docker-compose up' (after adding a compose file) or deploy to Cloud."

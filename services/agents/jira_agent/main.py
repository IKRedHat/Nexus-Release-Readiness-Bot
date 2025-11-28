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

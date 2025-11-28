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

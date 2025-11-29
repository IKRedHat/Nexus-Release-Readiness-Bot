import os
import sys
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskRequest, AgentTaskResponse
from nexus_lib.middleware import MetricsMiddleware
from nexus_lib.instrumentation import setup_tracing
from app.core.react_engine import ReActEngine
from app.core.memory import VectorMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.orchestrator")
react_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global react_engine
    setup_tracing("central-orchestrator")
    react_engine = ReActEngine(memory_client=VectorMemory())
    yield
    await react_engine.http_client.close()

app = FastAPI(title="Nexus Central Orchestrator", lifespan=lifespan)
app.add_middleware(MetricsMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    logger.info(f"Received Task {request.task_id}")
    result = await react_engine.run(request.payload.get("query", ""), request.user_context or {})
    return AgentTaskResponse(task_id=request.task_id, status="success", data=result)

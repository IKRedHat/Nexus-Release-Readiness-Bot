"""
Nexus Central Orchestrator
Main FastAPI application for the orchestration service
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    TaskStatus,
    AgentType,
    HealthCheck,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware, RequestIdMiddleware
from nexus_lib.instrumentation import setup_tracing, create_metrics_endpoint
from nexus_lib.utils import generate_task_id
from nexus_lib.specialists import (
    specialist_registry,
    SpecialistStatus,
    SPECIALIST_DEFINITIONS,
)

from app.core.react_engine import ReActEngine
from app.core.memory import VectorMemory, ConversationMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.orchestrator")

# Global instances
react_engine: Optional[ReActEngine] = None
vector_memory: Optional[VectorMemory] = None
conversation_memory: Optional[ConversationMemory] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global react_engine, vector_memory, conversation_memory
    
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Nexus Central Orchestrator v2.3.0")
    logger.info("=" * 60)
    
    setup_tracing("central-orchestrator", service_version="2.3.0")
    
    # Initialize memory systems
    logger.info("Initializing memory systems...")
    vector_memory = VectorMemory()
    conversation_memory = ConversationMemory()
    
    # Initialize ReAct engine
    logger.info("Initializing ReAct reasoning engine...")
    react_engine = ReActEngine(
        memory_client=vector_memory,
        max_iterations=int(os.environ.get("MAX_REACT_ITERATIONS", "10"))
    )
    
    # Register and verify specialist agents
    logger.info("-" * 60)
    logger.info("SPECIALIST AGENT REGISTRATION")
    logger.info("-" * 60)
    logger.info(f"Registered {len(SPECIALIST_DEFINITIONS)} specialist agents:")
    
    for spec_id, definition in SPECIALIST_DEFINITIONS.items():
        url = specialist_registry.get_url(spec_id)
        critical = "⚠️  CRITICAL" if definition.is_critical else ""
        logger.info(f"  • {definition.name} ({spec_id})")
        logger.info(f"    URL: {url}")
        logger.info(f"    Tools: {len(definition.tools)} | Category: {definition.category.value} {critical}")
    
    # Verify specialist health
    logger.info("-" * 60)
    logger.info("SPECIALIST HEALTH CHECK")
    logger.info("-" * 60)
    
    health_results = await specialist_registry.check_all_health()
    healthy_count = sum(1 for h in health_results.values() if h.status == SpecialistStatus.HEALTHY)
    
    for spec_id, health in health_results.items():
        definition = SPECIALIST_DEFINITIONS.get(spec_id)
        status_icon = "✅" if health.status == SpecialistStatus.HEALTHY else "❌"
        logger.info(f"  {status_icon} {definition.name if definition else spec_id}: {health.status.value}")
        if health.error_message:
            logger.warning(f"      Error: {health.error_message}")
        elif health.response_time_ms:
            logger.info(f"      Response time: {health.response_time_ms:.0f}ms")
    
    logger.info(f"\nHealthy specialists: {healthy_count}/{len(SPECIALIST_DEFINITIONS)}")
    
    # Check critical specialists
    all_critical_healthy, unhealthy_critical = await specialist_registry.verify_critical_specialists()
    if not all_critical_healthy:
        logger.warning(f"⚠️  Critical specialists unavailable: {unhealthy_critical}")
        logger.warning("   Some features may be limited until these services are available.")
    else:
        logger.info("✅ All critical specialists are healthy")
    
    # Start background health monitoring
    await specialist_registry.start_health_monitoring()
    
    logger.info("-" * 60)
    logger.info("Nexus Central Orchestrator started successfully")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nexus Central Orchestrator...")
    
    # Stop health monitoring
    await specialist_registry.stop_health_monitoring()
    
    if react_engine:
        await react_engine.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Nexus Central Orchestrator",
    description="""
    The brain of the Nexus Release Automation System.
    
    This service orchestrates multiple specialized agents to automate release readiness 
    assessments using a ReAct (Reasoning + Acting) architecture.
    
    ## Features
    - Natural language query processing
    - Multi-agent coordination
    - RAG-enhanced memory for context
    - Go/No-Go release decisions
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(MetricsMiddleware, agent_type="orchestrator")
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

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    
    Returns the current health status of the orchestrator and its dependencies.
    """
    memory_stats = await vector_memory.get_stats() if vector_memory else {}
    specialist_summary = specialist_registry.get_status_summary()
    
    return HealthCheck(
        status="healthy",
        service="central-orchestrator",
        version="2.3.0",
        dependencies={
            "memory_backend": memory_stats.get("backend", "unknown"),
            "memory_count": str(memory_stats.get("count", 0)),
            "react_engine": "ready" if react_engine else "not_initialized",
            "specialists_healthy": str(specialist_summary.get("healthy", 0)),
            "specialists_total": str(specialist_summary.get("total", 0))
        }
    )


@app.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe
    """
    if not react_engine:
        raise HTTPException(status_code=503, detail="ReAct engine not initialized")
    return {"status": "ready"}


@app.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe
    """
    return {"status": "alive"}


# ============================================================================
# SPECIALIST MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/specialists")
async def list_specialists():
    """
    List all registered specialist agents
    
    Returns a summary of all specialists including their status, capabilities,
    and health information.
    """
    summary = specialist_registry.get_status_summary()
    
    # Add tools information for each specialist
    for spec_id, spec_info in summary["specialists"].items():
        definition = SPECIALIST_DEFINITIONS.get(spec_id)
        if definition:
            spec_info["tools"] = [
                {"name": t.name, "description": t.description}
                for t in definition.tools
            ]
            spec_info["dependencies"] = definition.dependencies
    
    return {
        "orchestrator_version": "2.3.0",
        "total_specialists": summary["total"],
        "healthy": summary["healthy"],
        "degraded": summary["degraded"],
        "unhealthy": summary["unhealthy"],
        "specialists": summary["specialists"]
    }


@app.get("/specialists/{specialist_id}")
async def get_specialist(specialist_id: str):
    """
    Get detailed information about a specific specialist
    
    Returns complete definition, health status, and all available tools.
    """
    definition = SPECIALIST_DEFINITIONS.get(specialist_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Specialist '{specialist_id}' not found")
    
    health = specialist_registry.get_health(specialist_id)
    url = specialist_registry.get_url(specialist_id)
    
    return {
        "id": definition.id,
        "name": definition.name,
        "description": definition.description,
        "category": definition.category.value,
        "is_critical": definition.is_critical,
        "url": url,
        "port": definition.port,
        "health": {
            "status": health.status.value if health else "unknown",
            "last_check": health.last_check.isoformat() if health and health.last_check else None,
            "response_time_ms": health.response_time_ms if health else None,
            "error": health.error_message if health else None,
            "consecutive_failures": health.consecutive_failures if health else 0
        },
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "endpoint": t.endpoint,
                "method": t.method,
                "required_params": t.required_params
            }
            for t in definition.tools
        ],
        "dependencies": definition.dependencies
    }


@app.post("/specialists/{specialist_id}/health")
async def check_specialist_health(specialist_id: str):
    """
    Trigger a health check for a specific specialist
    
    Forces an immediate health check and returns the result.
    """
    definition = SPECIALIST_DEFINITIONS.get(specialist_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Specialist '{specialist_id}' not found")
    
    health = await specialist_registry.check_health(specialist_id)
    
    return {
        "specialist_id": specialist_id,
        "name": definition.name,
        "status": health.status.value,
        "response_time_ms": health.response_time_ms,
        "error": health.error_message,
        "checked_at": health.last_check.isoformat() if health.last_check else None
    }


@app.get("/specialists/tools/all")
async def list_all_tools():
    """
    List all available tools across all specialists
    
    Returns a flat list of all tools that the ReAct engine can use.
    """
    all_tools = specialist_registry.get_all_tools()
    
    tools_list = []
    for tool_name, (spec_id, tool) in all_tools.items():
        definition = SPECIALIST_DEFINITIONS.get(spec_id)
        tools_list.append({
            "name": tool_name,
            "specialist_id": spec_id,
            "specialist_name": definition.name if definition else spec_id,
            "description": tool.description,
            "endpoint": tool.endpoint,
            "method": tool.method,
            "required_params": tool.required_params
        })
    
    return {
        "total_tools": len(tools_list),
        "tools": sorted(tools_list, key=lambda x: x["name"])
    }


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Execute a task using the ReAct engine
    
    This is the main entry point for processing user queries and orchestrating
    multi-agent workflows.
    
    ## Request Body
    - **task_id**: Unique identifier for tracing
    - **action**: The action to perform (typically "process_query")
    - **payload**: Contains the query and any additional parameters
    - **user_context**: Optional user context (Slack user ID, team, etc.)
    
    ## Example
    ```json
    {
        "task_id": "task-123",
        "action": "process_query",
        "payload": {
            "query": "What is the release readiness status for v2.0?"
        },
        "user_context": {
            "user_id": "U123456",
            "team_id": "T123456"
        }
    }
    ```
    """
    try:
        query = request.payload.get("query", "")
        
        if not query:
            return AgentTaskResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error_message="Query is required in payload",
                agent_type=AgentType.ORCHESTRATOR
            )
        
        # Add to conversation memory
        session_id = request.user_context.get("session_id", request.task_id) if request.user_context else request.task_id
        conversation_memory.add_turn(session_id, "user", query)
        
        # Execute ReAct loop
        result = await react_engine.run(query, request.user_context or {})
        
        # Add result to conversation memory
        conversation_memory.add_turn(session_id, "assistant", result.get("result", ""))
        
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.SUCCESS,
            data=result,
            agent_type=AgentType.ORCHESTRATOR
        )
        
    except Exception as e:
        logger.exception(f"Task execution failed: {e}")
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.ORCHESTRATOR
        )


@app.post("/query")
async def simple_query(request: Request):
    """
    Simple query endpoint for quick interactions
    
    Accepts a plain text query and returns the result.
    """
    try:
        body = await request.json()
        query = body.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        task_request = AgentTaskRequest(
            task_id=generate_task_id("query"),
            action="process_query",
            payload={"query": query}
        )
        
        response = await execute_task(task_request)
        
        return {
            "query": query,
            "result": response.data.get("result") if response.data else None,
            "plan": response.data.get("plan") if response.data else None,
            "steps": response.data.get("steps") if response.data else 0,
            "status": response.status.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def get_memory_stats():
    """
    Get memory system statistics
    """
    vector_stats = await vector_memory.get_stats() if vector_memory else {}
    
    return {
        "vector_memory": vector_stats,
        "conversation_sessions": len(conversation_memory.conversations) if conversation_memory else 0
    }


@app.post("/memory/add")
async def add_to_memory(request: Request):
    """
    Add a document to vector memory
    
    Useful for adding release notes, runbooks, or other context documents.
    """
    try:
        body = await request.json()
        doc_id = body.get("doc_id", generate_task_id("doc"))
        content = body.get("content")
        metadata = body.get("metadata", {})
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        await vector_memory.add_context(doc_id, content, metadata)
        
        return {"status": "success", "doc_id": doc_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/search")
async def search_memory(query: str, n_results: int = 3):
    """
    Search vector memory for relevant context
    """
    context = await vector_memory.retrieve(query, n_results)
    return {"query": query, "context": context}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.environ.get("DEBUG") else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=os.environ.get("DEBUG", "false").lower() == "true"
    )

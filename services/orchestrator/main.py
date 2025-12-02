"""
Nexus Central Orchestrator
==========================

The brain of the Nexus Release Automation System.

Architecture: LangGraph StateGraph with MCP Tool Mesh
- Connects to multiple MCP servers for tool access
- Uses LLM Factory for model-agnostic orchestration
- Persists state to PostgreSQL for durability
- Supports human-in-the-loop approval workflows

Author: Nexus Team
Version: 3.0.0
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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

from app.core.graph import GraphEngine, get_graph_engine, close_graph_engine
from app.core.mcp_client import MCPClientManager, get_mcp_manager, close_mcp_manager
from app.core.memory import VectorMemory, ConversationMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.orchestrator")

# Global instances
graph_engine: Optional[GraphEngine] = None
mcp_manager: Optional[MCPClientManager] = None
vector_memory: Optional[VectorMemory] = None
conversation_memory: Optional[ConversationMemory] = None


# =============================================================================
# Request/Response Models
# =============================================================================

class QueryRequest(BaseModel):
    """Simple query request."""
    query: str = Field(..., description="Natural language query")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")


class QueryResponse(BaseModel):
    """Query response."""
    query: str
    result: Optional[str]
    plan: Optional[list]
    steps: int
    thread_id: str
    status: str
    requires_approval: bool = False


class ApprovalRequest(BaseModel):
    """Request to approve/reject a pending action."""
    thread_id: str = Field(..., description="Thread ID to approve")
    approved: bool = Field(..., description="Whether to approve the action")
    comment: Optional[str] = Field(None, description="Optional comment")


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global graph_engine, mcp_manager, vector_memory, conversation_memory
    
    logger.info("Starting Nexus Central Orchestrator v3.0...")
    
    # Setup tracing
    setup_tracing("central-orchestrator", service_version="3.0.0")
    
    # Initialize memory systems
    vector_memory = VectorMemory()
    conversation_memory = ConversationMemory()
    
    # Initialize MCP client manager
    logger.info("Initializing MCP Client Manager...")
    mcp_manager = await get_mcp_manager()
    
    logger.info(f"Connected to {mcp_manager.connected_count} MCP servers with {mcp_manager.total_tools} tools")
    
    # Initialize LangGraph engine with MCP tools
    logger.info("Initializing LangGraph Engine...")
    tools = mcp_manager.get_langchain_tools()
    graph_engine = await get_graph_engine(tools)
    
    logger.info("Nexus Central Orchestrator ready!")
    logger.info(f"  - Architecture: LangGraph + MCP Mesh")
    logger.info(f"  - MCP Servers: {mcp_manager.connected_count}")
    logger.info(f"  - Available Tools: {mcp_manager.total_tools}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nexus Central Orchestrator...")
    
    await close_graph_engine()
    await close_mcp_manager()
    
    logger.info("Shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Nexus Central Orchestrator",
    description="""
    The brain of the Nexus Release Automation System.
    
    ## Architecture
    - **LangGraph**: Stateful orchestration with planning and execution nodes
    - **MCP Mesh**: Connects to specialized agent servers via Model Context Protocol
    - **LLM Factory**: Model-agnostic LLM integration (OpenAI, Gemini, Ollama, etc.)
    
    ## Features
    - Natural language query processing
    - Multi-agent tool orchestration via MCP
    - RAG-enhanced memory for context
    - Human-in-the-loop approval workflows
    - Go/No-Go release decisions
    """,
    version="3.0.0",
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


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    memory_stats = await vector_memory.get_stats() if vector_memory else {}
    
    return HealthCheck(
        status="healthy",
        service="central-orchestrator",
        version="3.0.0",
        dependencies={
            "memory_backend": memory_stats.get("backend", "unknown"),
            "memory_count": str(memory_stats.get("count", 0)),
            "graph_engine": "ready" if graph_engine else "not_initialized",
            "mcp_servers": str(mcp_manager.connected_count if mcp_manager else 0),
            "mcp_tools": str(mcp_manager.total_tools if mcp_manager else 0),
        }
    )


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    if not graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not initialized")
    if not mcp_manager or mcp_manager.connected_count == 0:
        raise HTTPException(status_code=503, detail="No MCP servers connected")
    return {"status": "ready"}


@app.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/status")
async def get_status():
    """Get detailed orchestrator status."""
    mcp_statuses = mcp_manager.get_server_statuses() if mcp_manager else []
    
    return {
        "service": "central-orchestrator",
        "version": "3.0.0",
        "architecture": "LangGraph + MCP Mesh",
        "mcp_servers": [
            {
                "name": s.name,
                "url": s.url,
                "connected": s.connected,
                "tools_count": s.tools_count,
                "last_check": s.last_check.isoformat() if s.last_check else None,
            }
            for s in mcp_statuses
        ],
        "tools": [t.name for t in (mcp_manager.get_all_tools() if mcp_manager else [])],
        "memory": await vector_memory.get_stats() if vector_memory else {},
    }


# =============================================================================
# Query Execution Endpoints
# =============================================================================

@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Execute a task using the LangGraph engine.
    
    This is the main entry point for processing user queries and orchestrating
    multi-agent workflows via MCP.
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
        
        # Use thread_id from request if provided (for LangGraph state)
        thread_id = request.thread_id or request.task_id
        
        # Execute via LangGraph
        result = await graph_engine.run(query, request.user_context or {}, thread_id)
        
        # Add result to conversation memory
        if result.get("result"):
            conversation_memory.add_turn(session_id, "assistant", result["result"])
        
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.SUCCESS if result.get("success") else TaskStatus.FAILED,
            data=result,
            error_message=result.get("error"),
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


@app.post("/query", response_model=QueryResponse)
async def simple_query(request: QueryRequest):
    """
    Simple query endpoint for quick interactions.
    
    Accepts a plain text query and returns the result.
    """
    try:
        task_id = generate_task_id("query")
        thread_id = request.thread_id or task_id
        
        result = await graph_engine.run(request.query, {}, thread_id)
        
        return QueryResponse(
            query=request.query,
            result=result.get("result"),
            plan=result.get("plan"),
            steps=result.get("steps", 0),
            thread_id=result.get("thread_id", thread_id),
            status="success" if result.get("success") else "error",
            requires_approval=result.get("requires_approval", False),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve")
async def approve_action(request: ApprovalRequest):
    """
    Approve or reject a pending action.
    
    Used for human-in-the-loop workflows where certain actions
    (like publishing reports) require approval.
    """
    try:
        approval_status = "approved" if request.approved else "rejected"
        
        result = await graph_engine.resume(
            thread_id=request.thread_id,
            approval_status=approval_status,
        )
        
        return {
            "thread_id": request.thread_id,
            "approval_status": approval_status,
            "result": result.get("result"),
            "success": result.get("success", False),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/thread/{thread_id}")
async def get_thread_state(thread_id: str):
    """
    Get the current state of a conversation thread.
    
    Useful for debugging and resuming conversations.
    """
    state = await graph_engine.get_state(thread_id)
    
    if not state:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    return {
        "thread_id": thread_id,
        "query": state.get("query"),
        "current_step": state.get("current_step"),
        "final_answer": state.get("final_answer"),
        "requires_approval": state.get("requires_approval"),
        "approval_status": state.get("approval_status"),
        "tool_results_count": len(state.get("tool_results", [])),
    }


# =============================================================================
# Memory Endpoints
# =============================================================================

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    vector_stats = await vector_memory.get_stats() if vector_memory else {}
    
    return {
        "vector_memory": vector_stats,
        "conversation_sessions": len(conversation_memory.conversations) if conversation_memory else 0
    }


@app.post("/memory/add")
async def add_to_memory(request: Request):
    """Add a document to vector memory."""
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
    """Search vector memory for relevant context."""
    context = await vector_memory.retrieve(query, n_results)
    return {"query": query, "context": context}


# =============================================================================
# MCP Management Endpoints
# =============================================================================

@app.get("/mcp/servers")
async def list_mcp_servers():
    """List all MCP server connections."""
    statuses = mcp_manager.get_server_statuses() if mcp_manager else []
    
    return {
        "total": len(statuses),
        "connected": sum(1 for s in statuses if s.connected),
        "servers": [
            {
                "name": s.name,
                "url": s.url,
                "connected": s.connected,
                "tools_count": s.tools_count,
                "last_check": s.last_check.isoformat() if s.last_check else None,
                "error": s.error,
            }
            for s in statuses
        ]
    }


@app.get("/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools."""
    tools = mcp_manager.get_all_tools() if mcp_manager else []
    
    return {
        "total": len(tools),
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "server": t.server_name,
                "category": t.category,
                "parameters": t.parameters,
            }
            for t in tools
        ]
    }


@app.post("/mcp/refresh")
async def refresh_mcp_connections():
    """Refresh all MCP server connections."""
    if mcp_manager:
        await mcp_manager.refresh_connections()
        
        # Update graph engine with new tools
        tools = mcp_manager.get_langchain_tools()
        await graph_engine.initialize(tools)
    
    return {
        "status": "refreshed",
        "connected": mcp_manager.connected_count if mcp_manager else 0,
        "tools": mcp_manager.total_tools if mcp_manager else 0,
    }


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.environ.get("DEBUG") else "An unexpected error occurred"
        }
    )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=os.environ.get("DEBUG", "false").lower() == "true"
    )

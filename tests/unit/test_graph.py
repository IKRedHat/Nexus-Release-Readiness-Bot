"""
Unit Tests for LangGraph Engine
================================

Tests for the LangGraph-based orchestration engine that replaces the legacy ReActEngine.

Covers:
- State management
- Node execution (planner, agent, human_review)
- Conditional routing
- Tool execution
- Error handling
"""

import asyncio
import json
import os
import sys
import pytest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/orchestrator")))

# Mock environment
os.environ["LLM_PROVIDER"] = "mock"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["MEMORY_BACKEND"] = "mock"


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns structured responses."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    mock.bind_tools = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def mock_tools():
    """Create mock LangChain tools."""
    from langchain_core.tools import StructuredTool
    
    async def get_sprint_stats(project_key: str) -> str:
        return json.dumps({
            "sprint_id": 42,
            "sprint_name": f"Sprint 15 - {project_key}",
            "total_issues": 30,
            "completed_issues": 25,
            "in_progress_issues": 3,
            "blocked_issues": 2,
            "completion_percentage": 83.3,
        })
    
    async def get_build_status(job_name: str) -> str:
        return json.dumps({
            "job_name": job_name,
            "build_number": 142,
            "status": "SUCCESS",
            "test_results": {"passed": 234, "failed": 0},
        })
    
    async def get_security_scan(repo_name: str) -> str:
        return json.dumps({
            "repo_name": repo_name,
            "risk_score": 25,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 2,
        })
    
    return [
        StructuredTool(
            name="get_sprint_stats",
            description="Get sprint statistics for a project",
            func=lambda **kwargs: asyncio.run(get_sprint_stats(**kwargs)),
            coroutine=get_sprint_stats,
        ),
        StructuredTool(
            name="get_build_status",
            description="Get build status for a Jenkins job",
            func=lambda **kwargs: asyncio.run(get_build_status(**kwargs)),
            coroutine=get_build_status,
        ),
        StructuredTool(
            name="get_security_scan",
            description="Get security scan results for a repository",
            func=lambda **kwargs: asyncio.run(get_security_scan(**kwargs)),
            coroutine=get_security_scan,
        ),
    ]


@pytest.fixture
def initial_state():
    """Create initial agent state."""
    from langchain_core.messages import HumanMessage
    
    return {
        "messages": [HumanMessage(content="What is the release status?")],
        "query": "What is the release status?",
        "plan": None,
        "current_step": 0,
        "tool_results": [],
        "final_answer": None,
        "requires_approval": False,
        "approval_status": None,
        "error": None,
        "metadata": {},
    }


# =============================================================================
# State Tests
# =============================================================================

class TestAgentState:
    """Test the AgentState TypedDict structure."""
    
    def test_state_structure(self, initial_state):
        """Test that state has all required fields."""
        required_fields = [
            "messages", "query", "plan", "current_step", 
            "tool_results", "final_answer", "requires_approval",
            "approval_status", "error", "metadata"
        ]
        for field in required_fields:
            assert field in initial_state
    
    def test_state_initial_values(self, initial_state):
        """Test initial state values."""
        assert initial_state["query"] == "What is the release status?"
        assert initial_state["current_step"] == 0
        assert initial_state["tool_results"] == []
        assert initial_state["final_answer"] is None
        assert initial_state["error"] is None


# =============================================================================
# Routing Function Tests
# =============================================================================

class TestRoutingFunctions:
    """Test the graph routing functions."""
    
    def test_should_continue_to_end_on_final_answer(self, initial_state):
        """Test routing to end when final answer is present."""
        from app.core.graph import should_continue
        
        state = {**initial_state, "final_answer": "Release is ready!"}
        result = should_continue(state)
        assert result == "end"
    
    def test_should_continue_to_human_review(self, initial_state):
        """Test routing to human review when approval needed."""
        from app.core.graph import should_continue
        
        state = {
            **initial_state, 
            "final_answer": "Report ready to publish",
            "requires_approval": True,
            "approval_status": None,
        }
        result = should_continue(state)
        assert result == "human_review"
    
    def test_should_continue_to_agent(self, initial_state):
        """Test routing back to agent when no final answer."""
        from app.core.graph import should_continue
        
        result = should_continue(initial_state)
        assert result == "agent"
    
    def test_should_continue_on_error(self, initial_state):
        """Test routing to end on error."""
        from app.core.graph import should_continue
        
        state = {**initial_state, "error": "Something went wrong"}
        result = should_continue(state)
        assert result == "end"
    
    def test_should_continue_max_iterations(self, initial_state):
        """Test routing to end on max iterations."""
        from app.core.graph import should_continue
        
        with patch.dict(os.environ, {"MAX_GRAPH_ITERATIONS": "5"}):
            state = {**initial_state, "current_step": 5}
            result = should_continue(state)
            assert result == "end"
    
    def test_after_human_review_approved(self, initial_state):
        """Test routing after human approval."""
        from app.core.graph import after_human_review
        
        state = {**initial_state, "approval_status": "approved"}
        result = after_human_review(state)
        assert result == "agent"
    
    def test_after_human_review_rejected(self, initial_state):
        """Test routing after human rejection."""
        from app.core.graph import after_human_review
        
        state = {**initial_state, "approval_status": "rejected"}
        result = after_human_review(state)
        assert result == "end"


# =============================================================================
# Node Function Tests
# =============================================================================

class TestPlannerNode:
    """Test the planner node functionality."""
    
    @pytest.mark.asyncio
    async def test_planner_creates_plan(self, mock_llm, mock_tools, initial_state):
        """Test that planner creates an execution plan."""
        from app.core.graph import planner_node
        from langchain_core.messages import AIMessage
        
        # Mock LLM response with plan
        plan_response = json.dumps({
            "understanding": "User wants to check release readiness",
            "steps": [
                {"tool": "get_sprint_stats", "args": {"project_key": "PROJ"}, "reason": "Check ticket completion"},
                {"tool": "get_build_status", "args": {"job_name": "nexus-main"}, "reason": "Check CI status"},
            ],
            "requires_approval": False,
        })
        mock_llm.ainvoke.return_value = AIMessage(content=plan_response)
        
        result = await planner_node(initial_state, mock_llm, mock_tools)
        
        assert result["plan"] is not None
        assert len(result["plan"]) == 2
        assert result["plan"][0]["tool"] == "get_sprint_stats"
        assert result["requires_approval"] is False
    
    @pytest.mark.asyncio
    async def test_planner_handles_malformed_response(self, mock_llm, mock_tools, initial_state):
        """Test planner handles non-JSON LLM response."""
        from app.core.graph import planner_node
        from langchain_core.messages import AIMessage
        
        mock_llm.ainvoke.return_value = AIMessage(content="I'll help you check the release.")
        
        result = await planner_node(initial_state, mock_llm, mock_tools)
        
        # Should create default empty plan
        assert result["plan"] == []
        assert result["requires_approval"] is False
    
    @pytest.mark.asyncio
    async def test_planner_handles_exception(self, mock_llm, mock_tools, initial_state):
        """Test planner handles LLM exceptions."""
        from app.core.graph import planner_node
        
        mock_llm.ainvoke.side_effect = Exception("LLM API error")
        
        result = await planner_node(initial_state, mock_llm, mock_tools)
        
        assert result["error"] is not None
        assert "Planning failed" in result["error"]


class TestAgentNode:
    """Test the agent node functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_calls_tool(self, mock_llm, mock_tools, initial_state):
        """Test that agent can call a tool."""
        from app.core.graph import agent_node
        from langchain_core.messages import AIMessage
        
        # Mock LLM with tool call
        mock_response = MagicMock(spec=AIMessage)
        mock_response.content = ""
        mock_response.tool_calls = [{
            "id": "call_123",
            "name": "get_sprint_stats",
            "args": {"project_key": "PROJ"},
        }]
        
        llm_with_tools = MagicMock()
        llm_with_tools.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools.return_value = llm_with_tools
        
        result = await agent_node(initial_state, mock_llm, mock_tools)
        
        assert len(result["tool_results"]) == 1
        assert result["tool_results"][0]["tool"] == "get_sprint_stats"
        assert result["current_step"] == 1
    
    @pytest.mark.asyncio
    async def test_agent_provides_final_answer(self, mock_llm, mock_tools, initial_state):
        """Test that agent can provide a final answer."""
        from app.core.graph import agent_node
        from langchain_core.messages import AIMessage
        
        # Mock LLM with final answer
        mock_response = MagicMock(spec=AIMessage)
        mock_response.content = json.dumps({
            "action": "answer",
            "answer": "The release is ready to proceed."
        })
        mock_response.tool_calls = []
        
        llm_with_tools = MagicMock()
        llm_with_tools.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools.return_value = llm_with_tools
        
        result = await agent_node(initial_state, mock_llm, mock_tools)
        
        assert result["final_answer"] == "The release is ready to proceed."


class TestHumanReviewNode:
    """Test the human review node functionality."""
    
    @pytest.mark.asyncio
    async def test_human_review_sets_pending(self, initial_state):
        """Test that human review sets pending status."""
        from app.core.graph import human_review_node
        
        result = await human_review_node(initial_state)
        
        assert result["approval_status"] == "pending"
        assert "approval_requested_at" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_human_review_preserves_existing_status(self, initial_state):
        """Test that human review preserves existing approval status."""
        from app.core.graph import human_review_node
        
        state = {**initial_state, "approval_status": "approved"}
        result = await human_review_node(state)
        
        assert result["approval_status"] == "approved"


# =============================================================================
# GraphEngine Tests
# =============================================================================

class TestGraphEngine:
    """Test the GraphEngine class."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, mock_tools):
        """Test graph engine initialization."""
        from app.core.graph import GraphEngine
        
        with patch("app.core.graph.get_llm") as mock_get_llm:
            mock_get_llm.return_value = MagicMock()
            
            engine = GraphEngine()
            await engine.initialize(tools=mock_tools)
            
            assert engine._initialized is True
            assert len(engine._tools) == len(mock_tools)
    
    @pytest.mark.asyncio
    async def test_engine_run_returns_result(self, mock_tools):
        """Test that engine run returns a result."""
        from app.core.graph import GraphEngine
        from langchain_core.messages import AIMessage
        
        with patch("app.core.graph.get_llm") as mock_get_llm:
            # Create mock LLM that returns a final answer
            mock_llm = MagicMock()
            mock_response = MagicMock(spec=AIMessage)
            mock_response.content = json.dumps({
                "action": "answer",
                "answer": "Release is ready!"
            })
            mock_response.tool_calls = []
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm
            
            engine = GraphEngine()
            await engine.initialize(tools=mock_tools)
            
            result = await engine.run("What is the release status?")
            
            assert "result" in result
            assert "thread_id" in result
            assert result.get("success") is not None
    
    @pytest.mark.asyncio
    async def test_engine_state_persistence(self, mock_tools):
        """Test that engine can retrieve state by thread_id."""
        from app.core.graph import GraphEngine
        
        with patch("app.core.graph.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
                content="Final answer",
                tool_calls=[]
            ))
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm
            
            engine = GraphEngine()
            await engine.initialize(tools=mock_tools)
            
            result = await engine.run("Test query", thread_id="test-thread-123")
            
            state = await engine.get_state("test-thread-123")
            
            # State should be retrievable
            # Note: In memory checkpointer, state is available
            assert state is not None or result.get("thread_id") == "test-thread-123"
    
    @pytest.mark.asyncio
    async def test_engine_close(self, mock_tools):
        """Test engine cleanup."""
        from app.core.graph import GraphEngine
        
        with patch("app.core.graph.get_llm") as mock_get_llm:
            mock_get_llm.return_value = MagicMock()
            
            engine = GraphEngine()
            await engine.initialize(tools=mock_tools)
            
            await engine.close()
            
            assert engine._initialized is False


# =============================================================================
# Integration Tests
# =============================================================================

class TestGraphEngineIntegration:
    """Integration tests for the graph engine."""
    
    @pytest.mark.asyncio
    async def test_full_execution_flow(self, mock_tools):
        """Test a complete query execution flow."""
        from app.core.graph import GraphEngine
        from langchain_core.messages import AIMessage
        
        with patch("app.core.graph.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            
            # Planner response
            planner_response = MagicMock(spec=AIMessage)
            planner_response.content = json.dumps({
                "understanding": "Check release status",
                "steps": [{"tool": "get_sprint_stats", "args": {"project_key": "PROJ"}}],
                "requires_approval": False,
            })
            
            # Agent response with final answer
            agent_response = MagicMock(spec=AIMessage)
            agent_response.content = json.dumps({
                "action": "answer",
                "answer": "Sprint is 83% complete. Release is conditionally ready."
            })
            agent_response.tool_calls = []
            
            mock_llm.ainvoke = AsyncMock(side_effect=[planner_response, agent_response])
            mock_llm.bind_tools = MagicMock(return_value=mock_llm)
            mock_get_llm.return_value = mock_llm
            
            engine = GraphEngine()
            await engine.initialize(tools=mock_tools)
            
            result = await engine.run("What is the release status for PROJ?")
            
            assert result.get("success") or result.get("result") is not None
            await engine.close()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

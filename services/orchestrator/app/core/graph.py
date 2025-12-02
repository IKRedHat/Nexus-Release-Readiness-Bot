"""
Nexus LangGraph Engine
======================

LangGraph-based orchestration engine replacing the custom ReActEngine.

This module implements a stateful StateGraph with:
- Planner node: Analyzes queries and creates execution plans
- Agent node: Invokes tools from MCP servers
- Human review node: Handles interrupt points for approval
- Persistent state via PostgreSQL

Architecture:
    User Query -> Planner -> Agent (loop) -> Human Review (optional) -> Response

Author: Nexus Team
Version: 3.0.0
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, TypedDict, Union

from pydantic import BaseModel, Field

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# LangChain imports
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared")))

from nexus_lib.config import ConfigManager, ConfigKeys

logger = logging.getLogger("nexus.graph_engine")


# =============================================================================
# State Definition
# =============================================================================

class AgentState(TypedDict):
    """
    State schema for the LangGraph agent.
    
    Attributes:
        messages: Conversation history with add_messages reducer
        query: Original user query
        plan: Execution plan from planner
        current_step: Current step in the plan
        tool_results: Results from tool executions
        final_answer: Final response to user
        requires_approval: Whether human approval is needed
        approval_status: Status of human approval
        error: Any error that occurred
        metadata: Additional metadata
    """
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    plan: Optional[List[Dict[str, Any]]]
    current_step: int
    tool_results: List[Dict[str, Any]]
    final_answer: Optional[str]
    requires_approval: bool
    approval_status: Optional[Literal["pending", "approved", "rejected"]]
    error: Optional[str]
    metadata: Dict[str, Any]


# =============================================================================
# System Prompts
# =============================================================================

PLANNER_SYSTEM_PROMPT = """You are a Release Readiness Planner for the Nexus automation system.

Your role is to analyze user queries about release readiness and create an execution plan.

Available tool categories:
- Jira: get_ticket, get_ticket_hierarchy, search_tickets, get_sprint_stats, update_ticket_status
- GitHub: check_repo_health, check_pr_status, list_open_prs
- Jenkins: get_build_status, trigger_jenkins_build, get_build_history
- Security: get_security_scan
- Reporting: generate_report, publish_confluence_report, analyze_release_readiness
- RCA: analyze_build_failure, get_build_logs, get_commit_changes
- Hygiene: check_project_hygiene, get_project_violations

When creating a plan:
1. Identify what information is needed
2. List the tools to call in order
3. Note any dependencies between steps
4. Indicate if human approval is needed (for publish actions)

Respond with a JSON plan:
{
    "understanding": "What the user wants",
    "steps": [
        {"tool": "tool_name", "args": {...}, "reason": "Why this tool"},
        ...
    ],
    "requires_approval": true/false,
    "approval_reason": "Why approval is needed (if applicable)"
}
"""

AGENT_SYSTEM_PROMPT = """You are a Release Readiness Agent executing tools for the Nexus automation system.

Based on the plan and tool results so far, decide the next action:
1. Call a tool to gather more information
2. Provide a final answer summarizing the findings

When providing a final answer:
- Be concise but comprehensive
- Highlight key metrics and status
- Flag any blockers or risks
- Provide a clear Go/No-Go recommendation if applicable

If you need to call a tool, respond with:
{
    "action": "tool",
    "tool": "tool_name",
    "args": {...}
}

If you have enough information, respond with:
{
    "action": "answer",
    "answer": "Your comprehensive response"
}
"""


# =============================================================================
# Graph Nodes
# =============================================================================

async def planner_node(state: AgentState, llm, tools: List[BaseTool]) -> AgentState:
    """
    Planner node: Analyzes query and creates execution plan.
    
    Args:
        state: Current graph state
        llm: LLM instance from factory
        tools: Available tools
        
    Returns:
        Updated state with plan
    """
    logger.info("Planner node executing")
    
    query = state["query"]
    
    # Build tool descriptions
    tool_descriptions = "\n".join([
        f"- {tool.name}: {tool.description}"
        for tool in tools
    ])
    
    # Create planning prompt
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"""
User Query: {query}

Available Tools:
{tool_descriptions}

Create an execution plan.
"""),
    ]
    
    try:
        # Call LLM for planning
        response = await llm.ainvoke(messages)
        
        # Parse plan from response
        response_text = response.content
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            plan_data = json.loads(json_match.group())
        else:
            plan_data = {
                "understanding": query,
                "steps": [],
                "requires_approval": False,
            }
        
        return {
            **state,
            "messages": state["messages"] + [response],
            "plan": plan_data.get("steps", []),
            "requires_approval": plan_data.get("requires_approval", False),
            "metadata": {
                **state.get("metadata", {}),
                "plan_understanding": plan_data.get("understanding"),
            },
        }
        
    except Exception as e:
        logger.error(f"Planner node failed: {e}")
        return {
            **state,
            "error": f"Planning failed: {str(e)}",
        }


async def agent_node(state: AgentState, llm, tools: List[BaseTool]) -> AgentState:
    """
    Agent node: Executes tools and gathers information.
    
    Args:
        state: Current graph state
        llm: LLM instance
        tools: Available tools
        
    Returns:
        Updated state with tool results or final answer
    """
    logger.info(f"Agent node executing (step {state['current_step']})")
    
    # Build context from previous results
    results_context = "\n".join([
        f"Step {r['step']}: {r['tool']} -> {json.dumps(r['result'], default=str)[:500]}"
        for r in state.get("tool_results", [])
    ])
    
    plan_context = ""
    if state.get("plan"):
        plan_context = "Planned steps:\n" + "\n".join([
            f"- {s['tool']}: {s.get('reason', '')}"
            for s in state["plan"]
        ])
    
    messages = state["messages"] + [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Original Query: {state['query']}

{plan_context}

Results so far:
{results_context if results_context else "No results yet"}

What should we do next?
"""),
    ]
    
    try:
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke(messages)
        
        # Check if LLM wants to call a tool
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find and execute tool
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                try:
                    if asyncio.iscoroutinefunction(tool.coroutine):
                        result = await tool.coroutine(**tool_args)
                    else:
                        result = tool.func(**tool_args)
                    
                    tool_result = {
                        "step": state["current_step"],
                        "tool": tool_name,
                        "args": tool_args,
                        "result": json.loads(result) if isinstance(result, str) else result,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                except Exception as e:
                    tool_result = {
                        "step": state["current_step"],
                        "tool": tool_name,
                        "args": tool_args,
                        "result": {"error": str(e)},
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            else:
                tool_result = {
                    "step": state["current_step"],
                    "tool": tool_name,
                    "args": tool_args,
                    "result": {"error": f"Unknown tool: {tool_name}"},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            return {
                **state,
                "messages": state["messages"] + [
                    response,
                    ToolMessage(content=json.dumps(tool_result["result"], default=str), tool_call_id=tool_call["id"]),
                ],
                "tool_results": state.get("tool_results", []) + [tool_result],
                "current_step": state["current_step"] + 1,
            }
        
        # Check for final answer in response
        response_text = response.content
        
        # Try to parse JSON response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_data = json.loads(json_match.group())
                if response_data.get("action") == "answer":
                    return {
                        **state,
                        "messages": state["messages"] + [response],
                        "final_answer": response_data.get("answer", response_text),
                    }
        except json.JSONDecodeError:
            pass
        
        # Use response as final answer
        return {
            **state,
            "messages": state["messages"] + [response],
            "final_answer": response_text,
        }
        
    except Exception as e:
        logger.error(f"Agent node failed: {e}")
        return {
            **state,
            "error": f"Agent execution failed: {str(e)}",
        }


async def human_review_node(state: AgentState) -> AgentState:
    """
    Human review node: Handles approval workflow.
    
    This node is used when actions require human approval (e.g., publishing).
    The graph will interrupt here and wait for external approval.
    """
    logger.info("Human review node - waiting for approval")
    
    # In a real implementation, this would:
    # 1. Send notification to Slack/email
    # 2. Wait for callback with approval decision
    # 3. Update state based on decision
    
    # For now, we'll auto-approve (can be changed via state)
    if state.get("approval_status") is None:
        return {
            **state,
            "approval_status": "pending",
            "metadata": {
                **state.get("metadata", {}),
                "approval_requested_at": datetime.utcnow().isoformat(),
            },
        }
    
    return state


# =============================================================================
# Routing Functions
# =============================================================================

def should_continue(state: AgentState) -> Literal["agent", "human_review", "end"]:
    """
    Determine next step after agent node.
    
    Returns:
        Next node to execute or END
    """
    # Check for errors
    if state.get("error"):
        return "end"
    
    # Check if we have a final answer
    if state.get("final_answer"):
        # Check if approval is needed
        if state.get("requires_approval") and state.get("approval_status") != "approved":
            return "human_review"
        return "end"
    
    # Check iteration limit
    max_iterations = int(os.environ.get("MAX_GRAPH_ITERATIONS", "10"))
    if state.get("current_step", 0) >= max_iterations:
        logger.warning("Max iterations reached")
        return "end"
    
    # Continue to agent
    return "agent"


def after_human_review(state: AgentState) -> Literal["agent", "end"]:
    """
    Determine next step after human review.
    """
    if state.get("approval_status") == "approved":
        return "agent"
    elif state.get("approval_status") == "rejected":
        return "end"
    else:
        # Still pending - will be handled by interrupt
        return "end"


# =============================================================================
# Graph Builder
# =============================================================================

class GraphEngine:
    """
    LangGraph-based orchestration engine.
    
    Usage:
        engine = GraphEngine()
        await engine.initialize()
        
        result = await engine.run("What is the release status for v2.0?")
    """
    
    def __init__(self):
        self._graph = None
        self._tools: List[BaseTool] = []
        self._llm = None
        self._checkpointer = None
        self._initialized = False
    
    async def initialize(
        self,
        tools: Optional[List[BaseTool]] = None,
        use_postgres_checkpointer: bool = False,
    ):
        """
        Initialize the graph engine.
        
        Args:
            tools: List of LangChain tools (from MCP manager)
            use_postgres_checkpointer: Use PostgreSQL for state persistence
        """
        # Import LLM factory
        from .llm_factory import get_llm
        
        # Get LLM instance
        self._llm = await get_llm()
        
        # Store tools
        self._tools = tools or []
        
        # Setup checkpointer
        if use_postgres_checkpointer:
            try:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                
                postgres_url = os.environ.get(
                    "POSTGRES_URL",
                    "postgresql://nexus:nexus@localhost:5432/nexus"
                )
                self._checkpointer = AsyncPostgresSaver.from_conn_string(postgres_url)
            except Exception as e:
                logger.warning(f"Failed to initialize Postgres checkpointer: {e}")
                self._checkpointer = MemorySaver()
        else:
            self._checkpointer = MemorySaver()
        
        # Build the graph
        self._build_graph()
        
        self._initialized = True
        logger.info(f"GraphEngine initialized with {len(self._tools)} tools")
    
    def _build_graph(self):
        """Build the LangGraph StateGraph."""
        # Create workflow
        workflow = StateGraph(AgentState)
        
        # Create node wrappers that include llm and tools
        async def _planner(state):
            return await planner_node(state, self._llm, self._tools)
        
        async def _agent(state):
            return await agent_node(state, self._llm, self._tools)
        
        # Add nodes
        workflow.add_node("planner", _planner)
        workflow.add_node("agent", _agent)
        workflow.add_node("human_review", human_review_node)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add edges
        workflow.add_edge("planner", "agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "agent": "agent",
                "human_review": "human_review",
                "end": END,
            }
        )
        
        workflow.add_conditional_edges(
            "human_review",
            after_human_review,
            {
                "agent": "agent",
                "end": END,
            }
        )
        
        # Compile with checkpointer
        self._graph = workflow.compile(
            checkpointer=self._checkpointer,
            interrupt_before=["human_review"],  # Interrupt for approval
        )
    
    async def run(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the graph with a user query.
        
        Args:
            query: User's natural language query
            user_context: Optional context (user ID, team, etc.)
            thread_id: Thread ID for state persistence
            
        Returns:
            Execution result with final answer
        """
        if not self._initialized:
            raise RuntimeError("GraphEngine not initialized")
        
        # Generate thread ID if not provided
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
        
        # Initial state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "plan": None,
            "current_step": 0,
            "tool_results": [],
            "final_answer": None,
            "requires_approval": False,
            "approval_status": None,
            "error": None,
            "metadata": {
                "user_context": user_context or {},
                "started_at": datetime.utcnow().isoformat(),
            },
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Run the graph
            final_state = await self._graph.ainvoke(initial_state, config)
            
            # Extract result
            return {
                "success": True,
                "result": final_state.get("final_answer", "No answer generated"),
                "plan": final_state.get("plan"),
                "steps": len(final_state.get("tool_results", [])),
                "tool_results": final_state.get("tool_results", []),
                "thread_id": thread_id,
                "requires_approval": final_state.get("requires_approval", False),
                "approval_status": final_state.get("approval_status"),
                "error": final_state.get("error"),
            }
            
        except Exception as e:
            logger.exception(f"Graph execution failed: {e}")
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "thread_id": thread_id,
            }
    
    async def resume(
        self,
        thread_id: str,
        approval_status: Literal["approved", "rejected"],
    ) -> Dict[str, Any]:
        """
        Resume execution after human review.
        
        Args:
            thread_id: Thread ID to resume
            approval_status: Approval decision
            
        Returns:
            Resumed execution result
        """
        if not self._initialized:
            raise RuntimeError("GraphEngine not initialized")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        state = await self._graph.aget_state(config)
        
        if not state or not state.values:
            return {
                "success": False,
                "error": f"No state found for thread {thread_id}",
            }
        
        # Update approval status and resume
        updated_state = {
            **state.values,
            "approval_status": approval_status,
        }
        
        try:
            final_state = await self._graph.ainvoke(updated_state, config)
            
            return {
                "success": True,
                "result": final_state.get("final_answer"),
                "approval_status": approval_status,
                "thread_id": thread_id,
            }
            
        except Exception as e:
            logger.exception(f"Resume failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id,
            }
    
    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current state for a thread."""
        if not self._initialized:
            return None
        
        config = {"configurable": {"thread_id": thread_id}}
        state = await self._graph.aget_state(config)
        
        if state and state.values:
            return dict(state.values)
        return None
    
    async def close(self):
        """Cleanup resources."""
        self._initialized = False
        logger.info("GraphEngine closed")


# =============================================================================
# Singleton Instance
# =============================================================================

_engine_instance: Optional[GraphEngine] = None


async def get_graph_engine(
    tools: Optional[List[BaseTool]] = None,
) -> GraphEngine:
    """
    Get or create the singleton graph engine.
    
    Usage:
        engine = await get_graph_engine(tools)
        result = await engine.run("What is the release status?")
    """
    global _engine_instance
    
    if _engine_instance is None:
        _engine_instance = GraphEngine()
        await _engine_instance.initialize(tools)
    
    return _engine_instance


async def close_graph_engine():
    """Close the graph engine."""
    global _engine_instance
    
    if _engine_instance:
        await _engine_instance.close()
        _engine_instance = None


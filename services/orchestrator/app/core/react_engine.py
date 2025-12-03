"""
Nexus ReAct Engine
LangChain-powered reasoning engine with tool orchestration
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared")))

from nexus_lib.utils import AsyncHttpClient, agent_registry, generate_task_id
from nexus_lib.specialists import specialist_registry, SpecialistStatus
from nexus_lib.instrumentation import (
    track_llm_usage,
    track_tool_usage,
    track_react_loop,
    REACT_ITERATIONS,
    REACT_LOOP_DURATION,
)
from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    ReActStep,
    ReActTrace,
    TaskStatus,
)

logger = logging.getLogger("nexus.react")


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

class Tool(BaseModel):
    """Tool definition for the ReAct agent"""
    name: str
    description: str
    agent_type: str
    endpoint: str
    method: str = "GET"
    parameters: Dict[str, str] = Field(default_factory=dict)
    required_params: List[str] = Field(default_factory=list)


# Define available tools - comprehensive list for all specialist agents
AVAILABLE_TOOLS: Dict[str, Tool] = {
    # ==========================================================================
    # JIRA AGENT TOOLS
    # ==========================================================================
    "get_jira_ticket": Tool(
        name="get_jira_ticket",
        description="Fetch details of a Jira ticket by its key (e.g., PROJ-123). Returns ticket summary, status, assignee, and other details.",
        agent_type="jira",
        endpoint="/issue/{ticket_key}",
        method="GET",
        required_params=["ticket_key"]
    ),
    "get_ticket_hierarchy": Tool(
        name="get_ticket_hierarchy",
        description="Fetch the complete hierarchy of tickets under an Epic. Shows Epic -> Stories -> Subtasks structure.",
        agent_type="jira",
        endpoint="/hierarchy/{ticket_key}",
        method="GET",
        required_params=["ticket_key"]
    ),
    "search_jira": Tool(
        name="search_jira",
        description="Search Jira tickets using JQL (Jira Query Language). Example: 'project = PROJ AND status = \"In Progress\"'",
        agent_type="jira",
        endpoint="/search",
        method="GET",
        parameters={"jql": "JQL query string"},
        required_params=["jql"]
    ),
    "update_jira_ticket": Tool(
        name="update_jira_ticket",
        description="Update a Jira ticket's status or add a comment. Requires ticket key and either status or comment.",
        agent_type="jira",
        endpoint="/update",
        method="POST",
        parameters={"key": "Ticket key", "status": "New status", "comment": "Comment text"},
        required_params=["key"]
    ),
    "get_sprint_stats": Tool(
        name="get_sprint_stats",
        description="Get sprint statistics including completion rate, story points, and blockers for a project.",
        agent_type="jira",
        endpoint="/sprint-stats/{project_key}",
        method="GET",
        required_params=["project_key"]
    ),
    
    # ==========================================================================
    # GIT/CI AGENT TOOLS
    # ==========================================================================
    "get_repo_health": Tool(
        name="get_repo_health",
        description="Check GitHub repository health including branch status, open PRs, and CI status.",
        agent_type="git_ci",
        endpoint="/repo/{repo_name}/health",
        method="GET",
        required_params=["repo_name"]
    ),
    "get_pr_status": Tool(
        name="get_pr_status",
        description="Get details of a specific GitHub Pull Request including CI status and approvals.",
        agent_type="git_ci",
        endpoint="/repo/{repo_name}/pr/{pr_number}",
        method="GET",
        required_params=["repo_name", "pr_number"]
    ),
    "get_build_status": Tool(
        name="get_build_status",
        description="Get Jenkins build status for a job. Returns build result, test results, and artifacts.",
        agent_type="git_ci",
        endpoint="/build/{job_name}/status",
        method="GET",
        required_params=["job_name"]
    ),
    "trigger_build": Tool(
        name="trigger_build",
        description="Trigger a new Jenkins build for a specified job.",
        agent_type="git_ci",
        endpoint="/build/{job_name}",
        method="POST",
        required_params=["job_name"]
    ),
    "get_security_scan": Tool(
        name="get_security_scan",
        description="Get security scan results for a repository including vulnerabilities and risk score.",
        agent_type="git_ci",
        endpoint="/security/{repo_name}",
        method="GET",
        required_params=["repo_name"]
    ),
    
    # ==========================================================================
    # REPORTING AGENT TOOLS
    # ==========================================================================
    "generate_report": Tool(
        name="generate_report",
        description="Generate a release readiness HTML report from provided data.",
        agent_type="reporting",
        endpoint="/generate",
        method="POST",
        required_params=["report_data"]
    ),
    "publish_report": Tool(
        name="publish_report",
        description="Publish a report to Confluence. Can create a new page or update existing.",
        agent_type="reporting",
        endpoint="/publish",
        method="POST",
        parameters={"page_id": "Existing page ID (optional)", "space_key": "Confluence space", "title": "Page title"},
        required_params=["title", "report_data"]
    ),
    "analyze_readiness": Tool(
        name="analyze_readiness",
        description="Analyze release data and determine Go/No-Go decision with checklist.",
        agent_type="reporting",
        endpoint="/analyze",
        method="POST",
        required_params=["report_data"]
    ),
    
    # ==========================================================================
    # SLACK AGENT TOOLS
    # ==========================================================================
    "send_slack_notification": Tool(
        name="send_slack_notification",
        description="Send a message to a Slack channel with optional Block Kit formatting.",
        agent_type="slack",
        endpoint="/notify",
        method="POST",
        parameters={"channel": "Channel ID", "message": "Message text", "blocks": "Block Kit blocks (optional)"},
        required_params=["channel", "message"]
    ),
    "send_slack_dm": Tool(
        name="send_slack_dm",
        description="Send a direct message to a Slack user.",
        agent_type="slack",
        endpoint="/dm",
        method="POST",
        parameters={"user_id": "Slack user ID", "message": "Message text"},
        required_params=["user_id", "message"]
    ),
    
    # ==========================================================================
    # RCA AGENT TOOLS
    # ==========================================================================
    "analyze_build_failure": Tool(
        name="analyze_build_failure",
        description="Analyze a failed Jenkins build to determine root cause. Uses LLM to correlate error logs with git diffs to identify which code change caused the failure and suggest fixes.",
        agent_type="rca",
        endpoint="/analyze",
        method="POST",
        parameters={
            "job_name": "Jenkins job name",
            "build_number": "Build number to analyze",
            "repo_name": "GitHub repository name (optional)",
            "pr_id": "Pull request ID (optional)",
            "commit_sha": "Specific commit SHA (optional)"
        },
        required_params=["job_name", "build_number"]
    ),
    "get_rca_history": Tool(
        name="get_rca_history",
        description="Get history of RCA analyses for a job or repository.",
        agent_type="rca",
        endpoint="/history",
        method="GET",
        parameters={"job_name": "Jenkins job name", "repo_name": "Repository name"},
        required_params=[]
    ),
    
    # ==========================================================================
    # JIRA HYGIENE AGENT TOOLS
    # ==========================================================================
    "run_hygiene_check": Tool(
        name="run_hygiene_check",
        description="Run a hygiene check on Jira data for a project. Identifies missing fields, stale tickets, and other quality issues.",
        agent_type="hygiene",
        endpoint="/check/{project_key}",
        method="POST",
        parameters={"check_types": "Types of checks to run (optional)"},
        required_params=["project_key"]
    ),
    "get_hygiene_score": Tool(
        name="get_hygiene_score",
        description="Get the current hygiene score for a project. Returns score, trends, and issue breakdown.",
        agent_type="hygiene",
        endpoint="/score/{project_key}",
        method="GET",
        required_params=["project_key"]
    ),
    "fix_hygiene_issues": Tool(
        name="fix_hygiene_issues",
        description="Automatically fix identified hygiene issues for a project.",
        agent_type="hygiene",
        endpoint="/fix",
        method="POST",
        parameters={"issue_ids": "Specific issue IDs to fix (optional)"},
        required_params=["project_key"]
    ),
    "get_hygiene_history": Tool(
        name="get_hygiene_history",
        description="Get historical hygiene scores and trends for a project.",
        agent_type="hygiene",
        endpoint="/history/{project_key}",
        method="GET",
        required_params=["project_key"]
    ),
    
    # ==========================================================================
    # ANALYTICS SERVICE TOOLS
    # ==========================================================================
    "get_dora_metrics": Tool(
        name="get_dora_metrics",
        description="Get DORA (DevOps Research and Assessment) metrics: deployment frequency, lead time, change failure rate, and MTTR.",
        agent_type="analytics",
        endpoint="/dora",
        method="GET",
        parameters={"project": "Project identifier", "from_date": "Start date (ISO)", "to_date": "End date (ISO)"},
        required_params=[]
    ),
    "get_release_kpis": Tool(
        name="get_release_kpis",
        description="Get key performance indicators for releases including velocity, quality, and efficiency metrics.",
        agent_type="analytics",
        endpoint="/kpis",
        method="GET",
        parameters={"project": "Project identifier", "release_version": "Specific release version"},
        required_params=[]
    ),
    "get_trend_analysis": Tool(
        name="get_trend_analysis",
        description="Analyze trends in release metrics over time. Identifies patterns, anomalies, and forecasts.",
        agent_type="analytics",
        endpoint="/trends",
        method="GET",
        parameters={"metric": "Metric to analyze (velocity, quality)", "period": "Time period (7d, 30d, 90d)"},
        required_params=[]
    ),
    "predict_release_readiness": Tool(
        name="predict_release_readiness",
        description="Predict release readiness based on historical data and current trajectory.",
        agent_type="analytics",
        endpoint="/predict",
        method="POST",
        parameters={"target_date": "Target release date"},
        required_params=["release_version"]
    ),
    
    # ==========================================================================
    # WEBHOOKS SERVICE TOOLS
    # ==========================================================================
    "create_webhook_subscription": Tool(
        name="create_webhook_subscription",
        description="Create a new webhook subscription for event notifications.",
        agent_type="webhooks",
        endpoint="/subscriptions",
        method="POST",
        parameters={"secret": "HMAC secret for signature verification"},
        required_params=["event_type", "target_url"]
    ),
    "list_webhook_subscriptions": Tool(
        name="list_webhook_subscriptions",
        description="List all active webhook subscriptions.",
        agent_type="webhooks",
        endpoint="/subscriptions",
        method="GET",
        required_params=[]
    ),
    "get_webhook_delivery_status": Tool(
        name="get_webhook_delivery_status",
        description="Get delivery status and history for webhook events.",
        agent_type="webhooks",
        endpoint="/deliveries",
        method="GET",
        parameters={"subscription_id": "Subscription ID"},
        required_params=[]
    ),
    
    # ==========================================================================
    # SCHEDULING AGENT TOOLS
    # ==========================================================================
    "schedule_task": Tool(
        name="schedule_task",
        description="Schedule a recurring or one-time task.",
        agent_type="scheduling",
        endpoint="/schedule",
        method="POST",
        parameters={"cron": "Cron expression for recurring", "run_at": "ISO datetime for one-time", "payload": "Task payload"},
        required_params=["task_type"]
    ),
    "list_scheduled_tasks": Tool(
        name="list_scheduled_tasks",
        description="List all scheduled tasks.",
        agent_type="scheduling",
        endpoint="/tasks",
        method="GET",
        required_params=[]
    ),
}


def get_tools_description(include_health: bool = False) -> str:
    """
    Generate tools description for LLM prompt.
    
    Args:
        include_health: If True, indicate which tools are currently available based on specialist health.
    """
    lines = ["Available tools:"]
    
    # Group tools by agent type
    tools_by_agent: Dict[str, List[Tool]] = {}
    for name, tool in AVAILABLE_TOOLS.items():
        if tool.agent_type not in tools_by_agent:
            tools_by_agent[tool.agent_type] = []
        tools_by_agent[tool.agent_type].append(tool)
    
    for agent_type, tools in tools_by_agent.items():
        # Check specialist health if requested
        status_indicator = ""
        if include_health:
            health = specialist_registry.get_health(agent_type)
            if health:
                if health.status == SpecialistStatus.HEALTHY:
                    status_indicator = " ✓"
                elif health.status == SpecialistStatus.DEGRADED:
                    status_indicator = " ⚠"
                else:
                    status_indicator = " ✗ (unavailable)"
        
        lines.append(f"\n## {agent_type.upper()}{status_indicator}")
        for tool in tools:
            params = ", ".join(tool.required_params) if tool.required_params else "none"
            lines.append(f"- {tool.name}: {tool.description}")
            lines.append(f"  Required params: {params}")
    
    return "\n".join(lines)


# ============================================================================
# LLM CLIENT
# ============================================================================

class LLMClient:
    """
    LLM client with support for multiple providers
    """
    
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "mock")
        self.model = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
        self.api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = None
        
        if self.provider == "google" and self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                logger.info(f"LLM client initialized with Google {self.model}")
            except ImportError:
                logger.warning("google-generativeai not installed, using mock mode")
                self.provider = "mock"
        elif self.provider == "openai" and self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info(f"LLM client initialized with OpenAI {self.model}")
            except ImportError:
                logger.warning("openai not installed, using mock mode")
                self.provider = "mock"
        else:
            logger.info("LLM client running in MOCK mode")
            self.provider = "mock"
    
    @track_llm_usage(model_name="gemini-2.5-flash")
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        if self.provider == "mock":
            return self._mock_generate(prompt)
        
        try:
            if self.provider == "google":
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    full_prompt
                )
                return {
                    "content": response.text,
                    "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
                }
            elif self.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                return {
                    "content": response.choices[0].message.content,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> Dict[str, Any]:
        """Generate mock response for development"""
        # Parse the prompt to extract intent
        prompt_lower = prompt.lower()
        
        if "final answer" in prompt_lower or "observation" in prompt_lower:
            return {
                "content": "Thought: Based on the observations, I have gathered sufficient information.\nFinal Answer: The release readiness check is complete. The system shows 93% ticket completion with 2 high-severity vulnerabilities that require attention before release.",
                "input_tokens": 100,
                "output_tokens": 50
            }
        elif "jira" in prompt_lower or "ticket" in prompt_lower:
            if "PROJ-" in prompt or "hierarchy" in prompt_lower:
                return {
                    "content": "Thought: I need to fetch the Jira ticket hierarchy to understand the release scope.\nAction: get_ticket_hierarchy\nAction Input: {\"ticket_key\": \"PROJ-100\"}",
                    "input_tokens": 80,
                    "output_tokens": 40
                }
            else:
                return {
                    "content": "Thought: I need to get Jira sprint statistics to assess completion.\nAction: get_sprint_stats\nAction Input: {\"project_key\": \"PROJ\"}",
                    "input_tokens": 80,
                    "output_tokens": 40
                }
        elif "security" in prompt_lower or "vulnerab" in prompt_lower:
            return {
                "content": "Thought: I should check the security scan results for the repository.\nAction: get_security_scan\nAction Input: {\"repo_name\": \"nexus/backend\"}",
                "input_tokens": 80,
                "output_tokens": 40
            }
        elif "fail" in prompt_lower and "build" in prompt_lower:
            # RCA query
            return {
                "content": "Thought: The user is asking about a failed build. I should use the analyze_build_failure tool to perform root cause analysis.\nAction: analyze_build_failure\nAction Input: {\"job_name\": \"nexus-main\", \"build_number\": 142}",
                "input_tokens": 100,
                "output_tokens": 50
            }
        elif "why" in prompt_lower and ("fail" in prompt_lower or "error" in prompt_lower):
            # RCA query variant
            return {
                "content": "Thought: The user wants to know why something failed. I'll analyze the build failure to find the root cause.\nAction: analyze_build_failure\nAction Input: {\"job_name\": \"nexus-main\", \"build_number\": 142}",
                "input_tokens": 100,
                "output_tokens": 50
            }
        elif "diagnose" in prompt_lower or "debug" in prompt_lower or "rca" in prompt_lower:
            # Explicit RCA request
            return {
                "content": "Thought: The user wants me to diagnose an issue. I'll perform root cause analysis on the build.\nAction: analyze_build_failure\nAction Input: {\"job_name\": \"nexus-main\", \"build_number\": 142}",
                "input_tokens": 100,
                "output_tokens": 50
            }
        elif "build" in prompt_lower or "ci" in prompt_lower:
            return {
                "content": "Thought: I need to check the latest build status.\nAction: get_build_status\nAction Input: {\"job_name\": \"nexus-main\"}",
                "input_tokens": 80,
                "output_tokens": 40
            }
        elif "report" in prompt_lower:
            return {
                "content": "Thought: I should analyze the collected data and generate a report.\nAction: analyze_readiness\nAction Input: {\"report_data\": {\"stats\": {\"release_version\": \"v2.0.0\"}}}",
                "input_tokens": 80,
                "output_tokens": 40
            }
        elif "status" in prompt_lower or "ready" in prompt_lower or "release" in prompt_lower:
            return {
                "content": "Thought: To check release readiness, I need to gather information from multiple sources. Let me start with Jira sprint stats.\nAction: get_sprint_stats\nAction Input: {\"project_key\": \"PROJ\"}",
                "input_tokens": 100,
                "output_tokens": 50
            }
        else:
            return {
                "content": "Thought: I understand the request. Let me analyze the available information.\nFinal Answer: Request processed successfully. Please provide more specific details about what you'd like to check.",
                "input_tokens": 80,
                "output_tokens": 40
            }


# ============================================================================
# REACT ENGINE
# ============================================================================

class ReActEngine:
    """
    ReAct (Reasoning and Acting) engine for orchestrating multi-agent workflows
    """
    
    SYSTEM_PROMPT = """You are Nexus, an intelligent release automation assistant. Your role is to help teams assess release readiness by gathering information from various tools and providing actionable insights.

You operate using the ReAct (Reasoning + Acting) framework:
1. Thought: Reason about what information you need and why
2. Action: Call a tool to gather information
3. Observation: Review the tool's response
4. Repeat until you have enough information
5. Final Answer: Provide a comprehensive response

{tools_description}

IMPORTANT RULES:
- Always start with a Thought explaining your reasoning
- Use tools to gather real data, don't make assumptions
- When you have enough information, provide a Final Answer
- If a tool fails, explain the issue and try an alternative approach
- Format your response exactly as: "Thought: ...\nAction: ...\nAction Input: ..."
- For final answers: "Thought: ...\nFinal Answer: ..."

Current context from memory:
{memory_context}
"""

    USER_PROMPT = """User Query: {query}

Previous steps in this conversation:
{previous_steps}

{observation_prompt}

What is your next step?"""
    
    def __init__(self, memory_client, max_iterations: int = 10):
        self.memory = memory_client
        self.llm = LLMClient()
        self.max_iterations = max_iterations
        self.http_clients: Dict[str, AsyncHttpClient] = {}
        
        logger.info(f"ReAct engine initialized with max {max_iterations} iterations")
    
    async def _get_agent_client(self, agent_type: str) -> AsyncHttpClient:
        """Get or create HTTP client for an agent"""
        if agent_type not in self.http_clients:
            # First try specialist registry (preferred)
            url = specialist_registry.get_url(agent_type)
            if not url:
                # Fallback to legacy agent registry
                url = agent_registry.get_url(agent_type)
            if not url:
                raise ValueError(f"No URL configured for agent: {agent_type}")
            self.http_clients[agent_type] = AsyncHttpClient(base_url=url)
        return self.http_clients[agent_type]
    
    async def _check_specialist_available(self, agent_type: str) -> tuple:
        """
        Check if a specialist is available.
        
        Returns:
            Tuple of (is_available: bool, status_message: str)
        """
        health = specialist_registry.get_health(agent_type)
        if not health:
            # Force a health check
            health = await specialist_registry.check_health(agent_type)
        
        if health.status == SpecialistStatus.HEALTHY:
            return True, "healthy"
        elif health.status == SpecialistStatus.DEGRADED:
            return True, f"degraded: {health.error_message}"
        else:
            return False, f"unavailable: {health.error_message or 'service down'}"
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result"""
        if tool_name not in AVAILABLE_TOOLS:
            return {"error": f"Unknown tool: {tool_name}", "available_tools": list(AVAILABLE_TOOLS.keys())}
        
        tool = AVAILABLE_TOOLS[tool_name]
        
        # Check specialist availability
        is_available, status_msg = await self._check_specialist_available(tool.agent_type)
        if not is_available:
            logger.warning(f"Specialist {tool.agent_type} is {status_msg} - tool {tool_name} cannot be executed")
            return {
                "error": f"Specialist '{tool.agent_type}' is currently unavailable",
                "status": status_msg,
                "suggestion": "The service may be starting up or experiencing issues. Try again in a moment."
            }
        
        try:
            client = await self._get_agent_client(tool.agent_type)
        except ValueError as e:
            return {"error": str(e)}
        
        # Build endpoint with path parameters
        endpoint = tool.endpoint
        for param in tool.required_params:
            if param in args:
                endpoint = endpoint.replace(f"{{{param}}}", str(args[param]))
        
        # Build query params
        query_params = {k: v for k, v in args.items() if f"{{{k}}}" not in tool.endpoint}
        
        try:
            logger.info(f"Executing tool: {tool_name} on {tool.agent_type}")
            
            if tool.method == "GET":
                result = await client.get(endpoint, params=query_params if query_params else None)
            else:
                result = await client.post(endpoint, json_body=args)
            
            logger.debug(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {"error": str(e), "tool": tool_name, "agent": tool.agent_type}
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured components"""
        result = {
            "thought": None,
            "action": None,
            "action_input": None,
            "final_answer": None
        }
        
        lines = response.strip().split("\n")
        current_key = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("Thought:"):
                if current_key:
                    result[current_key] = " ".join(current_value).strip()
                current_key = "thought"
                current_value = [line[8:].strip()]
            elif line.startswith("Action:"):
                if current_key:
                    result[current_key] = " ".join(current_value).strip()
                current_key = "action"
                current_value = [line[7:].strip()]
            elif line.startswith("Action Input:"):
                if current_key:
                    result[current_key] = " ".join(current_value).strip()
                current_key = "action_input"
                current_value = [line[13:].strip()]
            elif line.startswith("Final Answer:"):
                if current_key:
                    result[current_key] = " ".join(current_value).strip()
                current_key = "final_answer"
                current_value = [line[13:].strip()]
            else:
                current_value.append(line)
        
        if current_key:
            result[current_key] = " ".join(current_value).strip()
        
        # Parse action input as JSON
        if result["action_input"]:
            try:
                result["action_input"] = json.loads(result["action_input"])
            except json.JSONDecodeError:
                # Try to extract JSON from the string
                import re
                match = re.search(r'\{[^{}]*\}', result["action_input"])
                if match:
                    try:
                        result["action_input"] = json.loads(match.group())
                    except:
                        result["action_input"] = {"raw": result["action_input"]}
        
        return result
    
    async def run(self, query: str, user_context: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the ReAct loop to process a user query
        """
        trace = ReActTrace(
            query=query,
            model_name=self.llm.model
        )
        
        # Get memory context
        memory_context = await self.memory.retrieve(query) if self.memory else ""
        
        steps: List[ReActStep] = []
        observation = None
        
        with track_react_loop(task_type=self._classify_query(query)) as tracker:
            for iteration in range(self.max_iterations):
                tracker.record_step("think")
                
                # Build prompt
                previous_steps_text = ""
                for i, step in enumerate(steps):
                    previous_steps_text += f"\nStep {i+1}:\n"
                    previous_steps_text += f"Thought: {step.thought}\n"
                    if step.action:
                        previous_steps_text += f"Action: {step.action}\n"
                        previous_steps_text += f"Action Input: {json.dumps(step.action_input)}\n"
                    if step.observation:
                        previous_steps_text += f"Observation: {step.observation[:500]}...\n" if len(str(step.observation)) > 500 else f"Observation: {step.observation}\n"
                
                observation_prompt = ""
                if observation:
                    observation_prompt = f"Observation from previous action:\n{observation}"
                
                system_prompt = self.SYSTEM_PROMPT.format(
                    tools_description=get_tools_description(),
                    memory_context=memory_context or "No previous context available."
                )
                
                user_prompt = self.USER_PROMPT.format(
                    query=query,
                    previous_steps=previous_steps_text or "None yet.",
                    observation_prompt=observation_prompt
                )
                
                # Generate LLM response
                llm_response = await self.llm.generate(user_prompt, system_prompt)
                content = llm_response.get("content", "")
                
                trace.total_input_tokens += llm_response.get("input_tokens", 0)
                trace.total_output_tokens += llm_response.get("output_tokens", 0)
                
                # Parse response
                parsed = self._parse_llm_response(content)
                
                step = ReActStep(
                    step_number=iteration + 1,
                    thought=parsed["thought"] or content,
                    action=parsed["action"],
                    action_input=parsed["action_input"]
                )
                
                # Check for final answer
                if parsed["final_answer"]:
                    step.is_final = True
                    step.observation = parsed["final_answer"]
                    steps.append(step)
                    
                    trace.steps = steps
                    trace.final_answer = parsed["final_answer"]
                    trace.total_iterations = iteration + 1
                    trace.success = True
                    trace.completed_at = datetime.utcnow()
                    
                    tracker.complete(success=True)
                    
                    # Store in memory
                    if self.memory:
                        await self.memory.add_context(
                            doc_id=trace.trace_id,
                            text=f"Query: {query}\nAnswer: {parsed['final_answer']}",
                            metadata={"user_context": user_context}
                        )
                    
                    return {
                        "plan": self._summarize_plan(steps),
                        "result": parsed["final_answer"],
                        "steps": iteration + 1,
                        "trace_id": trace.trace_id,
                        "tokens_used": trace.total_input_tokens + trace.total_output_tokens
                    }
                
                # Execute action
                if parsed["action"] and parsed["action_input"]:
                    tracker.record_step("act")
                    
                    tool_result = await self._execute_tool(
                        parsed["action"],
                        parsed["action_input"]
                    )
                    observation = json.dumps(tool_result, indent=2, default=str)
                    step.observation = observation
                
                steps.append(step)
            
            # Max iterations reached
            tracker.complete(success=False)
            
            trace.steps = steps
            trace.total_iterations = self.max_iterations
            trace.success = False
            trace.completed_at = datetime.utcnow()
            
            return {
                "plan": self._summarize_plan(steps),
                "result": "Max iterations reached. Please try a more specific query.",
                "steps": self.max_iterations,
                "trace_id": trace.trace_id,
                "error": "max_iterations_exceeded"
            }
    
    def _classify_query(self, query: str) -> str:
        """Classify query type for metrics"""
        query_lower = query.lower()
        if "fail" in query_lower or "why" in query_lower or "diagnose" in query_lower or "debug" in query_lower or "rca" in query_lower:
            return "rca"
        elif "release" in query_lower or "ready" in query_lower:
            return "release_check"
        elif "jira" in query_lower or "ticket" in query_lower:
            return "jira_query"
        elif "build" in query_lower or "ci" in query_lower:
            return "ci_query"
        elif "security" in query_lower:
            return "security_query"
        elif "report" in query_lower:
            return "report"
        else:
            return "general"
    
    def _summarize_plan(self, steps: List[ReActStep]) -> str:
        """Summarize the execution plan"""
        if not steps:
            return "No plan executed"
        
        actions = [s.action for s in steps if s.action]
        if actions:
            return " -> ".join(actions)
        return steps[0].thought[:100] if steps[0].thought else "Direct response"
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self.http_clients.values():
            await client.close()

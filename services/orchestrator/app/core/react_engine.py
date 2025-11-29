import os
import sys
import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.utils import AsyncHttpClient
from nexus_lib.instrumentation import track_llm_usage, REACT_ITERATIONS

logger = logging.getLogger("nexus.react")

class Tool(BaseModel):
    name: str
    description: str
    agent_url: str
    endpoint: str
    method: str = "POST"

class ReActEngine:
    def __init__(self, memory_client):
        self.memory = memory_client
        self.tools = {
            "get_ticket_hierarchy": Tool(name="get_ticket_hierarchy", description="Fetch Jira ticket", agent_url="http://jira", endpoint="/hierarchy/{ticket_key}", method="GET"),
            "trigger_build": Tool(name="trigger_build", description="Trigger Jenkins", agent_url="http://git", endpoint="/build/{job_name}", method="POST")
        }
        self.http_client = AsyncHttpClient()

    async def _execute_tool(self, tool_name: str, args: Dict) -> Any:
        return {"status": "simulated_success", "data": "Tool executed"}

    @track_llm_usage(model_name="gemini-2.5-flash")
    async def run(self, user_query: str, user_context: Dict) -> Dict:
        # Mock ReAct Loop for MVP without LLM Cost
        steps = 2
        REACT_ITERATIONS.labels(task_type="success").observe(steps)
        if "/jira" in user_query:
             return {"plan": "Fetch Ticket -> Update", "result": "Ticket updated successfully.", "steps": steps}
        return {"plan": "Direct Answer", "result": f"Processed: {user_query}", "steps": steps}

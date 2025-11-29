import os
import sys
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader

sys.path.append(os.path.abspath("../../../shared"))
from nexus_lib.schemas.agent_contract import AgentTaskResponse
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import setup_tracing, track_tool_usage

setup_tracing("reporting-agent")
app = FastAPI(title="Nexus Reporting Agent")
app.add_middleware(MetricsMiddleware)
app.add_middleware(AuthMiddleware, secret_key="nexus-secret")

templates = Environment(loader=FileSystemLoader("services/agents/reporting_agent/templates"))

@app.post("/publish")
@track_tool_usage("publish_confluence_report")
async def publish_report(page_id: str, title: str, report_data: dict):
    try:
        template = templates.get_template("release_report.html")
        html_content = template.render(data=report_data)
        # Mock Confluence Call
        return AgentTaskResponse(task_id="trace", status="success", data={"url": f"https://confluence.fake/pages/{page_id}"})
    except Exception as e:
        return AgentTaskResponse(task_id="error", status="error", error_message=str(e))

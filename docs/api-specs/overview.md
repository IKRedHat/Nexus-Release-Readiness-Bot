# API Reference Overview

This document provides an overview of all API endpoints exposed by Nexus services. With v3.0, agents now expose tools via MCP (Model Context Protocol) over SSE, while the orchestrator uses LangGraph for stateful execution.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXUS API ARCHITECTURE (v3.0)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                      REST API Layer                                │     │
│   │  • /query - Natural language queries                              │     │
│   │  • /execute - Direct task execution                               │     │
│   │  • /approve - Human-in-the-loop approvals                         │     │
│   │  • /thread/{id} - Thread state management                         │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    LangGraph Orchestrator                          │     │
│   │  • StateGraph with planner, agent, human_review nodes             │     │
│   │  • LLM Factory (OpenAI, Gemini, Anthropic, Ollama, Groq, vLLM)   │     │
│   │  • AsyncPostgresSaver for state persistence                       │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    MCP Client Manager                              │     │
│   │  • Discovers tools from all MCP servers                           │     │
│   │  • Binds tools to LangChain for LangGraph                         │     │
│   │  • Manages SSE connections with auto-reconnect                    │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│        ┌───────────┬───────────┬───┴───┬───────────┬───────────┐           │
│        ▼           ▼           ▼       ▼           ▼           ▼           │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│   │  Jira   │ │  Git/CI │ │Reporting│ │ Hygiene │ │   RCA   │ │  Slack  │ │
│   │  :8001  │ │  :8002  │ │  :8003  │ │  :8005  │ │  :8006  │ │  :8084  │ │
│   │  (MCP)  │ │  (MCP)  │ │  (MCP)  │ │  (MCP)  │ │  (MCP)  │ │  (REST) │ │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Common Patterns

### Request Schema

All agents accept requests following this structure:

```python
class AgentTaskRequest(BaseModel):
    task_id: str                    # Unique trace ID (auto-generated if not provided)
    correlation_id: Optional[str]   # Parent request ID for tracing
    action: str                     # Action to execute
    payload: Dict[str, Any]         # Action-specific parameters
    priority: TaskPriority = NORMAL # Execution priority
    user_context: Optional[Dict]    # User metadata (Slack user, etc.)
    timeout_seconds: int = 30       # Execution timeout
    
    # LangGraph-specific fields (v3.0)
    thread_id: Optional[str]        # LangGraph thread ID for stateful execution
    checkpoint: Optional[str]       # Resume from checkpoint
    graph_state: Optional[Dict]     # Initial graph state
```

### Response Schema

All agents return responses following this structure:

```python
class AgentTaskResponse(BaseModel):
    task_id: str                    # Original task ID
    status: TaskStatus              # success, failed, timeout, pending
    data: Optional[Dict[str, Any]]  # Result data
    error_message: Optional[str]    # Error description if failed
    execution_time_ms: Optional[float]
    agent_type: AgentType
    
    # LangGraph-specific fields (v3.0)
    thread_id: Optional[str]        # Thread ID for continuation
    requires_approval: bool = False # Human approval needed
    graph_state: Optional[Dict]     # Current graph state
```

### Health Check

All agents expose a health endpoint:

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "agent-name",
  "mock_mode": true,
  "version": "3.0.0",
  "mcp_enabled": true
}
```

### MCP SSE Endpoint (v3.0)

MCP-enabled agents expose an SSE endpoint for tool discovery and invocation:

```http
GET /sse
```

This endpoint streams MCP messages for:
- Tool listing
- Tool invocation
- Results streaming

---

## Orchestrator API (Port 8080)

The central coordination service using LangGraph for stateful execution.

### Execute Query

```http
POST /query
Content-Type: application/json

{
  "query": "Is the v2.0 release ready?",
  "thread_id": "optional-thread-id"
}
```

Response:
```json
{
  "task_id": "task-abc123",
  "thread_id": "thread-xyz789",
  "status": "success",
  "data": {
    "answer": "The v2.0 release is READY (GO)...",
    "reasoning_steps": [...],
    "decision": "GO",
    "tools_used": ["get_ticket", "get_build_status"]
  },
  "llm_provider": "openai",
  "model_used": "gpt-4o",
  "tokens_used": 1250
}
```

### Execute Task

```http
POST /execute
Content-Type: application/json

{
  "task_id": "custom-id",
  "action": "release_check",
  "payload": {
    "version": "v2.0",
    "project_key": "PROJ"
  },
  "thread_id": "optional-thread-id"
}
```

### Approve Action (Human-in-the-Loop)

```http
POST /approve
Content-Type: application/json

{
  "thread_id": "thread-xyz789",
  "approved": true,
  "comment": "Approved by release manager"
}
```

Response:
```json
{
  "status": "resumed",
  "thread_id": "thread-xyz789",
  "next_step": "execute_action"
}
```

### Get Thread State

```http
GET /thread/{thread_id}
```

Response:
```json
{
  "thread_id": "thread-xyz789",
  "status": "waiting_approval",
  "messages": [...],
  "plan": "1. Check Jira tickets\n2. Verify build status",
  "current_step": 2,
  "pending_action": {
    "tool": "trigger_build",
    "args": {"job_name": "nexus-main"}
  }
}
```

### List Available Tools

```http
GET /tools
```

Response:
```json
{
  "tools": [
    {
      "name": "get_ticket",
      "description": "Get a Jira ticket by key",
      "server": "jira_agent",
      "parameters": {
        "ticket_key": {"type": "string", "required": true}
      }
    },
    {
      "name": "analyze_build_failure",
      "description": "Analyze a failed CI build",
      "server": "rca_agent",
      "parameters": {
        "job_name": {"type": "string", "required": true},
        "build_number": {"type": "integer", "required": true}
      }
    }
  ],
  "total": 25
}
```

### LLM Configuration

```http
GET /llm/config
```

Response:
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

---

## MCP Agent APIs

All MCP agents expose tools via SSE at `/sse`. Below are the REST endpoints and MCP tools for each agent.

### Jira Agent (Port 8001)

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_ticket` | Get a Jira ticket | `ticket_key` |
| `search_tickets` | Search tickets with JQL | `jql`, `max_results` |
| `update_ticket` | Update ticket fields | `ticket_key`, `fields` |
| `get_hierarchy` | Get epic/story hierarchy | `ticket_key`, `max_depth` |
| `get_sprint_stats` | Get sprint statistics | `project_key`, `sprint_name` |

#### REST Endpoints

```http
GET /health
GET /sse          # MCP SSE endpoint
GET /issue/{ticket_key}
GET /hierarchy/{ticket_key}?max_depth=3
GET /search?jql=...&max_results=50
POST /update-ticket
```

### Git/CI Agent (Port 8002)

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_pr_status` | Get PR details | `repo`, `pr_number` |
| `get_build_status` | Get Jenkins build | `job_name`, `build_number` |
| `trigger_build` | Trigger a build | `job_name`, `parameters` |
| `get_build_logs` | Get build logs | `job_name`, `build_number` |
| `get_security_scan` | Get security results | `repo` |
| `get_commit_diff` | Get commit changes | `repo`, `commit_sha` |

#### REST Endpoints

```http
GET /health
GET /sse          # MCP SSE endpoint
GET /repo/{repo_name}/health
GET /repo/{repo_name}/pr/{pr_number}
POST /build/{job_name}
GET /build/{job_name}/status
GET /security/{repo_name}
```

### Reporting Agent (Port 8003)

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `generate_report` | Generate release report | `version`, `data` |
| `publish_confluence` | Publish to Confluence | `page_id`, `content` |
| `get_report_preview` | Preview report HTML | `version` |

#### REST Endpoints

```http
GET /health
GET /sse          # MCP SSE endpoint
POST /generate
POST /analyze
POST /publish
GET /preview
```

### Jira Hygiene Agent (Port 8005)

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `check_project_hygiene` | Run hygiene check | `project_key`, `notify` |
| `get_violations` | Get hygiene violations | `project_key` |
| `get_user_violations` | Get user's violations | `email` |
| `get_fix_recommendations` | Get fix suggestions | `ticket_key` |
| `notify_hygiene_issues` | Send notifications | `project_key` |

#### REST Endpoints

```http
GET /health
GET /sse          # MCP SSE endpoint
GET /status
POST /run-check
GET /violations/{project_key}
```

### RCA Agent (Port 8006)

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_build_failure` | Full RCA analysis | `job_name`, `build_number`, `include_git_diff` |
| `get_build_logs` | Fetch raw logs | `job_name`, `build_number` |
| `get_commit_changes` | Get git diff | `repo`, `commit_sha` or `pr_id` |
| `get_rca_history` | Get past analyses | `job_name` |

#### REST Endpoints

```http
GET /health
GET /sse          # MCP SSE endpoint
POST /analyze
POST /webhook/jenkins
```

---

## Admin Dashboard API (Port 8088)

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |
| `GET` | `/stats` | Dashboard statistics |
| `GET` | `/mode` | Get current system mode |
| `POST` | `/mode` | Set system mode |
| `GET` | `/config` | Get all configuration |
| `GET` | `/config/{key}` | Get specific config value |
| `POST` | `/config` | Update config value |
| `DELETE` | `/config/{key}` | Delete config value |
| `GET` | `/health-check` | Check all agent health |

### LLM Configuration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/llm/providers` | Get available LLM providers |
| `GET` | `/llm/config` | Get current LLM configuration |
| `POST` | `/llm/config` | Update LLM configuration |
| `POST` | `/llm/test` | Test LLM connection |

```http
POST /llm/config
Content-Type: application/json

{
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "sk-...",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

### MCP Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/mcp/servers` | List connected MCP servers |
| `GET` | `/mcp/tools` | List all available tools |
| `POST` | `/mcp/reconnect` | Reconnect to MCP servers |

---

## Slack Agent API (Port 8084)

The Slack Agent uses REST endpoints (not MCP) for Slack-specific functionality.

### Send Notification

```http
POST /notify
Content-Type: application/json

{
  "channel": "C0123456789",
  "message": "Release v2.0 is ready!",
  "blocks": [...]
}
```

### Send Direct Message

```http
POST /send-dm
Content-Type: application/json

{
  "email": "alice@example.com",
  "message": "Your Jira tickets need attention",
  "blocks": [...]
}
```

### Webhook Endpoints

```http
POST /slack/commands      # Slash command handler
POST /slack/interactions  # Button/modal handler
POST /slack/events        # Events API handler
```

---

## Analytics Service API (Port 8086)

### KPI Dashboard

```http
GET /api/v1/kpis?time_range=7d&project=NEXUS
```

### Time Series Data

```http
GET /api/v1/timeseries/build_success_rate?time_range=7d&granularity=hour
```

### Predictive Analytics

```http
POST /api/v1/predict/release-date
POST /api/v1/predict/quality
POST /api/v1/predict/resources
```

### Anomaly Detection

```http
GET /api/v1/anomalies?time_range=24h&severity=high
```

---

## Prometheus Metrics Endpoints

All agents expose Prometheus metrics:

```http
GET /metrics
```

### Key Metrics

```prometheus
# LLM Usage (v3.0)
nexus_llm_tokens_total{provider, model, type}
nexus_llm_latency_seconds{provider, model}
nexus_llm_requests_total{provider, model, status}
nexus_llm_cost_dollars_total{provider, model}

# LangGraph Metrics (v3.0)
nexus_langgraph_executions_total{status}
nexus_langgraph_iteration_count{thread_id}
nexus_langgraph_human_approvals_total{approved}
nexus_langgraph_state_persistence_total{status}

# MCP Metrics (v3.0)
nexus_mcp_connections_total{server, status}
nexus_mcp_tool_calls_total{server, tool, status}
nexus_mcp_tool_latency_seconds{server, tool}
nexus_mcp_reconnections_total{server}

# HTTP Requests
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# Tool Usage
nexus_tool_usage_total{tool_name, status, agent_type}

# Hygiene
nexus_project_hygiene_score{project_key}
nexus_hygiene_checks_total{project_key, trigger_type}
nexus_hygiene_violations_total{project_key, violation_type}

# RCA
nexus_rca_requests_total{status, error_type, trigger, llm_provider}
nexus_rca_duration_seconds{job_name}
nexus_rca_confidence_score

# Business
nexus_release_decisions_total{decision}
nexus_jira_tickets_processed_total{action, project_key}
```

---

## Error Codes

| Status | Meaning |
|--------|---------|
| `success` | Request completed successfully |
| `failed` | Request failed (see error_message) |
| `timeout` | Request exceeded timeout |
| `pending` | Request is still processing |
| `waiting_approval` | Waiting for human approval |

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (dependency down) |

---

## Authentication

### JWT Token (Service-to-Service)

```http
Authorization: Bearer <jwt_token>
```

### Slack Verification

Slack requests are verified using the signing secret.

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Query endpoints | 100 req/min |
| Tool execution | 50 req/min |
| Hygiene checks | 10 req/min |
| RCA analysis | 20 req/min |
| RCA webhooks | 100 req/min |
| Analytics KPIs | 60 req/min |
| LLM config updates | 10 req/min |
| MCP reconnect | 5 req/min |

---

## Multi-Tenancy API

All endpoints support multi-tenant operation when enabled.

### Tenant Headers

```http
X-Tenant-ID: tenant-uuid-here
# or
X-Tenant-Slug: acme-corp
```

### Rate Limits by Plan

| Plan | API Requests | LLM Tokens/Day | Storage |
|------|--------------|----------------|---------|
| Free | 500/day | 50,000 | 100MB |
| Starter | 2,000/day | 200,000 | 1GB |
| Professional | 10,000/day | 1,000,000 | 10GB |
| Enterprise | 100,000/day | 10,000,000 | 100GB |

---

## LLM Configuration API

### Supported Providers

```http
GET /llm/providers
```

Response:
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
      "config_keys": ["api_key"],
      "description": "OpenAI GPT models"
    },
    {
      "id": "google",
      "name": "Google Gemini",
      "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
      "config_keys": ["api_key"],
      "description": "Google Gemini models"
    },
    {
      "id": "anthropic",
      "name": "Anthropic",
      "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
      "config_keys": ["api_key"],
      "description": "Anthropic Claude models"
    },
    {
      "id": "azure",
      "name": "Azure OpenAI",
      "models": [],
      "config_keys": ["api_key", "endpoint", "deployment_name", "api_version"],
      "description": "Azure-hosted OpenAI models"
    },
    {
      "id": "ollama",
      "name": "Ollama",
      "models": ["llama3", "mistral", "codellama"],
      "config_keys": ["base_url"],
      "description": "Self-hosted models via Ollama"
    },
    {
      "id": "groq",
      "name": "Groq",
      "models": ["llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
      "config_keys": ["api_key"],
      "description": "Ultra-fast inference"
    },
    {
      "id": "vllm",
      "name": "vLLM",
      "models": [],
      "config_keys": ["api_base", "api_key"],
      "description": "Self-hosted OpenAI-compatible server"
    },
    {
      "id": "mock",
      "name": "Mock",
      "models": [],
      "config_keys": [],
      "description": "Mock provider for testing"
    }
  ]
}
```

### Test Connection

```http
POST /llm/test
```

Response:
```json
{
  "status": "connected",
  "provider": "openai",
  "model": "gpt-4o",
  "latency_ms": 145,
  "response_preview": "Hello! How can I help you today?"
}
```

---

## MCP Tool Schema

MCP tools follow the Model Context Protocol specification:

```json
{
  "name": "analyze_build_failure",
  "description": "Analyze a failed CI/CD build to determine root cause",
  "inputSchema": {
    "type": "object",
    "properties": {
      "job_name": {
        "type": "string",
        "description": "Jenkins job name"
      },
      "build_number": {
        "type": "integer",
        "description": "Build number to analyze"
      },
      "include_git_diff": {
        "type": "boolean",
        "description": "Include git diff in analysis",
        "default": true
      }
    },
    "required": ["job_name", "build_number"]
  }
}
```

### Tool Invocation via MCP

```http
POST /sse
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "analyze_build_failure",
    "arguments": {
      "job_name": "nexus-main",
      "build_number": 142
    }
  },
  "id": "req-123"
}
```

Response (via SSE):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"analysis_id\": \"rca-123\", \"root_cause_summary\": \"...\"}"
      }
    ]
  },
  "id": "req-123"
}
```

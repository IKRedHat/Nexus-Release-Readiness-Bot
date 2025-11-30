# API Reference Overview

This document provides an overview of all API endpoints exposed by Nexus agents. Each agent follows a standardized contract for inter-service communication.

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
  "mock_mode": true
}
```

---

## Orchestrator API (Port 8080)

The central coordination service.

### Execute Query

```http
POST /query
Content-Type: application/json

{
  "query": "Is the v2.0 release ready?"
}
```

Response:
```json
{
  "task_id": "task-abc123",
  "status": "success",
  "data": {
    "answer": "The v2.0 release is READY (GO)...",
    "reasoning_steps": [...],
    "decision": "GO"
  }
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
  }
}
```

---

## Jira Agent API (Port 8081)

Handles Jira operations.

### Get Issue

```http
GET /issue/{ticket_key}
```

Response:
```json
{
  "task_id": "...",
  "status": "success",
  "data": {
    "key": "PROJ-123",
    "summary": "Implement feature X",
    "status": "In Progress",
    "assignee": {...},
    "story_points": 5,
    "labels": ["backend"]
  }
}
```

### Get Hierarchy

```http
GET /hierarchy/{ticket_key}?max_depth=3
```

Returns epic with nested stories and subtasks.

### Search Issues

```http
GET /search?jql=project=PROJ+AND+status="In+Progress"&max_results=50
```

### Update Ticket Status

```http
POST /update?key=PROJ-123&status=Done&comment=Completed
```

### Update Ticket Fields (NEW)

Used by the Hygiene Agent for batch field updates.

```http
POST /update-ticket
Content-Type: application/json

{
  "ticket_key": "PROJ-123",
  "fields": {
    "labels": ["backend", "api"],
    "fixVersions": [{"name": "v2.0.0"}],
    "customfield_10016": 5.0
  },
  "updated_by": "alice@example.com"
}
```

Response:
```json
{
  "task_id": "jira-abc123",
  "status": "success",
  "data": {
    "message": "Updated PROJ-123",
    "fields_updated": ["labels", "fixVersions", "customfield_10016"],
    "updated_by": "alice@example.com"
  }
}
```

### Get Sprint Stats

```http
GET /sprint-stats/{project_key}?sprint_name=Sprint+42
```

---

## Git/CI Agent API (Port 8082)

Handles GitHub and Jenkins operations.

### Get Repository Health

```http
GET /repo/{repo_name}/health
```

### Get Pull Request

```http
GET /repo/{repo_name}/pr/{pr_number}
```

### Trigger Build

```http
POST /build/{job_name}
Content-Type: application/json

{
  "parameters": {
    "BRANCH": "main",
    "ENVIRONMENT": "staging"
  }
}
```

### Get Build Status

```http
GET /build/{job_name}/status?build_number=latest
```

### Get Security Scan

```http
GET /security/{repo_name}
```

Response:
```json
{
  "task_id": "...",
  "status": "success",
  "data": {
    "risk_score": 25,
    "critical_vulnerabilities": 0,
    "high_vulnerabilities": 2,
    "report_url": "https://..."
  }
}
```

---

## Reporting Agent API (Port 8083)

Handles report generation and publishing.

### Generate Report

```http
POST /generate
Content-Type: application/json

{
  "report_type": "release_readiness",
  "version": "v2.0.0",
  "data": {
    "jira_stats": {...},
    "build_status": {...},
    "security_scan": {...}
  }
}
```

### Analyze for Decision

```http
POST /analyze
Content-Type: application/json

{
  "version": "v2.0.0",
  "project_key": "PROJ"
}
```

### Publish to Confluence

```http
POST /publish
Content-Type: application/json

{
  "page_id": "12345",
  "title": "Release v2.0.0 Readiness Report",
  "html_content": "<html>..."
}
```

### Preview Report

```http
GET /preview
```

---

## Slack Agent API (Port 8084)

Handles Slack interactions.

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

### Send Direct Message (NEW)

Used by the Hygiene Agent to send DMs.

```http
POST /send-dm
Content-Type: application/json

{
  "email": "alice@example.com",
  "message": "Your Jira tickets need attention",
  "blocks": [
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "..."}
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "Fix Now"},
          "action_id": "open_hygiene_fix_modal"
        }
      ]
    }
  ]
}
```

### Webhook Endpoints

These are called by Slack:

```http
POST /slack/commands      # Slash command handler
POST /slack/interactions  # Button/modal handler
POST /slack/events        # Events API handler
```

---

## Jira Hygiene Agent API (Port 8005) 🆕

Proactive quality gatekeeper for Jira data.

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "jira-hygiene-agent",
  "mock_mode": true,
  "scheduler_running": true,
  "next_scheduled_run": "2024-01-16T09:00:00+00:00"
}
```

### Run Hygiene Check (Manual Trigger)

```http
POST /run-check
Content-Type: application/json

{
  "project_key": "PROJ",    # Optional - checks all if not provided
  "notify": true,           # Send DM notifications
  "dry_run": false          # Check without sending notifications
}
```

Response:
```json
{
  "task_id": "hygiene-abc123",
  "status": "success",
  "data": {
    "check_id": "hygiene-abc123",
    "project": "PROJ",
    "total_checked": 45,
    "compliant": 38,
    "non_compliant": 7,
    "hygiene_score": 84.4,
    "violation_summary": {
      "Labels": 3,
      "Story Points": 2,
      "Fix Version": 2
    },
    "assignees_notified": 4,
    "dry_run": false
  }
}
```

### Get Status

```http
GET /status
```

Response:
```json
{
  "service": "jira-hygiene-agent",
  "config": {
    "projects": ["PROJ", "CORE"],
    "required_fields": ["Labels", "Fix Version", "Story Points", "Team"],
    "schedule": "09:00",
    "schedule_days": "mon-fri",
    "timezone": "UTC"
  },
  "scheduler": {
    "running": true,
    "next_run": "2024-01-16T09:00:00+00:00"
  },
  "jira": {
    "mock_mode": true,
    "url": "https://jira.example.com"
  }
}
```

### Get Violations

```http
GET /violations/{project_key}
```

Response:
```json
{
  "project": "PROJ",
  "hygiene_score": 84.4,
  "total_tickets": 45,
  "compliant": 38,
  "non_compliant": 7,
  "violations_by_assignee": [
    {
      "assignee": "Alice Developer",
      "email": "alice@example.com",
      "ticket_count": 3,
      "tickets": [
        {
          "key": "PROJ-123",
          "summary": "Implement feature",
          "missing_fields": ["Labels", "Story Points"]
        }
      ]
    }
  ],
  "violation_summary": {
    "Labels": 3,
    "Story Points": 2,
    "Fix Version": 2
  }
}
```

### Execute Task (Orchestrator Integration)

```http
POST /execute
Content-Type: application/json

{
  "task_id": "custom-id",
  "action": "run_check",
  "payload": {
    "project_key": "PROJ",
    "notify": true
  }
}
```

---

## Prometheus Metrics Endpoints

All agents expose Prometheus metrics:

```http
GET /metrics
```

### Key Metrics

```
# LLM Usage
nexus_llm_tokens_total{model_name, type}
nexus_llm_latency_seconds{model_name}

# Tool Usage
nexus_tool_usage_total{tool_name, status, agent_type}

# HTTP Requests
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# Hygiene (Port 8005)
nexus_project_hygiene_score{project_key}
nexus_hygiene_checks_total{project_key, trigger_type}
nexus_hygiene_violations_total{project_key, violation_type}
nexus_hygiene_tickets_checked{project_key}
nexus_hygiene_compliant_tickets{project_key}

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

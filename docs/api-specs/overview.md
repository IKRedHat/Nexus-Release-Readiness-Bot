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
  "next_scheduled_run": "2025-12-01T09:00:00+00:00"
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
    "next_run": "2025-12-01T09:00:00+00:00"
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

## RCA Agent API (Port 8006) 🆕

Smart Root Cause Analysis for build failures with auto-trigger and Slack notifications.

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "rca-agent",
  "version": "2.2.0",
  "timestamp": "2025-12-01T10:30:00Z",
  "config": {
    "jenkins_mock": true,
    "github_mock": true,
    "llm_mock": true,
    "llm_model": "gemini-1.5-pro",
    "slack_mock": true,
    "auto_analyze": true,
    "release_channel": "#release-notifications"
  }
}
```

### Analyze Build Failure

```http
POST /analyze
Content-Type: application/json

{
  "job_name": "nexus-main",
  "build_number": 142,
  "build_url": "http://jenkins:8080/job/nexus-main/142/",
  "repo_name": "nexus-backend",
  "branch": "feature/new-api",
  "pr_id": 123,
  "commit_sha": "a1b2c3d4e5f6",
  "include_git_diff": true,
  "notify": true,
  "channel": "#release-notifications",
  "pr_owner_email": "developer@example.com"
}
```

Response:
```json
{
  "analysis_id": "rca-nexus-main-142-1701432600",
  "root_cause_summary": "Test failure in TestUserService due to validate_email returning None",
  "error_type": "test_failure",
  "error_message": "AttributeError: 'NoneType' object has no attribute 'is_valid'",
  "confidence_score": 0.92,
  "confidence_level": "high",
  "suspected_commit": "a1b2c3d4e5f6",
  "suspected_author": "developer@example.com",
  "suspected_files": [
    {
      "file_path": "src/api/users.py",
      "change_type": "modified",
      "lines_added": 6,
      "lines_deleted": 1,
      "relevant_lines": [87, 88, 89]
    }
  ],
  "fix_suggestion": "Add null check before accessing is_valid attribute...",
  "fix_code_snippet": "if result is not None:\n    return result.is_valid",
  "analyzed_at": "2025-12-01T10:30:00Z",
  "analysis_duration_seconds": 8.5,
  "notification_sent": true,
  "notification_channel": "#release-notifications",
  "pr_owner_tagged": "developer@example.com"
}
```

### Jenkins Webhook (Auto-Trigger)

Configure Jenkins to call this endpoint on build failures:

```http
POST /webhook/jenkins
Content-Type: application/json

{
  "name": "nexus-main",
  "number": 142,
  "url": "http://jenkins:8080/job/nexus-main/142/",
  "result": "FAILURE",
  "git_url": "https://github.com/org/repo.git",
  "git_branch": "feature/new-api",
  "git_commit": "a1b2c3d4e5f6",
  "pr_number": 123,
  "pr_author_email": "developer@example.com",
  "release_channel": "#release-notifications"
}
```

Response:
```json
{
  "status": "queued",
  "message": "RCA analysis queued, Slack notification will be sent",
  "job": "nexus-main",
  "build": 142,
  "channel": "#release-notifications"
}
```

### Execute Task (Orchestrator Integration)

```http
POST /execute
Content-Type: application/json

{
  "task_id": "custom-id",
  "action": "analyze_build_failure",
  "payload": {
    "job_name": "nexus-main",
    "build_number": 142,
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

# RCA (Port 8006)
nexus_rca_requests_total{status, error_type, trigger}
nexus_rca_duration_seconds{job_name}
nexus_rca_confidence_score                 # Histogram
nexus_rca_active_analyses                  # Gauge
nexus_rca_webhooks_total{job_name, status}
nexus_rca_notifications_total{channel, status}
nexus_llm_tokens_total{model, task_type}   # task_type=rca

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
| RCA analysis | 20 req/min |
| RCA webhooks | 100 req/min |

---

## Multi-Tenancy API

All endpoints support multi-tenant operation when enabled.

### Tenant Headers

```http
X-Tenant-ID: tenant-uuid-here
# or
X-Tenant-Slug: acme-corp
```

### Tenant Resolution

Requests are resolved to tenants via:
1. **Header**: `X-Tenant-ID` or `X-Tenant-Slug`
2. **Subdomain**: `acme.nexus.example.com`
3. **API Key**: Tenant association via Bearer token

### Tenant Context

All requests include tenant context:

```python
class TenantContext:
    tenant_id: str
    slug: str
    name: str
    plan: TenantPlan          # free, starter, professional, enterprise
    status: TenantStatus      # active, suspended, pending
    limits: TenantLimits
    config: TenantConfig
```

### Rate Limits by Plan

| Plan | API Requests | LLM Tokens/Day | Storage |
|------|--------------|----------------|---------|
| Free | 500/day | 50,000 | 100MB |
| Starter | 2,000/day | 200,000 | 1GB |
| Professional | 10,000/day | 1,000,000 | 10GB |
| Enterprise | 100,000/day | 10,000,000 | 100GB |

---

## AI Recommendations API

### Get Recommendations

```http
GET /recommendations
# or
GET /recommendations?project_key=PROJ
```

Response:
```json
{
  "recommendations": [
    {
      "id": "rec-abc123",
      "type": "BLOCKERS_RESOLUTION",
      "priority": "critical",
      "title": "Address blocking issues before release",
      "description": "2 blocking issues are preventing release readiness",
      "action_items": [
        "Resolve PROJ-145: API timeout issue",
        "Resolve PROJ-147: Database connection failure"
      ],
      "metadata": {
        "blocker_count": 2,
        "affected_version": "v2.0.0"
      },
      "created_at": "2025-11-30T10:30:00Z"
    },
    {
      "id": "rec-def456",
      "type": "HYGIENE_IMPROVEMENT",
      "priority": "high",
      "title": "Improve hygiene score from 78% to 90%+",
      "description": "5 tickets are missing required fields",
      "action_items": [
        "Add Story Points to 3 tickets",
        "Add Labels to 2 tickets"
      ],
      "metadata": {
        "current_score": 78,
        "target_score": 90,
        "violations": {
          "Story Points": 3,
          "Labels": 2
        }
      }
    },
    {
      "id": "rec-ghi789",
      "type": "RELEASE_TIMING",
      "priority": "medium",
      "title": "Consider releasing Tuesday instead of Friday",
      "description": "Historical data shows higher success rates on Tuesdays",
      "action_items": [
        "Schedule release for Tuesday afternoon",
        "Avoid Friday deployments"
      ],
      "metadata": {
        "tuesday_success_rate": 95,
        "friday_success_rate": 78
      }
    }
  ],
  "summary": {
    "total": 3,
    "by_priority": {
      "critical": 1,
      "high": 1,
      "medium": 1,
      "low": 0
    }
  },
  "generated_at": "2025-11-30T10:30:00Z"
}
```

### Recommendation Types

| Type | Description |
|------|-------------|
| `RELEASE_TIMING` | Optimal release day/time suggestions |
| `HYGIENE_IMPROVEMENT` | Jira data quality improvements |
| `VELOCITY_OPTIMIZATION` | Sprint velocity recommendations |
| `RISK_MITIGATION` | Security and risk reduction |
| `BLOCKERS_RESOLUTION` | Critical blocker handling |
| `PROCESS_IMPROVEMENT` | Long-term process enhancements |

---

## LLM API (Internal)

The LLM client is used internally by the orchestrator.

### Configuration

Environment variables:
```bash
LLM_PROVIDER=google           # google, openai, mock
LLM_MODEL=gemini-2.0-flash    # Model name
LLM_API_KEY=your-api-key      # API key
LLM_TEMPERATURE=0.7           # Generation temperature
LLM_MAX_TOKENS=4096           # Max output tokens
```

### Supported Providers

| Provider | Models | Features |
|----------|--------|----------|
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | Streaming, function calling |
| **OpenAI** | gpt-4o, gpt-4-turbo | Streaming, function calling |
| **Mock** | - | Development/testing |

### Usage Metrics

```
nexus_llm_tokens_total{model_name, type}      # input/output tokens
nexus_llm_latency_seconds{model_name}         # Request latency
nexus_llm_cost_dollars_total{model_name}      # Estimated cost
nexus_llm_requests_total{model_name, status}  # Success/failure count
```

---

## Slack App Home API

### Event Handler

```http
POST /slack/events
Content-Type: application/json

{
  "type": "event_callback",
  "event": {
    "type": "app_home_opened",
    "user": "U0123456789",
    "tab": "home"
  }
}
```

### App Home View Structure

```json
{
  "type": "home",
  "blocks": [
    {"type": "header", "text": {"type": "plain_text", "text": "🚀 Nexus Release Automation"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": "Good morning! Here's your dashboard."}},
    {"type": "divider"},
    {"type": "section", "text": {"type": "mrkdwn", "text": "*⚡ Quick Actions*"}},
    {
      "type": "actions",
      "elements": [
        {"type": "button", "text": {"type": "plain_text", "text": "📊 Release Status"}, "action_id": "quick_release_status"},
        {"type": "button", "text": {"type": "plain_text", "text": "🔧 Hygiene Check"}, "action_id": "quick_hygiene_check"},
        {"type": "button", "text": {"type": "plain_text", "text": "📝 Generate Report"}, "action_id": "quick_generate_report"}
      ]
    },
    {"type": "divider"},
    {"type": "section", "text": {"type": "mrkdwn", "text": "*📈 Release Status*\n🟡 CONDITIONAL | 87% complete | 2 blockers"}}
  ]
}
```

### Quick Action Handlers

| Action ID | Description |
|-----------|-------------|
| `quick_release_status` | Opens release status modal |
| `quick_hygiene_check` | Triggers hygiene check for user's projects |
| `quick_generate_report` | Opens report generation modal |
| `open_hygiene_fix_modal` | Opens hygiene fix modal |
| `view_all_recommendations` | Shows all AI recommendations |

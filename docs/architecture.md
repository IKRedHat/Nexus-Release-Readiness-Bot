# Architecture

This document describes the architecture of the Nexus Release Automation System, including its core components, communication patterns, and design decisions.

## System Overview

Nexus is a multi-agent system that uses a ReAct (Reasoning + Acting) architecture to orchestrate specialized agents for release readiness assessments and proactive quality management.

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Slack[Slack Workspace]
        API[REST API]
        AdminUI[Admin Dashboard UI<br/>Vercel/Docker]
    end
    
    subgraph Gateway["Gateway Layer"]
        SlackAgent[Slack Agent<br/>Port 8084]
        AdminDash[Admin Dashboard API<br/>Port 8088]
    end
    
    subgraph Core["Core Layer"]
        Orchestrator[Central Orchestrator<br/>Port 8080]
        ReAct[ReAct Engine]
        SpecRegistry[Specialist Registry]
        Memory[(Vector Memory<br/>ChromaDB/pgvector)]
        LLM[LLM Provider<br/>Gemini/OpenAI]
        ConfigMgr[ConfigManager<br/>Redis-backed]
    end
    
    subgraph Agents["Specialist Agents"]
        JiraAgent[Jira Agent<br/>Port 8081]
        GitAgent[Git/CI Agent<br/>Port 8082]
        ReportAgent[Reporting Agent<br/>Port 8083]
        HygieneAgent[Jira Hygiene Agent<br/>Port 8085]
        RCAAgent[RCA Agent<br/>Port 8006]
        Analytics[Analytics Service<br/>Port 8086]
        Webhooks[Webhooks Service<br/>Port 8087]
        Scheduling[Scheduling Agent]
    end
    
    subgraph External["External Systems"]
        Jira[Jira Cloud/Server]
        GitHub[GitHub]
        Jenkins[Jenkins CI]
        Confluence[Confluence]
        Smartsheet[Smartsheet]
    end
    
    subgraph Observability["Observability"]
        Prometheus[Prometheus<br/>Port 9090]
        Grafana[Grafana<br/>Port 3000]
        Jaeger[Jaeger<br/>Port 16686]
    end
    
    Slack --> SlackAgent
    API --> Orchestrator
    AdminUI --> AdminDash
    SlackAgent --> Orchestrator
    AdminDash --> ConfigMgr
    AdminDash --> Agents
    
    Orchestrator --> ReAct
    Orchestrator --> SpecRegistry
    SpecRegistry --> Agents
    ReAct --> Memory
    ReAct --> LLM
    ConfigMgr --> Agents
    
    HygieneAgent --> JiraAgent
    HygieneAgent --> SlackAgent
    HygieneAgent --> Jira
    
    Orchestrator --> RCAAgent
    RCAAgent --> GitAgent
    RCAAgent --> SlackAgent
    RCAAgent --> Jenkins
    RCAAgent --> GitHub
    Jenkins -.->|Webhook| RCAAgent
    
    JiraAgent --> Jira
    GitAgent --> GitHub
    GitAgent --> Jenkins
    ReportAgent --> Confluence
    
    AdminDash --> Smartsheet
    
    Analytics --> Prometheus
    Analytics --> Memory
    Orchestrator --> Analytics
    
    Webhooks --> External
    
    All --> Prometheus
    Prometheus --> Grafana
    All --> Jaeger
```

---

## High-Level Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Slack
    participant SlackAgent
    participant Orchestrator
    participant Agents
    participant External
    
    User->>Slack: /nexus status v2.0
    Slack->>SlackAgent: Command payload
    SlackAgent->>Orchestrator: AgentTaskRequest
    
    loop ReAct Loop
        Orchestrator->>Orchestrator: Thought (reasoning)
        Orchestrator->>Agents: Action (tool call)
        Agents->>External: API request
        External-->>Agents: Response
        Agents-->>Orchestrator: Observation
    end
    
    Orchestrator-->>SlackAgent: Final response
    SlackAgent-->>Slack: Block Kit message
    Slack-->>User: Rich formatted result
```

---

## Core Components

### 1. Central Orchestrator

The brain of the system. Receives requests and coordinates multi-agent workflows using the ReAct engine.

**Responsibilities:**
- Parse and understand user queries
- Plan multi-step execution workflows
- Coordinate agent interactions
- Aggregate results and generate responses
- Maintain conversation context

**Technology:**
- FastAPI for HTTP API
- Pydantic for data validation
- OpenTelemetry for distributed tracing

### 2. ReAct Reasoning Engine

The ReAct (Reasoning + Acting) engine implements an LLM-powered reasoning loop that combines thinking with action.

```mermaid
flowchart LR
    Query[User Query] --> Think[Thought]
    Think --> Act[Action]
    Act --> Observe[Observation]
    Observe --> Think
    Think --> Answer[Final Answer]
```

**The ReAct Loop:**

1. **Thought**: The LLM reasons about what information is needed
2. **Action**: Calls a tool to gather data
3. **Observation**: Reviews the tool's response
4. **Repeat**: Continue until sufficient information
5. **Final Answer**: Synthesize and respond

**Example Trace:**

```
User: "Is the v2.0 release ready?"

Thought: I need to check the Jira sprint status to understand ticket completion.
Action: get_sprint_stats
Action Input: {"project_key": "PROJ"}
Observation: {"completed_tickets": 42, "total_tickets": 45, "completion_rate": 93.3}

Thought: Good progress on tickets. Now I should check security.
Action: get_security_scan
Action Input: {"repo_name": "nexus/backend"}
Observation: {"risk_score": 25, "critical_vulnerabilities": 0, "high_vulnerabilities": 2}

Thought: No critical vulnerabilities. Let me check the build status.
Action: get_build_status
Action Input: {"job_name": "nexus-main"}
Observation: {"status": "SUCCESS", "test_results": {"passed": 245, "failed": 0}}

Thought: I have enough information to make a decision.
Final Answer: The v2.0 release is READY (GO). 93.3% ticket completion, 
              no critical vulnerabilities, and all tests passing.
```

### 3. Vector Memory

RAG-enabled memory system for maintaining context across conversations.

**Features:**
- Stores previous interactions and decisions
- Retrieves relevant context for new queries
- Supports ChromaDB (local) and pgvector (PostgreSQL)

**Use Cases:**
- "Last time we had a similar issue..."
- Historical release data retrieval
- Learning from past decisions

---

## Agent Contracts

All agents follow a standardized contract for communication.

### Request Schema

```python
class AgentTaskRequest(BaseModel):
    task_id: str           # Unique trace ID
    correlation_id: str    # Parent request ID
    action: str            # Action to execute
    payload: Dict          # Action parameters
    priority: TaskPriority # Execution priority
    user_context: Dict     # User metadata
    timeout_seconds: int   # Execution timeout
```

### Response Schema

```python
class AgentTaskResponse(BaseModel):
    task_id: str           # Original task ID
    status: TaskStatus     # success, failed, timeout
    data: Dict             # Result data
    error_message: str     # Error if failed
    execution_time_ms: float
    agent_type: AgentType
```

---

## Specialized Agents

### Jira Agent (Port 8081)

Handles all Jira-related operations including ticket fetching, updates, and hierarchy traversal.

**Capabilities:**
- Fetch ticket details and hierarchies
- Search using JQL
- Update ticket status and fields
- Add comments
- Get sprint statistics

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issue/{key}` | GET | Fetch single ticket |
| `/hierarchy/{key}` | GET | Fetch epic → stories → subtasks |
| `/search` | GET | JQL search |
| `/update` | POST | Update status/add comment |
| `/update-ticket` | POST | Update multiple fields (for hygiene fixes) |
| `/sprint-stats/{project}` | GET | Sprint metrics |

### Git/CI Agent (Port 8082)

Manages GitHub and Jenkins interactions.

**Capabilities:**
- Check repository health
- Get PR status and approvals
- Trigger Jenkins builds
- Fetch build results
- Run security scans

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repo/{name}/health` | GET | Repository health |
| `/repo/{name}/pr/{number}` | GET | PR details |
| `/build/{job}` | POST | Trigger build |
| `/build/{job}/status` | GET | Build status |
| `/security/{repo}` | GET | Security scan |

### Reporting Agent (Port 8083)

Generates and publishes reports.

**Capabilities:**
- Generate HTML reports with Jinja2
- Analyze release readiness
- Publish to Confluence
- Calculate Go/No-Go decisions

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Generate HTML report |
| `/analyze` | POST | Analyze for Go/No-Go |
| `/publish` | POST | Publish to Confluence |
| `/preview` | GET | Preview sample report |

### Slack Agent (Port 8084)

Handles Slack workspace interactions with rich interactive experiences.

**Capabilities:**
- Process slash commands
- Open Block Kit modals
- Send rich messages and DMs
- Handle button interactions
- Support hygiene fix modals

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/slack/commands` | POST | Slash command handler |
| `/slack/interactions` | POST | Button/modal interactions |
| `/slack/events` | POST | Events API handler |
| `/notify` | POST | Send channel notification |
| `/send-dm` | POST | Send direct message by email |

### Jira Hygiene Agent (Port 8085)

Proactive quality gatekeeper that monitors and enforces Jira data hygiene through scheduled checks and interactive notifications.

```mermaid
flowchart LR
    subgraph Schedule["Scheduled Trigger"]
        Cron[APScheduler<br/>Weekdays 9AM]
    end
    
    subgraph Hygiene["Jira Hygiene Agent"]
        Fetch[Fetch Active Tickets]
        Validate[Validate Fields]
        Score[Calculate Score]
        Group[Group by Assignee]
    end
    
    subgraph Notify["Notification Flow"]
        DM[Slack DM with Buttons]
        Modal[Fix Modal]
        Update[Update Jira]
    end
    
    Cron --> Fetch
    Fetch --> Validate
    Validate --> Score
    Score --> Group
    Group --> DM
    DM --> Modal
    Modal --> Update
```

**Capabilities:**
- **Scheduled Hygiene Checks**: Runs automatically on weekdays at 9:00 AM
- **Field Validation**: Checks for missing Labels, Fix Version, Affected Version, Story Points, Team
- **Hygiene Scoring**: Calculates `nexus_project_hygiene_score` (0-100%)
- **Interactive Notifications**: Sends Slack DMs with "Fix Tickets Now" button
- **Modal-Based Fixes**: Users can fix violations directly from Slack without leaving the app

**Validation Rules:**

| Field | Jira Field ID | Why It Matters |
|-------|---------------|----------------|
| Labels | `labels` | Categorization and filtering |
| Fix Version | `fixVersions` | Release planning |
| Affected Version | `versions` | Impact analysis |
| Story Points | `customfield_10016` | Capacity planning |
| Team/Contributors | `customfield_10001` | Ownership tracking |

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with scheduler status |
| `/run-check` | POST | Manual trigger for hygiene check |
| `/status` | GET | Configuration and scheduler info |
| `/violations/{project}` | GET | Get violations for a project |
| `/execute` | POST | Orchestrator integration |

**Prometheus Metrics:**

```
# Hygiene Score (0-100%)
nexus_project_hygiene_score{project_key}

# Check Counters
nexus_hygiene_checks_total{project_key, trigger_type}
nexus_hygiene_violations_total{project_key, violation_type}

# Ticket Counts
nexus_hygiene_tickets_checked{project_key}
nexus_hygiene_compliant_tickets{project_key}
```

---

## Interactive Hygiene Fix Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant HygieneAgent
    participant Jira
    participant SlackAgent
    participant User
    participant JiraAgent
    
    Scheduler->>HygieneAgent: Trigger Check (9AM)
    HygieneAgent->>Jira: Fetch Active Tickets
    Jira-->>HygieneAgent: Tickets Data
    
    HygieneAgent->>HygieneAgent: Validate Fields
    HygieneAgent->>HygieneAgent: Calculate Score
    HygieneAgent->>HygieneAgent: Group by Assignee
    
    HygieneAgent->>SlackAgent: POST /send-dm
    SlackAgent->>User: DM with Fix Button
    
    User->>SlackAgent: Click "Fix Tickets Now"
    SlackAgent->>User: Open Modal
    
    User->>SlackAgent: Submit Modal
    SlackAgent->>JiraAgent: POST /update-ticket
    JiraAgent->>Jira: Update Fields
    Jira-->>JiraAgent: Success
    JiraAgent-->>SlackAgent: Confirmation
    SlackAgent->>User: Success DM
```

---

### RCA Agent (Port 8006) 🆕

Smart Root Cause Analysis agent that automatically diagnoses build failures using LLM-powered log analysis and git correlation.

```mermaid
flowchart TB
    subgraph Trigger["Trigger Sources"]
        Webhook[Jenkins Webhook<br/>Build Failure]
        Manual[Manual Request<br/>/analyze API]
        Orchestrator[Orchestrator<br/>Natural Language]
    end
    
    subgraph RCA["RCA Agent"]
        Fetch[Fetch Console Logs]
        Truncate[Truncate for LLM]
        GitDiff[Fetch Git Diff]
        LLM[Gemini 1.5 Pro<br/>Analysis]
        Format[Format Results]
    end
    
    subgraph Output["Output"]
        Response[API Response]
        Slack[Slack Notification<br/>@PR Owner]
    end
    
    Webhook --> Fetch
    Manual --> Fetch
    Orchestrator --> Fetch
    
    Fetch --> Truncate
    Truncate --> GitDiff
    GitDiff --> LLM
    LLM --> Format
    
    Format --> Response
    Format --> Slack
```

**Capabilities:**
- **Auto-Trigger**: Jenkins webhook triggers RCA on FAILURE/UNSTABLE builds
- **Slack Notifications**: Sends analysis to release channel with @PR-owner mention
- **Log Truncation**: Smart truncation preserves errors while fitting LLM context
- **Git Correlation**: Maps errors to specific files and commits
- **Confidence Scoring**: Rates analysis reliability (high/medium/low/uncertain)

**Analysis Flow:**

```mermaid
sequenceDiagram
    participant Jenkins
    participant RCA as RCA Agent
    participant GitHub
    participant Gemini as Gemini LLM
    participant Slack
    
    Jenkins->>RCA: POST /webhook/jenkins
    Note over RCA: Build FAILURE detected
    
    RCA->>Jenkins: Fetch Console Output
    Jenkins-->>RCA: Build Logs (100KB+)
    
    RCA->>RCA: Truncate Logs<br/>(keep errors, head, tail)
    
    RCA->>GitHub: Fetch Commit Diff
    GitHub-->>RCA: File Changes
    
    RCA->>Gemini: Send [Logs + Diff]<br/>System: "You are a DevOps Debugger"
    Gemini-->>RCA: Analysis Result
    
    RCA->>RCA: Parse & Score Confidence
    
    RCA->>Slack: POST /notify
    Note over Slack: @pr-owner tagged<br/>Root cause + Fix suggestion
```

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with config status |
| `/analyze` | POST | Analyze build failure (with optional notify) |
| `/webhook/jenkins` | POST | Jenkins auto-trigger webhook |
| `/execute` | POST | Orchestrator integration |
| `/metrics` | GET | Prometheus metrics |

**Prometheus Metrics:**

```
# Request Metrics
nexus_rca_requests_total{status, error_type, trigger}
nexus_rca_duration_seconds{job_name}
nexus_rca_confidence_score  # Histogram 0.0-1.0

# Webhook Metrics
nexus_rca_webhooks_total{job_name, status}

# Notification Metrics
nexus_rca_notifications_total{channel, status}

# LLM Usage
nexus_llm_tokens_total{model, task_type="rca"}
nexus_rca_active_analyses  # Gauge
```

---

### Analytics Service (Port 8086) 🆕

Advanced analytics and insights service providing DORA metrics, predictions, and anomaly detection.

```mermaid
flowchart TB
    subgraph DataSources["Data Sources"]
        Prometheus[Prometheus]
        Postgres[(PostgreSQL)]
        Redis[(Redis Cache)]
    end
    
    subgraph Analytics["Analytics Service"]
        Collector[Data Collector]
        Aggregator[Metric Aggregator]
        ML[ML Models]
        Predictor[Prediction Engine]
        Anomaly[Anomaly Detector]
    end
    
    subgraph Output["Outputs"]
        KPIs[KPI Dashboard]
        Timeseries[Time Series API]
        Predictions[Predictions API]
        Alerts[Anomaly Alerts]
        Insights[AI Insights]
    end
    
    Prometheus --> Collector
    Postgres --> Collector
    Redis --> Collector
    
    Collector --> Aggregator
    Aggregator --> ML
    ML --> Predictor
    ML --> Anomaly
    
    Aggregator --> KPIs
    Aggregator --> Timeseries
    Predictor --> Predictions
    Anomaly --> Alerts
    ML --> Insights
```

**Capabilities:**
- **DORA Metrics**: Deployment frequency, lead time, MTTR, change failure rate
- **KPI Dashboard**: Real-time quality scores and health indicators
- **Time Series Analysis**: Historical trends with flexible granularity
- **Predictive Analytics**: Release date and quality score forecasting
- **Anomaly Detection**: Automatic detection of unusual patterns
- **Team Performance**: Compare teams by velocity and quality
- **AI Insights**: Intelligent recommendations based on patterns

**Dashboard Preview:**

![Analytics Dashboard](assets/mockups/analytics-dashboard.svg)

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/kpis` | GET | Get KPI dashboard data |
| `/api/v1/timeseries/{metric}` | GET | Get time series data |
| `/api/v1/trends` | GET | Get trend analysis |
| `/api/v1/predict/release-date` | POST | Predict release date |
| `/api/v1/predict/quality` | POST | Predict quality score |
| `/api/v1/anomalies` | GET | Get detected anomalies |
| `/api/v1/teams` | GET | Get team performance |
| `/api/v1/insights` | GET | Get AI-powered insights |

**Prometheus Metrics:**

```
# Analytics Queries
nexus_analytics_queries_total{query_type, time_range}

# KPIs
nexus_release_velocity{project}
nexus_quality_score{project}
nexus_team_efficiency{team}

# Predictions
nexus_prediction_accuracy{prediction_type}
```

---

### Webhooks Service (Port 8087)

Event-driven webhook service for integrating with external systems.

**Capabilities:**
- **25+ Event Types**: Release, build, ticket, security, hygiene events
- **HMAC Security**: Cryptographic signature verification
- **Auto-Retry**: Exponential backoff with configurable attempts
- **Rate Limiting**: Per-subscription and global limits
- **Event Filtering**: Subscribe to specific event patterns
- **Delivery Tracking**: Full audit trail of deliveries

**Supported Event Types:**
- `release.*` - Release lifecycle events
- `build.*` - CI/CD pipeline events
- `ticket.*` - Jira ticket events
- `security.*` - Security scan events
- `hygiene.*` - Hygiene check events
- `rca.*` - RCA analysis events

---

### Admin Dashboard (Port 8088)

Web-based management interface for system configuration, monitoring, and release management.

```mermaid
flowchart TB
    subgraph Frontend["React Frontend"]
        UI[Vite + React + Tailwind]
        Pages[Dashboard / Config / Metrics / Releases]
    end
    
    subgraph Backend["FastAPI Backend"]
        API[REST API]
        Config[ConfigManager]
        Health[Health Aggregator]
        Release[Release Manager]
    end
    
    subgraph Storage["Data Layer"]
        Redis[(Redis)]
        Agents[Agent APIs]
        External[External Sources]
    end
    
    UI --> API
    Pages --> API
    
    API --> Config
    API --> Health
    API --> Release
    
    Config --> Redis
    Health --> Agents
    Release --> External
```

**Capabilities:**
- **Dynamic Configuration**: Change settings without service restarts
- **Mode Switching**: Toggle Mock/Live mode instantly across all agents
- **Health Monitoring**: Real-time agent health with auto-refresh
- **Observability Dashboard**: Integrated metrics, charts, and Grafana links
- **Release Management**: Track versions, dates, milestones from external sources

**Release Management Features:**
- Create and track releases with target dates
- Import from Smartsheet, CSV, or webhooks
- Visual release calendar view
- Milestone and risk tracking
- Release readiness metrics

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health-check` | GET | Service health |
| `/mode` | GET/POST | Get/set mock/live mode |
| `/config` | GET/PUT | Configuration management |
| `/agents/health` | GET | All agents health status |
| `/api/metrics` | GET | Aggregated observability metrics |
| `/releases` | GET/POST | Release CRUD |
| `/releases/calendar` | GET | Calendar view data |
| `/releases/sync/smartsheet` | POST | Import from Smartsheet |

**Deployment Options:**
- **Docker**: Included in docker-compose with backend API
- **Vercel**: Frontend deployed to Vercel CDN for production
- **Kubernetes**: Helm chart with separate frontend/backend pods

---

### Specialist Registry

The Specialist Registry is a centralized service discovery and health monitoring system for all agents.

```mermaid
flowchart LR
    subgraph Orchestrator["Orchestrator"]
        ReAct[ReAct Engine]
        Registry[SpecialistRegistry]
    end
    
    subgraph Specialists["Specialist Agents"]
        Jira[Jira Agent]
        Git[Git/CI Agent]
        Slack[Slack Agent]
        Report[Reporting Agent]
        Hygiene[Hygiene Agent]
        RCA[RCA Agent]
        Analytics[Analytics]
        Webhooks[Webhooks]
        Scheduling[Scheduling]
    end
    
    ReAct --> Registry
    Registry --> Specialists
    Registry -.->|Health Monitor| Specialists
```

**Capabilities:**
- **Service Discovery**: Dynamic URL resolution from environment or K8s
- **Health Monitoring**: Background health checks every 30 seconds
- **Tool Registry**: Central catalog of all available tools per agent
- **Critical Verification**: Validates essential specialists on startup

**Registered Specialists (9 agents):**

| Specialist | Tools |
|------------|-------|
| Jira | get_ticket, search_tickets, update_ticket, get_sprint_stats |
| Git/CI | get_repo_health, get_pr_status, trigger_build, get_build_status |
| Slack | send_notification, open_modal, send_dm |
| Reporting | generate_report, analyze_release, publish_report |
| Hygiene | run_hygiene_check, get_hygiene_report, get_rules |
| RCA | analyze_failure, get_rca_history |
| Analytics | get_dora_metrics, get_kpis, get_trends, get_predictions |
| Webhooks | subscribe, unsubscribe, send_event |
| Scheduling | schedule_check, list_schedules, cancel_schedule |

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/specialists` | GET | List all specialists with health |
| `/specialists/{id}` | GET | Get specialist details |
| `/specialists/{id}/health` | POST | Trigger health check |
| `/specialists/tools/all` | GET | List all available tools |

---

### Dynamic Configuration (ConfigManager)

Redis-backed configuration management with real-time propagation.

```mermaid
flowchart LR
    subgraph Sources["Configuration Sources"]
        Env[Environment Variables]
        Redis[(Redis)]
        AdminUI[Admin Dashboard]
    end
    
    subgraph ConfigMgr["ConfigManager"]
        Cache[Local Cache<br/>TTL: 60s]
        Resolver[Priority Resolver]
    end
    
    subgraph Agents["All Agents"]
        Agent1[Agent 1]
        Agent2[Agent 2]
        AgentN[Agent N]
    end
    
    Sources --> ConfigMgr
    ConfigMgr --> Agents
    AdminUI -->|Real-time| Redis
    Redis -->|Propagate| ConfigMgr
```

**Features:**
- **Priority Resolution**: Redis > Environment > Default
- **Caching**: 60-second TTL for performance
- **Mode Switching**: Instant mock/live toggle across all agents
- **Sensitive Masking**: Auto-mask API keys and tokens
- **Templates**: Pre-built configurations for integrations

**Usage:**
```python
from nexus_lib import ConfigManager

config = ConfigManager()

# Check mode
if config.is_mock_mode():
    return mock_data()

# Get config with fallback
jira_url = config.get("JIRA_URL", default="https://jira.example.com")

# Set config (propagates to all agents)
await config.set("SYSTEM_MODE", "live")
```

---

## Observability

### Grafana Dashboard

The Nexus Grafana dashboard provides real-time visibility into system health, LLM economics, and release metrics.

![Grafana Dashboard](assets/mockups/grafana-dashboard.svg)

**Dashboard Panels:**
- **LLM Token Usage**: Track Gemini and OpenAI consumption
- **LLM Cost**: Monitor daily and per-query costs
- **Hygiene Score**: Project compliance percentage with trend
- **Release Decisions**: GO/CONDITIONAL/NO-GO breakdown
- **Agent Response Times**: P95 latency per agent
- **ReAct Loop Analytics**: Iterations, duration, success rate

### Metrics (Prometheus)

Key metrics exported by all services:

```
# LLM Usage
nexus_llm_tokens_total{model_name, type}
nexus_llm_latency_seconds{model_name}
nexus_llm_cost_dollars_total{model_name}

# Tool Usage
nexus_tool_usage_total{tool_name, status}
nexus_tool_latency_seconds{tool_name}

# ReAct Loop
nexus_react_iterations_count{task_type}
nexus_react_loop_duration_seconds{task_type}

# Hygiene (NEW)
nexus_project_hygiene_score{project_key}
nexus_hygiene_checks_total{project_key, trigger_type}
nexus_hygiene_violations_total{project_key, violation_type}

# Business
nexus_release_decisions_total{decision}
nexus_reports_generated_total{type}
nexus_jira_tickets_processed_total{action}
```

### Tracing (OpenTelemetry)

Distributed tracing across all services using OpenTelemetry with Jaeger export.

**Trace Context:**
- Request ID propagation
- Span correlation across agents
- LLM call tracing
- Tool execution timing

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2025-11-30T10:30:00Z",
  "level": "INFO",
  "service": "jira-hygiene-agent",
  "request_id": "req-abc123",
  "message": "Hygiene check completed",
  "hygiene_score": 85.0,
  "tickets_checked": 45,
  "violations_found": 7
}
```

---

## Security

### Authentication

- **JWT Tokens**: Service-to-service authentication
- **Slack Verification**: Request signing for Slack events
- **API Keys**: External service authentication

### Authorization

- Role-based access (Slack user roles)
- Agent-level permissions
- Audit logging

### Secrets Management

- Environment variables for development
- Kubernetes Secrets for production
- Integration with external vaults (HashiCorp Vault)

---

## Deployment Architecture

### Development (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Docker Network                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│ Orchestrator│  Jira Agent │ Git/CI Agent│Report Agent │   Slack Agent   │
│   :8080     │    :8081    │    :8082    │   :8083     │      :8084      │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤
│   Hygiene   │  RCA Agent  │  Analytics  │  Webhooks   │ Admin Dashboard │
│   :8085     │    :8006    │    :8086    │   :8087     │      :8088      │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┤
│                       Observability Stack                                │
├─────────────┬─────────────┬─────────────┬──────────────────────────────┤
│  Prometheus │   Grafana   │   Jaeger    │                              │
│    :9090    │    :3000    │   :16686    │                              │
├─────────────┴─────────────┴─────────────┴──────────────────────────────┤
│                          Data Layer                                      │
├─────────────┬─────────────┬─────────────────────────────────────────────┤
│  PostgreSQL │    Redis    │                                              │
│    :5432    │    :6379    │   (ConfigManager, Cache, Sessions)          │
└─────────────┴─────────────┴─────────────────────────────────────────────┘
```

### Production (Kubernetes)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ingress (NGINX)                                  │
├──────────────┬───────────────┬───────────────┬──────────────────────────┤
│    /api/*    │   /slack/*    │   /admin/*    │     Static Assets        │
├──────────────┴───────────────┴───────────────┴──────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌────────────────────────────────────────────┐ │
│  │   Orchestrator   │    │           Specialist Agents                │ │
│  │   (2+ replicas)  │────│  - Jira Agent        - Analytics           │ │
│  │        HPA       │    │  - Git/CI Agent      - Webhooks            │ │
│  │ SpecialistRegist │    │  - Reporting Agent   - Scheduling          │ │
│  └──────────────────┘    │  - Slack Agent       - RCA Agent           │ │
│           │              │  - Jira Hygiene Agent                      │ │
│           │              └────────────────────────────────────────────┘ │
│           │                                                              │
│  ┌──────────────────┐    ┌────────────────────────────────────────────┐ │
│  │ Admin Dashboard  │    │         Frontend (Vercel CDN)             │ │
│  │    Backend API   │    │  nexus-admin.vercel.app                    │ │
│  │      :8088       │    │  - React + Vite                            │ │
│  └──────────────────┘    │  - Auto-deploy on push                     │ │
│           │              └────────────────────────────────────────────┘ │
│           │                                                              │
│  ┌──────────────────┐    ┌────────────────────────────────────────────┐ │
│  │    PostgreSQL    │    │       Redis (ConfigManager/Cache)          │ │
│  │    (pgvector)    │    │                                            │ │
│  └──────────────────┘    └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Frontend Deployment (Vercel)

The Admin Dashboard frontend can be deployed to Vercel for production:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Vercel Edge Network                              │
├─────────────────────────────────────────────────────────────────────────┤
│  nexus-admin.vercel.app                                                  │
│  ├── Preview Deployments (PR-based)                                      │
│  ├── Production (main branch)                                            │
│  └── Staging (develop branch)                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Features:                                                               │
│  - Automatic HTTPS & CDN                                                 │
│  - Zero-config deployments                                               │
│  - Preview URLs for every PR                                             │
│  - Environment variable management                                       │
│  - Rollback support                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| Orchestrator | 8080 | Central coordination with Specialist Registry |
| Jira Agent | 8081 | Jira operations |
| Git/CI Agent | 8082 | GitHub + Jenkins |
| Reporting Agent | 8083 | Report generation |
| Slack Agent | 8084 | Slack interface |
| Jira Hygiene Agent | 8085 | Proactive quality checks |
| RCA Agent | 8006 | Root cause analysis |
| Analytics Service | 8086 | DORA metrics & KPIs |
| Webhooks Service | 8087 | Event distribution |
| **Admin Dashboard** | **8088** | **Web-based management UI** |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & ConfigManager |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |
| Jaeger | 16686 | Tracing UI |

---

## Design Decisions

### Why ReAct over Simple Chains?

1. **Flexibility**: Can handle unexpected scenarios
2. **Transparency**: Shows reasoning for decisions
3. **Self-correction**: Can recover from tool failures
4. **Extensibility**: Easy to add new tools

### Why Separate Agents?

1. **Scalability**: Scale agents independently
2. **Fault Isolation**: Failures don't cascade
3. **Technology Flexibility**: Each agent can use optimal libraries
4. **Team Ownership**: Clear boundaries for teams

### Why Vector Memory?

1. **Context Retention**: Learn from past interactions
2. **Semantic Search**: Find relevant historical data
3. **RAG Enhancement**: Better LLM responses with context

### Why Proactive Hygiene Agent?

1. **Data Quality**: Ensures Jira data is complete for accurate assessments
2. **Shift Left**: Catches issues before release readiness checks
3. **User Experience**: Interactive fixes reduce friction
4. **Automation**: Scheduled checks remove manual effort

---

## LLM Integration Layer

Nexus provides a production-ready LLM abstraction layer supporting multiple providers.

### Supported Providers

| Provider | Models | Features |
|----------|--------|----------|
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | Streaming, function calling, 1M context |
| **OpenAI** | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | Streaming, function calling |
| **Mock** | - | Development/testing without API costs |

### LLM Client Architecture

```mermaid
flowchart TB
    subgraph Factory["LLM Factory"]
        Config[LLMConfig]
        Create[create_llm_client]
    end
    
    subgraph Clients["LLM Clients"]
        Gemini[GeminiClient]
        OpenAI[OpenAIClient]
        Mock[MockClient]
    end
    
    subgraph Features["Features"]
        Gen[generate]
        Chat[chat]
        Stream[stream]
        Embed[embed]
    end
    
    Config --> Create
    Create --> Gemini
    Create --> OpenAI
    Create --> Mock
    
    Gemini --> Features
    OpenAI --> Features
    Mock --> Features
```

### Configuration

```python
from nexus_lib.llm import create_llm_client, LLMConfig

# From environment (recommended)
client = create_llm_client()  # Uses LLM_PROVIDER, LLM_MODEL, LLM_API_KEY

# Explicit configuration
config = LLMConfig(
    provider="google",
    model="gemini-2.0-flash",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=4096,
)
client = create_llm_client(**config.dict())
```

### Usage Example

```python
# Simple generation
response = await client.generate(
    prompt="Is the v2.0 release ready?",
    system_prompt="You are a release automation assistant."
)
print(response.content)
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost_estimate:.4f}")

# Streaming
async for chunk in client.stream("Summarize the release status"):
    print(chunk, end="")
```

---

## Multi-Tenancy Architecture

Nexus supports multi-tenant deployments for enterprise use cases.

### Tenant Isolation Model

```mermaid
flowchart TB
    subgraph Request["Incoming Request"]
        Headers[X-Tenant-ID / X-Tenant-Slug]
        Subdomain[tenant.nexus.example.com]
        APIKey[Authorization: Bearer key]
    end
    
    subgraph Middleware["Tenant Middleware"]
        Resolve[Tenant Resolution]
        Validate[Status Validation]
        Context[Set Context]
    end
    
    subgraph Tenant["Tenant Context"]
        Config[Tenant Config]
        Limits[Resource Limits]
        Features[Feature Flags]
    end
    
    subgraph Services["Isolated Services"]
        Jira[Jira Settings]
        Slack[Slack Settings]
        LLM[LLM Settings]
    end
    
    Request --> Middleware
    Middleware --> Tenant
    Tenant --> Services
```

### Tenant Plans

| Plan | API Requests | LLM Tokens/Day | Users | Projects |
|------|--------------|----------------|-------|----------|
| **Free** | 500/day | 50K | 3 | 2 |
| **Starter** | 2,000/day | 200K | 10 | 5 |
| **Professional** | 10,000/day | 1M | 50 | 20 |
| **Enterprise** | 100,000/day | 10M | 500 | 100 |

### Tenant Resolution Strategies

1. **Header**: `X-Tenant-ID` or `X-Tenant-Slug`
2. **Subdomain**: `acme.nexus.example.com`
3. **Path Prefix**: `/t/acme/api/...`
4. **API Key**: Tenant association via Bearer token

### Configuration Isolation

Each tenant has isolated configuration for:

```python
class TenantConfig:
    # Jira settings
    jira_url: str
    jira_api_token: str
    jira_projects: List[str]
    
    # GitHub settings
    github_token: str
    github_org: str
    
    # Slack settings
    slack_bot_token: str
    slack_workspace_id: str
    
    # LLM settings (optional per-tenant override)
    llm_api_key: Optional[str]
    
    # Feature flags
    features: Dict[str, bool] = {
        "react_engine": True,
        "hygiene_agent": True,
        "ai_recommendations": True,
    }
```

---

## AI Recommendations Engine

The recommendation engine analyzes patterns to provide intelligent suggestions.

### Recommendation Flow

```mermaid
flowchart LR
    subgraph Data["Data Sources"]
        Releases[Release History]
        Hygiene[Hygiene Scores]
        Velocity[Sprint Velocity]
        Risks[Risk Factors]
    end
    
    subgraph Analyzers["Pattern Analyzers"]
        RelAnalyzer[Release Analyzer]
        HygAnalyzer[Hygiene Analyzer]
        VelAnalyzer[Velocity Analyzer]
        RiskAnalyzer[Risk Analyzer]
    end
    
    subgraph Engine["Recommendation Engine"]
        Aggregate[Aggregate Findings]
        Prioritize[Prioritize]
        Format[Format Output]
    end
    
    Data --> Analyzers
    Analyzers --> Engine
    Engine --> Recommendations[Recommendations]
```

### Recommendation Types

| Type | Priority Levels | Example |
|------|-----------------|---------|
| `RELEASE_TIMING` | Medium | "Consider releasing Tuesday instead of Friday" |
| `HYGIENE_IMPROVEMENT` | High | "5 tickets missing Story Points" |
| `VELOCITY_OPTIMIZATION` | Medium | "Velocity dropped 30% - check blockers" |
| `RISK_MITIGATION` | Critical | "2 critical vulnerabilities blocking release" |
| `BLOCKERS_RESOLUTION` | Critical | "3 blocking issues need immediate attention" |
| `PROCESS_IMPROVEMENT` | Low | "Automate release readiness checks" |

### Analyzers

#### Release Pattern Analyzer
- Analyzes day-of-week success rates
- Identifies risky release windows
- Tracks failure patterns

#### Hygiene Pattern Analyzer
- Detects score trends (improving/declining)
- Identifies most common violations
- Tracks compliance over time

#### Velocity Analyzer
- Calculates predictability score
- Detects velocity drops
- Identifies capacity issues

#### Risk Analyzer
- Assesses blocker impact
- Evaluates security vulnerabilities
- Calculates overall risk score

---

## Slack App Home Dashboard

The App Home provides a rich dashboard when users open the Nexus app.

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Nexus Release Automation                                 │
│  Good morning! Here's your release management dashboard.     │
│  📅 Sunday, November 30, 2025 | Last updated: 9:30 AM       │
├─────────────────────────────────────────────────────────────┤
│  ⚡ Quick Actions                                            │
│  [📊 Release Status] [🔧 Hygiene Check] [📝 Report] [❓ Help] │
├─────────────────────────────────────────────────────────────┤
│  📈 Release Status Overview                                  │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ Version      │ Decision     │ Completion   │             │
│  │ v2.0.0       │ 🟡 CONDITIONAL│ 87%         │             │
│  ├──────────────┼──────────────┼──────────────┤             │
│  │ Build Status │ Security     │ Blockers     │             │
│  │ ✅ Passing   │ 75/100       │ 2            │             │
│  └──────────────┴──────────────┴──────────────┘             │
├─────────────────────────────────────────────────────────────┤
│  🔧 Jira Hygiene                          [View Details]     │
│  🟡 78% - Good                                               │
│  ████████░░ 78%                                              │
│  ⚠️ You have 3 ticket(s) needing attention    [Fix Now]     │
├─────────────────────────────────────────────────────────────┤
│  📋 Recent Activity                                          │
│  ✅ Release readiness check completed (2h ago)               │
│  🔧 Fixed 2 hygiene violations (5h ago)                      │
│  📝 Generated v1.9 release report (1d ago)                   │
├─────────────────────────────────────────────────────────────┤
│  💡 AI Recommendations                       [View All]      │
│  🟠 Address blocking issues before release                   │
│  🟡 Improve hygiene score to 90%+                           │
│  🟢 Consider releasing mid-week                              │
├─────────────────────────────────────────────────────────────┤
│  🤖 Powered by Nexus | /nexus help for commands              │
└─────────────────────────────────────────────────────────────┘
```

### Event Handling

The App Home responds to:
- `app_home_opened` - Rebuilds and publishes the view
- Button actions - Quick actions, fix hygiene, view details

### Why App Home?

1. **At-a-Glance Status**: See release health without commands
2. **Reduced Friction**: One-click actions
3. **Personalization**: User-specific hygiene issues
4. **Discoverability**: Surfaces AI recommendations proactively

---

## Testing Architecture

Nexus employs a comprehensive multi-layered testing strategy with **1,449 tests** ensuring reliability across all components.

### Test Pyramid

```mermaid
flowchart TB
    subgraph Tests["Test Layers (1,449 total)"]
        direction TB
        Unit["🧪 Unit Tests<br/>875 tests<br/>Isolated component testing"]
        E2E["🔄 E2E Tests<br/>410 tests<br/>Service endpoint testing"]
        Integration["🔗 Integration Tests<br/>60 tests<br/>Inter-service workflows"]
        Smoke["💨 Smoke Tests<br/>72 tests<br/>Health verification"]
        Performance["⚡ Performance Tests<br/>32 tests<br/>Load & latency"]
    end
    
    Unit --> E2E
    E2E --> Integration
    Integration --> Smoke
    Smoke --> Performance
```

### Test Coverage by Component

| Component | Unit | E2E | Total | Coverage |
|-----------|------|-----|-------|----------|
| **Orchestrator** | 30 | 72 | 102 | 100% |
| **Jira Agent** | 100 | 26 | 126 | 100% |
| **Git/CI Agent** | 94 | 24 | 118 | 100% |
| **Slack Agent** | 106 | 50 | 156 | 100% |
| **Admin Dashboard** | - | 110 | 110 | 100% |
| **Shared Library** | 94 | - | 94 | 100% |
| **Hygiene Agent** | 40 | 20 | 60 | 80% |
| **RCA Agent** | 30 | 24 | 54 | 80% |
| **Analytics** | 42 | - | 42 | 84% |
| **Webhooks** | 34 | - | 34 | 68% |

### Test Infrastructure

```mermaid
flowchart LR
    subgraph CI["GitHub Actions CI"]
        Lint[Lint & Format]
        Security[Security Scan]
        UnitJob[Unit Tests<br/>Python 3.10/3.11/3.12]
        IntJob[Integration Tests]
        E2EJob[E2E Tests]
        SmokeJob[Smoke Tests]
        Coverage[Codecov Upload]
    end
    
    subgraph Reports["Test Reports"]
        HTML[HTML Report]
        XML[JUnit XML]
        CovReport[Coverage Report]
    end
    
    Lint --> Security
    Security --> UnitJob
    UnitJob --> IntJob
    IntJob --> E2EJob
    E2EJob --> SmokeJob
    SmokeJob --> Coverage
    
    UnitJob --> Reports
    E2EJob --> Reports
    Coverage --> CovReport
```

### Test Categories

| Category | Purpose | Speed | When to Run |
|----------|---------|-------|-------------|
| **Unit** | Isolated component testing | ⚡ Fast | Every commit |
| **E2E** | Service endpoint testing | 🚀 Medium | Every PR |
| **Integration** | Inter-service workflows | 🔗 Medium | Pre-merge |
| **Smoke** | Health verification | 💨 Fast | Post-deploy |
| **Performance** | Load & latency testing | ⏱️ Slow | Release |

### Key Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/test_jira_agent.py` | 100 | JiraClient, parsing, operations |
| `tests/unit/test_slack_agent.py` | 106 | SlackClient, BlockKitBuilder, modals |
| `tests/unit/test_git_ci_agent.py` | 94 | GitHub, Jenkins, Security clients |
| `tests/unit/test_shared_lib.py` | 94 | Schemas, LLM, ConfigManager |
| `tests/unit/test_error_handling.py` | 40 | Error scenarios, edge cases |
| `tests/e2e/test_admin_dashboard.py` | 110 | Dashboard, releases, metrics |
| `tests/e2e/test_orchestrator.py` | 72 | Queries, specialists, memory |
| `tests/e2e/test_slack_agent.py` | 50 | Commands, events, interactions |
| `tests/integration/test_full_workflows.py` | 36 | Complete workflow chains |
| `tests/smoke/test_comprehensive_smoke.py` | 47 | Full system verification |
| `tests/performance/test_load.py` | 32 | Load testing, latency |

### Running Tests

```bash
# All tests
pytest

# By category
pytest -m unit           # 875 tests
pytest -m e2e            # 410 tests
pytest -m integration    # 60 tests
pytest -m smoke          # 72 tests
pytest -m performance    # 32 tests

# With coverage
pytest --cov=shared --cov=services --cov-report=html

# Generate report
python scripts/generate_test_report.py
```

📖 **[Full Testing Documentation](testing.md)**

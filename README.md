# 🚀 Nexus Release Automation System

<div align="center">

<img src="docs/assets/mockups/nexus-logo.svg" alt="Nexus Logo" width="200" onerror="this.style.display='none'"/>

### **Enterprise AI Platform for Automated Release Readiness Assessments**

[![Version](https://img.shields.io/badge/version-3.0.0-blue?style=for-the-badge)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10+-green?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge)](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/actions)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-FF6F00?style=for-the-badge&logo=langchain)](https://langchain.com/langgraph)
[![MCP](https://img.shields.io/badge/MCP-Tool%20Mesh-8B5CF6?style=for-the-badge)](https://modelcontextprotocol.io)
[![LLM](https://img.shields.io/badge/LLM-Multi--Provider-4285F4?style=for-the-badge&logo=openai)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/k8s-helm-326CE5?style=for-the-badge&logo=kubernetes)](https://kubernetes.io)

*Transform your release process with AI-powered automation, LangGraph orchestration, and the Model Context Protocol.*

[📚 Documentation](docs/index.md) • [🚀 Quick Start](#-quick-start) • [💬 Slack Commands](#-slack-integration) • [📊 Demo](demo/feature_walkthrough_script.md)

---

</div>

## 🎯 What is Nexus?

**Nexus** is an enterprise-grade, AI-powered release automation platform that revolutionizes how teams manage software releases. Built on **LangGraph** for stateful orchestration and the **Model Context Protocol (MCP)** for standardized tool connectivity, Nexus coordinates specialized agents to deliver intelligent **Go/No-Go release decisions** through natural language conversations.

> **"Is v2.0 ready for release?"** — Ask Nexus in plain English, and get a comprehensive analysis of your Jira tickets, CI/CD pipelines, security scans, and code quality metrics in seconds.

### 🌟 What's New in v3.0

| Feature | Description |
|---------|-------------|
| **🧠 LangGraph Engine** | Stateful orchestration with PostgreSQL persistence, replacing custom ReAct loops |
| **🔌 MCP Tool Mesh** | Standardized tool protocol for seamless agent connectivity over SSE |
| **🏭 LLM Factory** | Multi-provider support: OpenAI, Google Gemini, Ollama, Azure OpenAI |
| **🎛️ Admin Dashboard** | React UI for managing LLM configuration and MCP server endpoints |
| **🔍 Enhanced RCA** | AI-powered root cause analysis with auto-triggered Jenkins webhooks |
| **📊 Jira Hygiene** | Proactive data quality checks with interactive Slack modals |

### 🌟 Why Choose Nexus?

| Challenge | Traditional Approach | Nexus Solution |
|-----------|---------------------|----------------|
| **Release Readiness** | Manual spreadsheets, meetings | AI-powered instant assessment |
| **Data Collection** | Hours gathering from multiple tools | Automatic aggregation in seconds |
| **Build Failures** | Manual log analysis | Smart RCA with fix suggestions |
| **Jira Hygiene** | Periodic manual audits | Proactive daily checks with auto-fix |
| **Stakeholder Updates** | Email chains, status meetings | Real-time Slack notifications |
| **Decision Making** | Gut feeling, incomplete data | Data-driven Go/No-Go with confidence scores |
| **Tool Integration** | Custom REST APIs, maintenance burden | Standardized MCP protocol |
| **LLM Lock-in** | Single provider dependency | Multi-provider LLM Factory |

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧠 **LangGraph Orchestration**
- **StateGraph**: Durable workflows with plan → act → review nodes
- **PostgreSQL Persistence**: Resume conversations across restarts
- **Human-in-the-Loop**: Approval workflows for sensitive actions
- **Streaming**: Real-time progress updates via SSE

</td>
<td width="50%">

### 🔌 **MCP Tool Mesh**
- **Standardized Protocol**: All agents expose tools via MCP
- **SSE Transport**: Efficient streaming over HTTP
- **Tool Aggregation**: Single interface to all connected servers
- **Graceful Degradation**: Offline servers don't break the graph

</td>
</tr>
<tr>
<td width="50%">

### 🏭 **LLM Factory**
- **OpenAI**: GPT-4o, GPT-4-turbo
- **Google Gemini**: 2.0 Flash, 1.5 Pro
- **Ollama**: Local models (Llama 3, Mistral)
- **Azure OpenAI**: Enterprise deployments
- **Runtime Switching**: Change providers via Admin UI

</td>
<td width="50%">

### 🎛️ **Admin Dashboard**
- **React + FastAPI**: Modern single-page application
- **Redis Configuration**: Dynamic settings without restarts
- **MCP Server Management**: Add/remove tool servers
- **Live Mode Toggle**: Instant Mock/Production switching

</td>
</tr>
<tr>
<td width="50%">

### 📊 **Advanced Analytics**
- **DORA Metrics**: Deployment frequency, lead time, MTTR
- **Predictive Analytics**: ML-powered release date predictions
- **Anomaly Detection**: Automatic identification of unusual patterns
- **Team Performance**: Velocity and quality comparisons

</td>
<td width="50%">

### 💬 **Slack-First Experience**
- **Natural Language**: Ask questions in plain English
- **App Home Dashboard**: Rich widgets with quick actions
- **Interactive Modals**: Fix Jira tickets directly from Slack
- **Proactive Notifications**: RCA results, hygiene alerts

</td>
</tr>
</table>

---

## 🏗️ Architecture Overview

Nexus v3.0 uses a **LangGraph + MCP Mesh** architecture where the Central Orchestrator coordinates specialized agents via the Model Context Protocol:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │  Slack App      │  │  Admin Dashboard│  │  REST API                       │  │
│  │  - Commands     │  │  - LLM Config   │  │  - /query                       │  │
│  │  - App Home     │  │  - MCP Servers  │  │  - /execute                     │  │
│  │  - Modals       │  │  - Health       │  │  - /approve                     │  │
│  └────────┬────────┘  └────────┬────────┘  └────────────────┬────────────────┘  │
└───────────┼─────────────────────┼───────────────────────────┼───────────────────┘
            │                     │                           │
            └─────────────────────┼───────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     CENTRAL ORCHESTRATOR (LangGraph)                            │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         StateGraph Engine                                  │  │
│  │  ┌─────────┐    ┌─────────┐    ┌───────────────┐    ┌─────────────────┐   │  │
│  │  │  Plan   │ -> │   Act   │ -> │ Human Review  │ -> │    Respond      │   │  │
│  │  │  Node   │    │  Node   │    │    Node       │    │    Node         │   │  │
│  │  └─────────┘    └─────────┘    └───────────────┘    └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │ LLM Factory │  │ MCP Client   │  │ PostgreSQL     │  │ Vector Memory    │  │
│  │ (Multi-LLM) │  │   Manager    │  │ Checkpoints    │  │ (RAG)            │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                         MCP Protocol (SSE)
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
┌─────────────┐ ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐
│ Jira MCP    │ │ Git/CI    │ │ Reporting   │ │ Hygiene   │ │ RCA MCP     │
│ Server      │ │ MCP Server│ │ MCP Server  │ │ MCP Server│ │ Server      │
│             │ │           │ │             │ │           │ │             │
│ @tool:      │ │ @tool:    │ │ @tool:      │ │ @tool:    │ │ @tool:      │
│ get_issue   │ │ get_pr    │ │ generate    │ │ check_    │ │ analyze_    │
│ search      │ │ trigger   │ │ publish     │ │ hygiene   │ │ build       │
│ update      │ │ get_build │ │ analyze     │ │           │ │             │
└──────┬──────┘ └─────┬─────┘ └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
┌─────────────┐ ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐
│    Jira     │ │  GitHub   │ │ Confluence  │ │   Slack   │ │  Jenkins    │
│    Cloud    │ │  Jenkins  │ │             │ │           │ │             │
└─────────────┘ └───────────┘ └─────────────┘ └───────────┘ └─────────────┘

                        INFRASTRUCTURE LAYER
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│  │   Redis     │  │ PostgreSQL  │  │ Prometheus  │  │    Grafana          │    │
│  │  - Config   │  │  - State    │  │  - Metrics  │  │  - Dashboards       │    │
│  │  - Cache    │  │  - Vectors  │  │             │  │                     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Highlights

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestrator** | LangGraph StateGraph | Stateful workflow orchestration |
| **Tool Protocol** | MCP over SSE | Standardized agent connectivity |
| **LLM Layer** | LLM Factory Pattern | Multi-provider model support |
| **State Store** | PostgreSQL + pgvector | Checkpoints + RAG embeddings |
| **Config Store** | Redis | Dynamic configuration |
| **Observability** | OpenTelemetry + Prometheus | Metrics and tracing |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Local orchestration |
| Node.js | 18+ | MCP sidecar servers (optional) |
| Git | 2.0+ | Source control |

### Option 1: One-Click Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# Run automated setup
./scripts/setup.sh
```

The setup script automatically:
- ✅ Validates all prerequisites
- ✅ Creates Python virtual environment
- ✅ Installs dependencies (including LangGraph, MCP SDK)
- ✅ Configures environment variables
- ✅ Starts Redis and PostgreSQL
- ✅ Builds and starts all MCP servers
- ✅ Runs health verification

**Setup Options:**
```bash
./scripts/setup.sh --help           # Show all options
./scripts/setup.sh --dev            # Include dev tools
./scripts/setup.sh --with-ollama    # Include local Ollama LLM
./scripts/setup.sh --with-observability  # Include Prometheus/Grafana
./scripts/setup.sh --clean          # Fresh install
```

### Option 2: Docker Compose

```bash
# Clone and start core services
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot
docker-compose up -d

# Start with observability stack
docker-compose --profile observability up -d

# Start with local LLM (Ollama)
docker-compose --profile local-llm up -d

# Verify
docker-compose ps
curl http://localhost:8080/health
```

### Option 3: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install shared library
pip install -e shared/

# Install LangGraph and MCP dependencies
pip install langgraph langchain-core mcp sse-starlette

# Install service dependencies
pip install -r services/orchestrator/requirements.txt

# Start Redis and PostgreSQL
docker-compose up -d redis postgres

# Start the orchestrator
cd services/orchestrator
uvicorn main:app --reload --port 8080
```

---

## 🖥️ Service Endpoints

Once running, access these services:

| Service | URL | Description |
|---------|-----|-------------|
| **Orchestrator API** | http://localhost:8080/docs | LangGraph brain, /execute endpoint |
| **Admin Dashboard** | http://localhost:3001 | LLM & MCP configuration UI |
| **Jira MCP Server** | http://localhost:8081/mcp/tools | Jira tool definitions |
| **Git/CI MCP Server** | http://localhost:8082/mcp/tools | GitHub + Jenkins tools |
| **Reporting MCP Server** | http://localhost:8083/mcp/tools | Confluence publishing |
| **Hygiene MCP Server** | http://localhost:8005/mcp/tools | Data quality checks |
| **RCA MCP Server** | http://localhost:8006/mcp/tools | Build failure analysis |
| **Grafana** | http://localhost:3000 | Dashboards (admin/nexus_admin) |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Jaeger** | http://localhost:16686 | Distributed tracing |

### Try Your First Query

```bash
# Simple query
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is the v2.0 release ready?"}'

# With thread persistence (for follow-up questions)
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the open blockers?", "thread_id": "my-session-123"}'

# Check thread state
curl http://localhost:8080/thread/my-session-123
```

### List Available MCP Tools

```bash
# Get all connected tools
curl http://localhost:8080/mcp/tools
```

---

## 🔌 MCP Server Architecture

Nexus agents expose their capabilities via the Model Context Protocol:

### Custom Python MCP Servers

| Server | Port | Tools |
|--------|------|-------|
| **jira_agent** | 8081 | `get_jira_issue`, `search_jira_issues`, `update_jira_issue_status`, `add_jira_comment`, `get_jira_sprint_stats` |
| **git_ci_agent** | 8082 | `get_repo_health`, `get_pr_status`, `list_open_prs`, `trigger_jenkins_build`, `get_jenkins_build_status`, `get_security_scan_results` |
| **reporting_agent** | 8083 | `generate_release_report_html`, `publish_confluence_report`, `analyze_release_readiness` |
| **jira_hygiene_agent** | 8005 | `check_project_hygiene` |
| **rca_agent** | 8006 | `analyze_build_failure` |

### Tool Definition Example

Each MCP server exposes tools with JSON Schema definitions:

```json
{
  "name": "get_jira_issue",
  "description": "Fetch a single Jira issue by its key.",
  "input_schema": {
    "type": "object",
    "properties": {
      "key": {"type": "string", "description": "The Jira ticket key (e.g., PROJ-123)."}
    },
    "required": ["key"]
  },
  "output_schema": {...}
}
```

---

## 🧠 LangGraph Workflow

The orchestrator uses a LangGraph StateGraph with the following nodes:

```
         ┌─────────────────┐
         │     START       │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │      PLAN       │ ← LLM creates execution plan
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         │                 │
    (has tools)      (no tools)
         │                 │
         ▼                 │
┌─────────────────┐        │
│      ACTION     │ ← Execute MCP tools
└────────┬────────┘        │
         │                 │
    ┌────┴────┐            │
    │         │            │
(more)    (done)           │
    │         │            │
    ▼         ▼            │
   LOOP   ┌─────────┐      │
          │ REVIEW  │ ← Human approval (if sensitive)
          └────┬────┘      │
               │           │
         ┌─────┴─────┐     │
         │           │     │
     (approved)  (rejected)│
         │           │     │
         ▼           ▼     │
         │     ┌─────────┐ │
         │     │  ERROR  │ │
         │     └─────────┘ │
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │     RESPOND     │ ← Generate final answer
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │       END       │
         └─────────────────┘
```

### State Persistence

LangGraph state is persisted to PostgreSQL, enabling:
- **Resume conversations**: Pick up where you left off
- **Audit trail**: Complete history of tool executions
- **Human-in-the-loop**: Pause for approval, resume later

---

## 🏭 LLM Factory Configuration

Configure your preferred LLM provider via the Admin Dashboard or environment variables:

### Supported Providers

| Provider | Models | Environment Variables |
|----------|--------|----------------------|
| **OpenAI** | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | `LLM_PROVIDER=openai`, `OPENAI_API_KEY` |
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | `LLM_PROVIDER=google`, `GOOGLE_API_KEY` |
| **Ollama** | llama3, mistral, codellama | `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL` |
| **Azure OpenAI** | Any Azure deployment | `LLM_PROVIDER=azure`, `AZURE_OPENAI_*` |
| **Mock** | (Development) | `LLM_PROVIDER=mock` |

### Runtime Configuration

Change providers without restart via Admin Dashboard or API:

```bash
# Set LLM provider via Admin API
curl -X POST http://localhost:3001/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "nexus:config:llm_provider",
    "value": "openai"
  }'

# Set API key
curl -X POST http://localhost:3001/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "nexus:config:openai_api_key",
    "value": "sk-..."
  }'
```

---

## 💬 Slack Integration

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/nexus status <version>` | Check release readiness | `/nexus status v2.0` |
| `/nexus ticket <key>` | Get ticket details | `/nexus ticket PROJ-123` |
| `/nexus blockers` | List all blockers | `/nexus blockers` |
| `/nexus report` | Generate release report | `/nexus report` |
| `/nexus rca <job> <build>` | Analyze build failure | `/nexus rca backend-ci 42` |
| `/nexus hygiene <project>` | Run hygiene check | `/nexus hygiene PROJ` |
| `/nexus help` | Show all commands | `/nexus help` |

### Interactive Notifications

Nexus sends proactive notifications:
- **Hygiene Violations**: DM with "Fix Now" button opening an interactive modal
- **RCA Results**: Channel message with root cause, suspected file, and fix suggestion
- **Release Updates**: Status changes and milestone completions

---

## 🎛️ Admin Dashboard

The Admin Dashboard provides a web-based interface for managing Nexus:

### Features

| Tab | Functionality |
|-----|---------------|
| **Dashboard** | System overview, MCP server health, quick actions |
| **LLM Config** | Select provider, set API keys, test connectivity |
| **MCP Servers** | View connected servers, available tools, health status |
| **Releases** | Track versions, target dates, import from external sources |
| **Observability** | Metrics, charts, LLM usage, integrated Grafana |

### Mode Switching

Toggle between **Mock Mode** (development) and **Live Mode** (production):

```bash
# Via API
curl -X POST http://localhost:3001/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "live"}'
```

---

## 🧪 Testing

Nexus has a comprehensive test suite:

| Category | Count | Purpose |
|----------|-------|---------|
| **Unit** | ~200 | Individual component testing |
| **E2E** | ~100 | Service endpoint testing |
| **Integration** | ~30 | Inter-service communication |
| **Smoke** | ~40 | Quick health verification |

### Running Tests

```bash
# All tests
pytest

# By category
pytest -m unit
pytest -m e2e

# LangGraph engine tests
pytest tests/unit/test_graph.py -v

# With coverage
pytest --cov=shared --cov=services --cov-report=html
```

---

## 📁 Project Structure

```
Nexus-Release-Readiness-Bot/
├── services/                        # Microservices
│   ├── orchestrator/                # LangGraph engine + MCP client
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── graph.py         # LangGraph StateGraph
│   │   │   │   ├── llm_factory.py   # Multi-provider LLM
│   │   │   │   ├── mcp_client.py    # MCP client manager
│   │   │   │   └── memory.py        # Vector + conversation memory
│   │   │   └── models/
│   │   └── main.py
│   ├── agents/
│   │   ├── jira_agent/              # MCP server for Jira
│   │   ├── git_ci_agent/            # MCP server for GitHub/Jenkins
│   │   ├── reporting_agent/         # MCP server for Confluence
│   │   ├── slack_agent/             # Slack interface
│   │   ├── jira_hygiene_agent/      # MCP server for data quality
│   │   └── rca_agent/               # MCP server for RCA
│   ├── admin_dashboard/             # React + FastAPI admin UI
│   └── analytics/                   # Advanced analytics
│
├── shared/nexus_lib/                # Shared library
│   ├── schemas/                     # Pydantic models
│   ├── llm/                         # LLM client base classes
│   ├── mcp.py                       # MCP server utilities
│   ├── config.py                    # ConfigManager (Redis + Env)
│   ├── middleware.py                # Auth, metrics
│   └── instrumentation.py           # OTEL, Prometheus
│
├── infrastructure/
│   ├── docker/                      # Dockerfiles
│   │   ├── init-db.sql              # PostgreSQL schema
│   │   └── prometheus.yml
│   ├── k8s/nexus-stack/             # Helm chart
│   └── grafana/                     # Dashboards
│
├── tests/
│   ├── unit/
│   │   ├── test_graph.py            # LangGraph tests
│   │   ├── test_rca_logic.py
│   │   └── test_hygiene_logic.py
│   ├── e2e/
│   └── integration/
│
└── docs/                            # Documentation
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment | development |
| `LLM_PROVIDER` | LLM provider | mock |
| `LLM_MODEL` | Model name | gpt-4 |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GOOGLE_API_KEY` | Google API key | - |
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `REDIS_URL` | Redis connection | redis://localhost:6379 |
| `DATABASE_URL` | PostgreSQL connection | postgresql://... |
| `MCP_JIRA_URL` | Jira MCP server | http://jira-agent:8081/mcp |
| `MEMORY_BACKEND` | Vector store | postgres |

---

## 🆕 Version History

### v3.0.0 - LangGraph + MCP Architecture (Current)
- 🧠 **LangGraph Engine** - Stateful orchestration replacing ReAct
- 🔌 **MCP Tool Mesh** - All agents as MCP servers
- 🏭 **LLM Factory** - Multi-provider support
- 📊 **PostgreSQL Persistence** - Durable state + pgvector

### v2.4.0 - Release Management
- 📅 Release tracking from Smartsheet/CSV

### v2.3.0 - Admin Dashboard
- 🎛️ Web UI for configuration
- 🔄 Dynamic Redis-backed settings

### v2.2.0 - Smart RCA
- 🔍 AI-powered build failure analysis
- 🔔 Auto-triggered Jenkins webhooks

📖 See [CHANGELOG.md](CHANGELOG.md) for complete history.

---

## 🗺️ Roadmap

### Completed ✅
- [x] LangGraph StateGraph engine
- [x] MCP server architecture for all agents
- [x] Multi-provider LLM Factory
- [x] PostgreSQL state persistence
- [x] Human-in-the-loop approval workflows
- [x] Smart Root Cause Analysis
- [x] Jira Hygiene with interactive fixes
- [x] Admin Dashboard with React UI

### In Progress 🚧
- [ ] MCP server discovery (dynamic registration)
- [ ] Anthropic Claude integration
- [ ] LangGraph Supervisor for multi-agent coordination

### Planned 📋
- [ ] LangGraph Studio integration
- [ ] GitLab MCP server
- [ ] Azure DevOps MCP server
- [ ] Custom LLM fine-tuning
- [ ] Mobile companion app

---

## 🤝 Contributing

We welcome contributions! See [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing`
3. Commit with conventional commits: `git commit -m 'feat: add amazing feature'`
4. Push and open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE).

---

<div align="center">

### Built with ❤️ by the Nexus Team

**Powered by LangGraph 🧠 + MCP 🔌**

[⭐ Star us on GitHub](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot) — it helps!

*Making release management intelligent, one decision at a time.*

</div>

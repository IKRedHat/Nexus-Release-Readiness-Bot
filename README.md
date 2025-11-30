# 🚀 Nexus Release Automation System

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.0-4285F4)

**Intelligent Multi-Agent System for Automated Release Readiness Assessments**

*Now with Google Gemini 2.0, AI Recommendations, Multi-Tenancy, and Slack App Home!*

[Documentation](docs/index.md) • [User Guide](docs/user_guide.md) • [Architecture](docs/architecture.md) • [Demo](demo/feature_walkthrough_script.md)

</div>

---

## 🎯 Overview

Nexus is an AI-powered release automation system that uses a **ReAct (Reasoning + Acting)** architecture to coordinate specialized agents. It connects to your existing tools—Jira, GitHub, Jenkins, and Confluence—to provide intelligent **Go/No-Go release decisions** through natural language interactions.

### ✨ Key Features

- 🤖 **Google Gemini Integration** - Production-ready LLM with streaming and function calling
- 🧠 **Intelligent Orchestration** - ReAct engine that reasons and acts with transparent traces
- 💡 **AI Recommendations** - Pattern-based intelligent suggestions for release optimization
- 🏠 **Slack App Home** - Rich dashboard with quick actions and real-time widgets
- 🏢 **Multi-Tenant Support** - Enterprise-ready organization isolation with plan tiers
- 🔗 **Multi-Tool Integration** - Jira, GitHub, Jenkins, Confluence, Slack
- 📊 **Rich Reports** - Beautiful HTML reports with Go/No-Go decisions
- 💬 **Natural Language** - Ask questions in plain English via Slack
- 🔧 **Proactive Hygiene** - Automated Jira data quality checks with interactive fixes
- 📈 **Full Observability** - Prometheus metrics, Grafana dashboards, OpenTelemetry tracing
- 🔐 **Production Ready** - JWT auth, Kubernetes deployment, Helm charts

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Slack Workspace                             │
│            (User: /nexus status v2.0 | App Home Dashboard)           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Slack Agent                                 │
│         (Commands, Modals, DMs, App Home, Notifications)             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────────────┐    ┌─────────────────────────────┐
│     Central Orchestrator        │    │  Jira Hygiene Agent         │
│  ┌───────────────────────────┐  │    │  ┌───────────────────────┐  │
│  │   ReAct Engine + Gemini   │  │    │  │  Scheduled Checks     │  │
│  │  Thought → Action → Obs   │  │    │  │  Field Validation     │  │
│  └───────────────────────────┘  │    │  │  Hygiene Scoring      │  │
│  ┌──────────┐ ┌───────────────┐ │    │  │  Interactive Modals   │  │
│  │ Memory   │ │ AI Recommend. │ │    │  └───────────────────────┘  │
│  │(ChromaDB)│ │    Engine     │ │    └─────────────────┬───────────┘
│  └──────────┘ └───────────────┘ │                      │
│  ┌──────────────────────────────┤                      │
│  │ Multi-Tenant Middleware     ││                      │
│  └─────────────────────────────┘│                      │
└───────┬─────────────────────────┘                      │
        │                                                │
  ┌─────┴────────────┬──────────────┐                   │
  ▼                  ▼              ▼                   │
┌─────────┐  ┌─────────────┐  ┌──────────┐             │
│  Jira   │◄─│   Git/CI    │  │Reporting │             │
│  Agent  │  │    Agent    │  │  Agent   │             │
└────┬────┘  └──────┬──────┘  └────┬─────┘             │
     │              │              │                    │
     ▼              ▼              ▼                    │
┌─────────┐  ┌───────────┐  ┌───────────┐              │
│  Jira   │  │  GitHub   │  │Confluence │              │
│  Cloud  │◄─│  Jenkins  │  │           │              │
└─────────┘  └───────────┘  └───────────┘              │
     ▲                                                  │
     └──────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- (Optional) Kubernetes for production

### 1. Clone and Start

```bash
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# Start with Docker Compose
docker-compose up -d
```

### 2. Verify Services

```bash
# Check orchestrator health
curl http://localhost:8080/health

# Check hygiene agent health
curl http://localhost:8005/health

# View all services
docker-compose ps
```

### 3. Try a Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is the v2.0 release ready?"}'
```

### 4. Run a Hygiene Check

```bash
curl -X POST http://localhost:8005/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": false}'
```

### 5. Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| Orchestrator API | http://localhost:8080/docs | - |
| Hygiene Agent API | http://localhost:8005/docs | - |
| Report Preview | http://localhost:8083/preview | - |
| Grafana | http://localhost:3000 | admin / nexus_admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |

---

## 🆕 What's New in v2.0

### 🤖 Google Gemini Integration
- Production-ready LLM client with Gemini 2.0 Flash
- Streaming, function calling, and embeddings support
- Automatic token usage and cost tracking
- Fallback to mock mode for development

### 💡 AI Recommendations Engine
- Pattern-based intelligent suggestions
- Release timing optimization
- Hygiene improvement recommendations
- Blocker and risk assessment

### 🏠 Slack App Home Dashboard
- Rich personalized dashboard on app open
- Quick action buttons for common tasks
- Real-time release status widget
- AI recommendations preview

### 🏢 Multi-Tenant Support
- Enterprise-ready organization isolation
- Plan tiers (Free, Starter, Professional, Enterprise)
- Per-tenant resource limits and configuration
- Feature flags per organization

---

## 💬 Slack Commands

Once configured with Slack:

```
/nexus status v2.0       # Check release readiness
/nexus ticket PROJ-123   # Get ticket details
/nexus blockers          # List all blockers
/jira-update             # Update ticket via modal
/nexus report            # Generate release report
/nexus help              # Show all commands
```

### 🔧 Jira Hygiene Notifications

Nexus proactively monitors Jira data quality:

1. **Scheduled Checks**: Weekdays at 9:00 AM
2. **DM Notifications**: Sent to assignees with violations
3. **Interactive Fixes**: Click "Fix Tickets Now" to open a modal
4. **Update Fields**: Labels, Fix Version, Story Points, Team - directly from Slack!

---

## 📁 Project Structure

```
Nexus-Release-Readiness-Bot/
├── services/
│   ├── orchestrator/              # Central brain (ReAct engine)
│   └── agents/
│       ├── jira_agent/            # Jira integration
│       ├── git_ci_agent/          # GitHub + Jenkins
│       ├── reporting_agent/       # Report generation
│       ├── slack_agent/           # Slack interface
│       └── jira_hygiene_agent/    # 🆕 Proactive quality checks
├── shared/
│   └── nexus_lib/                 # Shared library
│       ├── schemas/               # Pydantic models
│       ├── llm/                   # 🆕 LLM clients (Gemini, OpenAI)
│       ├── multitenancy/          # 🆕 Tenant isolation
│       ├── recommendations/       # 🆕 AI recommendations engine
│       ├── middleware.py          # JWT auth, metrics, tenant
│       ├── instrumentation.py     # OTEL, Prometheus
│       └── utils.py               # HTTP client, helpers
├── infrastructure/
│   ├── docker/                    # Dockerfiles
│   ├── k8s/nexus-stack/           # Helm chart
│   ├── grafana/                   # Dashboards
│   └── terraform/                 # Cloud infrastructure
├── docs/                          # MkDocs documentation
├── tests/                         # Unit & E2E tests
└── demo/                          # Demo scripts
```

---

## 🔌 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Orchestrator | 8080 | Central coordination |
| Jira Agent | 8081 | Jira operations |
| Git/CI Agent | 8082 | GitHub + Jenkins |
| Reporting Agent | 8083 | Report generation |
| Slack Agent | 8084 | Slack interface |
| **Jira Hygiene Agent** | **8005** | **Proactive quality checks** |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment (development/production) | development |
| `LLM_PROVIDER` | LLM provider (google/openai/mock) | mock |
| `LLM_MODEL` | Model name (gemini-2.0-flash, gpt-4o) | gemini-2.0-flash |
| `LLM_API_KEY` | API key for LLM | - |
| `LLM_TEMPERATURE` | Generation temperature | 0.7 |
| `MEMORY_BACKEND` | Vector store (chromadb/pgvector/mock) | mock |
| `MULTI_TENANT_ENABLED` | Enable multi-tenancy | false |
| `RECOMMENDATIONS_ENABLED` | Enable AI recommendations | true |
| `JIRA_MOCK_MODE` | Use mock Jira data | true |
| `GITHUB_MOCK_MODE` | Use mock GitHub data | true |
| `HYGIENE_SCHEDULE_HOUR` | Hour for hygiene checks (0-23) | 9 |
| `HYGIENE_SCHEDULE_DAYS` | Days for checks (mon-fri/daily) | mon-fri |

### Production Configuration

See [Deployment Runbook](docs/runbooks/deployment.md) for production setup.

---

## 📊 Observability

### Prometheus Metrics

```
# LLM Usage
nexus_llm_tokens_total{model_name, type}
nexus_llm_latency_seconds{model_name}
nexus_llm_cost_dollars_total{model_name}

# Agent Performance
nexus_tool_usage_total{tool_name, status}
http_request_duration_seconds{agent_type}

# ReAct Engine
nexus_react_iterations_count{task_type}

# Hygiene Metrics (NEW)
nexus_project_hygiene_score{project_key}
nexus_hygiene_checks_total{project_key, trigger_type}
nexus_hygiene_violations_total{project_key, violation_type}

# Business Metrics
nexus_release_decisions_total{decision}
```

### Grafana Dashboard

Import `infrastructure/grafana/dashboard.json` for:
- LLM economics (tokens, cost)
- Agent latency (P95/P99)
- ReAct loop analytics
- Hygiene score tracking
- Release decision tracking

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# E2E tests only
pytest tests/e2e/ -v

# Hygiene logic tests
pytest tests/unit/test_hygiene_logic.py -v

# With coverage
pytest tests/ --cov=shared --cov=services --cov-report=html
```

---

## 🚢 Kubernetes Deployment

```bash
# Add Helm dependencies
cd infrastructure/k8s/nexus-stack
helm dependency update

# Deploy
helm upgrade --install nexus . \
  --namespace nexus \
  --create-namespace \
  --values production-values.yaml
```

---

## 🗺️ Roadmap

- [x] Core ReAct Engine
- [x] Jira, GitHub, Jenkins integrations
- [x] Confluence report publishing
- [x] Slack Block Kit interface
- [x] Prometheus/Grafana observability
- [x] Kubernetes Helm charts
- [x] **Jira Hygiene Agent with interactive fixes**
- [x] **Google Gemini live integration** ✨ NEW
- [x] **Multi-tenant support** ✨ NEW
- [x] **AI-powered recommendations** ✨ NEW
- [x] **Slack App Home dashboard** ✨ NEW
- [ ] Anthropic Claude integration
- [ ] Advanced analytics dashboard
- [ ] Webhook integrations for external systems

---

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

---

<div align="center">

**Built with ❤️ by the Nexus Team**

[⬆ Back to top](#-nexus-release-automation-system)

</div>

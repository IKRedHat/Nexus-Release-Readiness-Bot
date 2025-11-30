# 🚀 Nexus Release Automation System

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

**Intelligent Multi-Agent System for Automated Release Readiness Assessments**

[Documentation](docs/index.md) • [User Guide](docs/user_guide.md) • [Architecture](docs/architecture.md) • [Demo](demo/feature_walkthrough_script.md)

</div>

---

## 🎯 Overview

Nexus is an AI-powered release automation system that uses a **ReAct (Reasoning + Acting)** architecture to coordinate specialized agents. It connects to your existing tools—Jira, GitHub, Jenkins, and Confluence—to provide intelligent **Go/No-Go release decisions** through natural language interactions.

### ✨ Key Features

- 🧠 **Intelligent Orchestration** - LLM-powered ReAct engine that reasons and acts
- 🔗 **Multi-Tool Integration** - Jira, GitHub, Jenkins, Confluence, Slack
- 📊 **Rich Reports** - Beautiful HTML reports with Go/No-Go decisions
- 💬 **Natural Language** - Ask questions in plain English via Slack
- 📈 **Full Observability** - Prometheus metrics, Grafana dashboards, OpenTelemetry tracing
- 🔐 **Production Ready** - JWT auth, Kubernetes deployment, Helm charts

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Slack Workspace                          │
│                    (User: /nexus status v2.0)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Slack Agent                               │
│                  (Commands, Modals, Notifications)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Central Orchestrator                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ReAct Engine                          │    │
│  │  Thought → Action → Observation → Thought → Final Answer │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Vector Memory│  │  LLM Client  │  │   Agent Registry     │   │
│  │  (ChromaDB)  │  │(Gemini/GPT)  │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────┬──────────────┬───────────────────┬───────────────────┘
           │              │                   │
     ┌─────┴─────┐  ┌─────┴─────┐      ┌─────┴─────┐
     ▼           ▼  ▼           ▼      ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌──────────────┐
│  Jira   │ │ Git/CI  │ │  Reporting  │ │  Scheduling  │
│  Agent  │ │  Agent  │ │    Agent    │ │    Agent     │
└────┬────┘ └────┬────┘ └──────┬──────┘ └──────────────┘
     │           │             │
     ▼           ▼             ▼
┌─────────┐ ┌─────────┐ ┌───────────┐
│  Jira   │ │ GitHub  │ │Confluence │
│  Cloud  │ │ Jenkins │ │           │
└─────────┘ └─────────┘ └───────────┘
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
# Check health
curl http://localhost:8080/health

# View all services
docker-compose ps
```

### 3. Try a Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is the v2.0 release ready?"}'
```

### 4. Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| Orchestrator API | http://localhost:8080/docs | - |
| Report Preview | http://localhost:8083/preview | - |
| Grafana | http://localhost:3000 | admin / nexus_admin |
| Prometheus | http://localhost:9090 | - |
| Jaeger | http://localhost:16686 | - |

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

---

## 📁 Project Structure

```
Nexus-Release-Readiness-Bot/
├── services/
│   ├── orchestrator/          # Central brain (ReAct engine)
│   └── agents/
│       ├── jira_agent/        # Jira integration
│       ├── git_ci_agent/      # GitHub + Jenkins
│       ├── reporting_agent/   # Report generation
│       ├── slack_agent/       # Slack interface
│       └── scheduling_agent/  # Future: Cron jobs
├── shared/
│   └── nexus_lib/             # Shared library
│       ├── schemas/           # Pydantic models
│       ├── middleware.py      # JWT auth, metrics
│       ├── instrumentation.py # OTEL, Prometheus
│       └── utils.py           # HTTP client, helpers
├── infrastructure/
│   ├── docker/                # Dockerfiles
│   ├── k8s/nexus-stack/       # Helm chart
│   ├── grafana/               # Dashboards
│   └── terraform/             # Cloud infrastructure
├── docs/                      # MkDocs documentation
├── tests/                     # Unit & E2E tests
└── demo/                      # Demo scripts
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment (development/production) | development |
| `LLM_PROVIDER` | LLM provider (google/openai/mock) | mock |
| `LLM_API_KEY` | API key for LLM | - |
| `MEMORY_BACKEND` | Vector store (chromadb/pgvector/mock) | mock |
| `JIRA_MOCK_MODE` | Use mock Jira data | true |
| `GITHUB_MOCK_MODE` | Use mock GitHub data | true |

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

# Business Metrics
nexus_release_decisions_total{decision}
```

### Grafana Dashboard

Import `infrastructure/grafana/dashboard.json` for:
- LLM economics (tokens, cost)
- Agent latency (P95/P99)
- ReAct loop analytics
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
- [ ] Google Gemini live integration
- [ ] Scheduling agent for cron workflows
- [ ] Multi-tenant support
- [ ] AI-powered recommendations

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

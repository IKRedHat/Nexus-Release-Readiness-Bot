# 🚀 Nexus Release Automation System

<div align="center">

<img src="docs/assets/mockups/nexus-logo.svg" alt="Nexus Logo" width="200" onerror="this.style.display='none'"/>

### **Intelligent Multi-Agent System for Automated Release Readiness Assessments**

[![Version](https://img.shields.io/badge/version-2.4.0-blue?style=for-the-badge)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-324%20passing-brightgreen?style=for-the-badge)](docs/testing.md)
[![Python](https://img.shields.io/badge/python-3.10+-green?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge)](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/actions)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.0-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/k8s-helm-326CE5?style=for-the-badge&logo=kubernetes)](https://kubernetes.io)

*Transform your release process with AI-powered automation, real-time insights, and intelligent decision-making.*

[📚 Documentation](docs/index.md) • [🚀 Quick Start](#-quick-start) • [💬 Slack Commands](#-slack-integration) • [📊 Demo](demo/feature_walkthrough_script.md)

---

</div>

## 🎯 What is Nexus?

**Nexus** is an enterprise-grade, AI-powered release automation platform that revolutionizes how teams manage software releases. Using a sophisticated **ReAct (Reasoning + Acting)** architecture powered by Google Gemini, Nexus coordinates specialized agents to deliver intelligent **Go/No-Go release decisions** through natural language conversations.

> **"Is v2.0 ready for release?"** — Ask Nexus in plain English, and get a comprehensive analysis of your Jira tickets, CI/CD pipelines, security scans, and code quality metrics in seconds.

### 🌟 Why Choose Nexus?

| Challenge | Traditional Approach | Nexus Solution |
|-----------|---------------------|----------------|
| **Release Readiness** | Manual spreadsheets, meetings | AI-powered instant assessment |
| **Data Collection** | Hours gathering from multiple tools | Automatic aggregation in seconds |
| **Build Failures** | Manual log analysis | Smart RCA with fix suggestions |
| **Jira Hygiene** | Periodic manual audits | Proactive daily checks with auto-fix |
| **Stakeholder Updates** | Email chains, status meetings | Real-time Slack notifications |
| **Decision Making** | Gut feeling, incomplete data | Data-driven Go/No-Go with confidence scores |

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧠 **AI-Powered Intelligence**
- **ReAct Engine**: Transparent reasoning with thought → action → observation loops
- **Google Gemini 2.0**: State-of-the-art LLM with streaming and function calling
- **Smart Recommendations**: Pattern-based suggestions from historical data
- **Root Cause Analysis**: Automatic build failure diagnosis with fix suggestions

</td>
<td width="50%">

### 🎛️ **Admin Dashboard**
- **Web-based UI**: Modern React dashboard for system management
- **Dynamic Configuration**: Change settings without service restarts
- **Live Mode Switching**: Toggle Mock/Production instantly
- **Release Management**: Track versions, dates, and metrics from external sources

</td>
</tr>
<tr>
<td width="50%">

### 📊 **Advanced Analytics**
- **DORA Metrics**: Deployment frequency, lead time, MTTR, change failure rate
- **Predictive Analytics**: ML-powered release date predictions
- **Anomaly Detection**: Automatic identification of unusual patterns
- **Team Performance**: Velocity and quality comparisons

</td>
<td width="50%">

### 💬 **Slack-First Experience**
- **Natural Language**: Ask questions in plain English
- **App Home Dashboard**: Rich widgets with quick actions
- **Interactive Modals**: Fix Jira tickets directly from Slack
- **Proactive Notifications**: RCA results, hygiene alerts, release updates

</td>
</tr>
<tr>
<td width="50%">

### 🔗 **Multi-Tool Integration**
- **Jira**: Tickets, epics, sprints, story points
- **GitHub**: PRs, commits, code reviews
- **Jenkins**: Builds, artifacts, console logs
- **Confluence**: Auto-publish release reports
- **Smartsheet**: Import release schedules

</td>
<td width="50%">

### 🏢 **Enterprise Ready**
- **Multi-Tenant**: Organization isolation with plan tiers
- **JWT Authentication**: Secure inter-service communication
- **Full Observability**: Prometheus, Grafana, OpenTelemetry
- **Kubernetes Native**: Production-ready Helm charts

</td>
</tr>
</table>

---

## 🏗️ Architecture Overview

Nexus uses a **Hub-and-Spoke** architecture where the Central Orchestrator coordinates specialized agents:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │  Slack App      │  │  Admin Dashboard│  │  REST API                       │  │
│  │  - Commands     │  │  - Config UI    │  │  - /query                       │  │
│  │  - App Home     │  │  - Health       │  │  - /reports                     │  │
│  │  - Modals       │  │  - Releases     │  │  - /agents/*                    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────────────┬────────────────┘  │
└───────────┼─────────────────────┼───────────────────────────┼───────────────────┘
            │                     │                           │
            └─────────────────────┼───────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CENTRAL ORCHESTRATOR                                      │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        ReAct Engine (Gemini 2.0)                          │  │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌─────────────────┐    │  │
│  │  │ Thought │ -> │  Action │ -> │ Observation │ -> │  Final Answer   │    │  │
│  │  └─────────┘    └─────────┘    └─────────────┘    └─────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │Vector Memory│  │AI Recommender│  │ Multi-Tenancy │  │ Tool Registry    │   │
│  └─────────────┘  └──────────────┘  └───────────────┘  └──────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
┌─────────────┐ ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐
│ Jira Agent  │ │ Git/CI    │ │ Reporting   │ │ Hygiene   │ │ RCA Agent   │
│             │ │ Agent     │ │ Agent       │ │ Agent     │ │             │
│ - Tickets   │ │ - PRs     │ │ - HTML      │ │ - Checks  │ │ - Log Parse │
│ - Sprints   │ │ - Builds  │ │ - Confluence│ │ - Scoring │ │ - Git Diff  │
│ - Hierarchy │ │ - Commits │ │ - Preview   │ │ - DM      │ │ - LLM Fix   │
└──────┬──────┘ └─────┬─────┘ └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
┌─────────────┐ ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐
│    Jira     │ │  GitHub   │ │ Confluence  │ │   Slack   │ │  Jenkins    │
│    Cloud    │ │  Jenkins  │ │             │ │           │ │             │
└─────────────┘ └───────────┘ └─────────────┘ └───────────┘ └─────────────┘

                        SUPPORTING SERVICES
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│  │  Analytics  │  │  Webhooks   │  │   Redis     │  │    PostgreSQL       │    │
│  │  - DORA     │  │  - Events   │  │  - Config   │  │    - Data Store     │    │
│  │  - Predict  │  │  - Delivery │  │  - Cache    │  │    - Tenant Data    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Local orchestration |
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
- ✅ Installs dependencies
- ✅ Configures environment variables
- ✅ Builds and starts Docker services
- ✅ Runs health verification

**Setup Options:**
```bash
./scripts/setup.sh --help        # Show all options
./scripts/setup.sh --dev         # Include dev tools (pytest, black, mypy)
./scripts/setup.sh --skip-docker # Python setup only
./scripts/setup.sh --clean       # Fresh install
```

### Option 2: Docker Compose

```bash
# Clone and start
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot
docker-compose up -d

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

# Install service dependencies
pip install -r services/orchestrator/requirements.txt

# Start a service
cd services/orchestrator
uvicorn main:app --reload --port 8080
```

---

## 🖥️ Service Endpoints

Once running, access these services:

| Service | URL | Description |
|---------|-----|-------------|
| **Orchestrator API** | http://localhost:8080/docs | Central brain, query endpoint |
| **Admin Dashboard** | http://localhost:8088 | Web UI for configuration |
| **Jira Hygiene Agent** | http://localhost:8005/docs | Proactive quality checks |
| **RCA Agent** | http://localhost:8006/docs | Build failure analysis |
| **Analytics Service** | http://localhost:8086/docs | DORA metrics & predictions |
| **Grafana** | http://localhost:3000 | Dashboards (admin/nexus_admin) |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Jaeger** | http://localhost:16686 | Distributed tracing |

### Try Your First Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is the v2.0 release ready?"}'
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

### Slack App Home

The App Home provides a rich dashboard with:
- 📊 Release readiness overview
- 🎯 Quick action buttons
- 📋 Recent activities
- ⚠️ Active blockers
- 📈 Hygiene score widget

### Interactive Notifications

Nexus sends proactive notifications:
- **Hygiene Violations**: DM with "Fix Now" button opening an interactive modal
- **RCA Results**: Channel message with root cause, suspected file, and fix suggestion
- **Release Updates**: Status changes and milestone completions

---

## 🎛️ Admin Dashboard

The Admin Dashboard provides a web-based interface for managing Nexus:

![Admin Dashboard](docs/assets/mockups/admin-dashboard.svg)

### Features

| Tab | Functionality |
|-----|---------------|
| **Dashboard** | System overview, agent health, quick actions |
| **Releases** | Track versions, target dates, import from Smartsheet/CSV |
| **Observability** | Metrics, charts, LLM usage, integrated Grafana |
| **Health Monitor** | Real-time agent status with auto-refresh |
| **Configuration** | Manage credentials, URLs, API keys securely |

### Mode Switching

Instantly toggle between **Mock Mode** (development) and **Live Mode** (production):

```bash
# Via API
curl -X POST http://localhost:8088/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "live"}'
```

---

## 📊 Analytics & Metrics

### DORA Metrics

Nexus tracks key DevOps Research and Assessment metrics:

| Metric | Description |
|--------|-------------|
| **Deployment Frequency** | How often you deploy to production |
| **Lead Time for Changes** | Time from commit to production |
| **Mean Time to Recovery** | Time to restore service after incident |
| **Change Failure Rate** | Percentage of deployments causing failures |

### Prometheus Metrics

```prometheus
# LLM Usage
nexus_llm_tokens_total{model_name, type}
nexus_llm_cost_dollars_total{model_name}

# Agent Performance
nexus_tool_usage_total{tool_name, status}
http_request_duration_seconds{agent_type}

# Business Metrics
nexus_project_hygiene_score{project_key}
nexus_release_decisions_total{decision}
nexus_rca_requests_total{status}
```

### Grafana Dashboard

Import `infrastructure/grafana/dashboard.json` for comprehensive observability:

![Grafana Dashboard](docs/assets/mockups/grafana-dashboard.svg)

---

## 🧪 Testing

Nexus has a comprehensive test suite with **324+ tests** across 4 categories:

| Category | Count | Purpose |
|----------|-------|---------|
| **Unit** | ~180 | Individual component testing |
| **E2E** | ~90 | Service endpoint testing |
| **Integration** | ~20 | Inter-service communication |
| **Smoke** | ~34 | Quick health verification |

### Running Tests

```bash
# All tests
pytest

# By category
pytest -m unit
pytest -m e2e
pytest -m integration
pytest -m smoke

# With coverage
pytest --cov=shared --cov=services --cov-report=html

# Parallel execution
pytest -n auto
```

📖 See [Testing Documentation](docs/testing.md) for complete details.

---

## 📁 Project Structure

```
Nexus-Release-Readiness-Bot/
├── services/                        # Microservices
│   ├── orchestrator/                # Central brain (ReAct engine)
│   ├── agents/
│   │   ├── jira_agent/              # Jira integration
│   │   ├── git_ci_agent/            # GitHub + Jenkins
│   │   ├── reporting_agent/         # Report generation
│   │   ├── slack_agent/             # Slack interface
│   │   ├── jira_hygiene_agent/      # Proactive quality checks
│   │   └── rca_agent/               # Root cause analysis
│   ├── analytics/                   # Advanced analytics
│   ├── webhooks/                    # Event delivery
│   └── admin_dashboard/             # Admin UI (React + FastAPI)
│
├── shared/nexus_lib/                # Shared library
│   ├── schemas/                     # Pydantic models
│   ├── llm/                         # LLM clients
│   ├── multitenancy/                # Tenant isolation
│   ├── recommendations/             # AI suggestions
│   ├── config.py                    # Dynamic configuration
│   ├── middleware.py                # Auth, metrics, tenant
│   └── instrumentation.py           # OTEL, Prometheus
│
├── infrastructure/
│   ├── docker/                      # Dockerfiles
│   ├── k8s/nexus-stack/             # Helm chart
│   ├── grafana/                     # Dashboards
│   └── terraform/                   # Cloud infra
│
├── scripts/                         # Automation
│   ├── setup.sh                     # One-click setup
│   ├── dev.sh                       # Development helper
│   ├── verify.sh                    # Health checks
│   └── uninstall.sh                 # Clean removal
│
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   ├── e2e/                         # End-to-end tests
│   ├── integration/                 # Integration tests
│   └── smoke/                       # Smoke tests
│
├── docs/                            # Documentation
└── demo/                            # Demo scripts
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment (development/production) | development |
| `LLM_PROVIDER` | LLM provider (google/openai/mock) | mock |
| `LLM_MODEL` | Model name | gemini-2.0-flash |
| `LLM_API_KEY` | API key for LLM | - |
| `MEMORY_BACKEND` | Vector store (chromadb/pgvector/mock) | mock |
| `MULTI_TENANT_ENABLED` | Enable multi-tenancy | false |
| `JIRA_MOCK_MODE` | Use mock Jira data | true |
| `GITHUB_MOCK_MODE` | Use mock GitHub data | true |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |

### Dynamic Configuration

Use the Admin Dashboard or API to change configuration without restarts:

```bash
# Get current mode
curl http://localhost:8088/mode

# Update configuration
curl -X POST http://localhost:8088/config \
  -H "Content-Type: application/json" \
  -d '{"key": "nexus:config:jira_url", "value": "https://your-org.atlassian.net"}'
```

---

## 🚢 Deployment

### Kubernetes (Production)

```bash
cd infrastructure/k8s/nexus-stack
helm dependency update

helm upgrade --install nexus . \
  --namespace nexus \
  --create-namespace \
  --values production-values.yaml
```

### Docker Compose (Development)

```bash
docker-compose up -d
docker-compose logs -f
```

### Frontend (Vercel)

Deploy the Admin Dashboard to Vercel for production frontend hosting:

```bash
# Using Python deployment script
python scripts/deploy_frontend.py --env production --api-url https://your-api.com

# Or manually with Vercel CLI
cd services/admin_dashboard/frontend
npm install --legacy-peer-deps
npm run build:prod
vercel deploy --prod
```

📖 See [Frontend Deployment Guide](docs/frontend-deployment-guide.md) for complete setup.

📖 See [Deployment Runbook](docs/runbooks/deployment.md) for backend production setup.

---

## 🆕 Version History

### v2.4.0 - Frontend Deployment & Testing
- 🚀 **Vercel Deployment** - Deploy Admin Dashboard to Vercel cloud
- 🐍 **Python Deploy Script** - Comprehensive automation with rollback support
- 🔄 **GitHub Actions** - CI/CD workflow for frontend with preview deploys
- 🧪 **324 Passing Tests** - Comprehensive test suite fixes (116% improvement)

### v2.3.1 - Release Management
- 📅 **Release Management** - Track versions and target dates from Smartsheet/CSV/webhooks
- 🎛️ **Enhanced Admin Dashboard** - New Releases page with metrics
- 📊 **Updated Mockups** - All dashboards now show 5 navigation items

### v2.3.0 - Admin Dashboard & Dynamic Configuration
- 🎛️ **Admin Dashboard** - Web UI for system management
- 🔄 **Dynamic Configuration** - Redis-backed settings without restarts
- ⚡ **Live Mode Switching** - Toggle Mock/Live instantly

### v2.2.0 - Smart Root Cause Analysis
- 🔍 **RCA Agent** - AI-powered build failure analysis
- 🔔 **Auto-Trigger** - Jenkins webhook triggers RCA
- 💬 **Slack Notifications** - RCA results with fix suggestions

### v2.1.0 - Analytics & Webhooks
- 📊 **Advanced Analytics** - DORA metrics, predictions, anomalies
- 🔔 **Webhook Integrations** - Real-time event delivery

### v2.0.0 - Core Platform
- 🤖 **Google Gemini Integration** - Production LLM
- 💡 **AI Recommendations Engine** - Pattern-based suggestions
- 🏠 **Slack App Home** - Rich dashboard
- 🏢 **Multi-Tenant Support** - Enterprise isolation

📖 See [CHANGELOG.md](CHANGELOG.md) for complete history.

---

## 🗺️ Roadmap

### Completed ✅
- [x] Core ReAct Engine with Gemini 2.0
- [x] Jira, GitHub, Jenkins, Confluence integrations
- [x] Slack Block Kit with App Home
- [x] Jira Hygiene Agent with interactive fixes
- [x] Smart Root Cause Analysis (RCA)
- [x] Advanced Analytics Dashboard
- [x] Webhook Integrations
- [x] Admin Dashboard with Dynamic Configuration
- [x] Release Management from External Sources
- [x] Multi-Tenant Support
- [x] Kubernetes Helm Charts

### In Progress 🚧
- [ ] Anthropic Claude integration
- [ ] Custom LLM fine-tuning for release domain
- [ ] Enhanced security scanning integration

### Planned 📋
- [ ] Mobile app companion
- [ ] GitLab integration
- [ ] Azure DevOps integration
- [ ] Automated rollback suggestions
- [ ] Cost optimization recommendations

---

## 🤝 Contributing

We welcome contributions! Every contribution matters, whether it's code, documentation, bug reports, or ideas.

### Quick Start

1. **Read** our [Contributing Guide](CONTRIBUTING.md)
2. **Find** an issue labeled [`good first issue`](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
3. **Fork** the repository
4. **Create** a feature branch: `git checkout -b feature/amazing`
5. **Commit** with conventional commits: `git commit -m 'feat: add amazing feature'`
6. **Push** and open a Pull Request

### Community

- 📜 [Code of Conduct](CODE_OF_CONDUCT.md)
- 🔒 [Security Policy](SECURITY.md)
- 👥 [Contributors](CONTRIBUTORS.md)

### Issue Templates

- 🐛 [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- 📝 [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)

---

## 🔄 CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | Push, PR | Lint, test, security scan, Docker build |
| **Release** | Tags (v*) | Build images, create GitHub release |
| **Dependabot** | Weekly | Automated dependency updates |
| **Stale** | Daily | Clean up inactive issues/PRs |

📖 See [CI/CD Documentation](docs/ci-cd/index.md) for details.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/user_guide.md) | End-user documentation |
| [Architecture](docs/architecture.md) | System design and components |
| [API Reference](docs/api-specs/overview.md) | REST API documentation |
| [Admin Dashboard](docs/admin-dashboard.md) | Dashboard features and API |
| [Admin Tutorial](docs/admin-dashboard-tutorial.md) | Step-by-step dashboard guide |
| [Frontend Deployment](docs/frontend-deployment-guide.md) | Vercel deployment guide |
| [Testing Guide](docs/testing.md) | Test strategy and execution |
| [Backend Deployment](docs/runbooks/deployment.md) | Production deployment guide |
| [RCA Documentation](docs/rca.md) | Root Cause Analysis feature |
| [Analytics](docs/analytics.md) | Analytics dashboard features |
| [Webhooks](docs/webhooks.md) | Webhook integrations |
| [API Testing](docs/api-testing-guide.md) | API endpoint testing guide |

---

## ❓ FAQ

<details>
<summary><strong>What LLM providers are supported?</strong></summary>

Nexus supports:
- **Google Gemini** (recommended): gemini-2.0-flash, gemini-1.5-pro
- **OpenAI**: gpt-4o, gpt-4-turbo
- **Mock**: For development without API costs

</details>

<details>
<summary><strong>Can I use Nexus without Slack?</strong></summary>

Yes! While Slack provides the best user experience, you can use Nexus via:
- REST API (`POST /query`)
- Admin Dashboard
- Direct agent API calls

</details>

<details>
<summary><strong>How do I switch from mock to production mode?</strong></summary>

1. **Via Admin Dashboard**: Navigate to Dashboard → Click "Switch to Live Mode"
2. **Via API**: `POST http://localhost:8088/mode` with `{"mode": "live"}`
3. **Via Environment**: Set `LLM_PROVIDER=google`, `JIRA_MOCK_MODE=false`, etc.

</details>

<details>
<summary><strong>What's the cost of running Nexus with Gemini?</strong></summary>

Costs depend on usage. Typical costs:
- **Gemini 2.0 Flash**: ~$0.001 per query
- **Gemini 1.5 Pro**: ~$0.01 per complex query
- Track costs via Grafana dashboard or `nexus_llm_cost_dollars_total` metric

</details>

<details>
<summary><strong>Can I deploy Nexus on-premise?</strong></summary>

Yes! Nexus is fully self-hosted. Use:
- Docker Compose for small deployments
- Kubernetes Helm charts for enterprise scale
- Air-gapped deployment with mock LLM or self-hosted models

</details>

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Built with ❤️ by the Nexus Team

**[⭐ Star us on GitHub](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot)** — it helps!

[Documentation](docs/index.md) • [Report Bug](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues/new?template=bug_report.md) • [Request Feature](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues/new?template=feature_request.md)

---

*Making release management intelligent, one decision at a time.*

</div>

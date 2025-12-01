# Nexus Release Automation System

<div style="text-align: center; margin-bottom: 2em;">
  <img src="https://img.shields.io/badge/version-2.3.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
</div>

**Nexus** is an intelligent multi-agent system that automates release readiness assessments. It uses a ReAct (Reasoning + Acting) architecture powered by LLMs to coordinate specialized agents that gather data from Jira, GitHub, Jenkins, and other systems to provide Go/No-Go release decisions.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Kubernetes (for production deployment)
- Google Cloud API key (for Gemini) or OpenAI API key

### Local Development

```bash
# Clone the repository
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# Start the development stack
docker-compose up -d

# Access services
# - Orchestrator: http://localhost:8080
# - Jira Hygiene Agent: http://localhost:8085
# - RCA Agent: http://localhost:8006
# - Analytics Dashboard: http://localhost:8086
# - Admin Dashboard: http://localhost:8088
# - Webhook Service: http://localhost:8087
# - Grafana: http://localhost:3000 (admin/nexus_admin)
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
```

### Try it out

```bash
# Check health
curl http://localhost:8080/health

# Run a query (uses Gemini or mock LLM)
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the release readiness status for v2.0?"}'

# Trigger a hygiene check
curl -X POST http://localhost:8085/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": false}'

# Get AI recommendations
curl http://localhost:8080/recommendations

# Get analytics KPIs
curl http://localhost:8086/api/v1/kpis?time_range=7d

# Create a webhook subscription
curl -X POST http://localhost:8087/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"name": "My Webhook", "url": "https://example.com/hook", "events": ["release.completed"]}'

# Analyze a build failure (RCA)
curl -X POST http://localhost:8006/analyze \
  -H "Content-Type: application/json" \
  -d '{"job_name": "nexus-main", "build_number": 142, "notify": true}'

# Or ask naturally via the orchestrator
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Why did the last build fail?"}'
```

## 🏗️ Architecture Overview

```mermaid
flowchart TB
    subgraph Slack["Slack Workspace"]
        User[User] --> SlackApp[Nexus Bot]
        SlackApp --> AppHome[App Home Dashboard]
    end
    
    subgraph Nexus["Nexus System"]
        SlackApp --> SlackAgent[Slack Agent]
        SlackAgent --> Orchestrator[Central Orchestrator]
        
        subgraph LLMLayer["LLM Layer"]
            LLMFactory[LLM Factory]
            Gemini[Google Gemini]
            OpenAI[OpenAI GPT]
        end
        
        Orchestrator --> ReAct[ReAct Engine]
        ReAct --> Memory[(Vector Memory)]
        ReAct --> LLMFactory
        LLMFactory --> Gemini
        LLMFactory --> OpenAI
        
        subgraph AILayer["AI Layer"]
            RecEngine[Recommendation Engine]
            Analyzers[Pattern Analyzers]
        end
        
        Orchestrator --> RecEngine
        RecEngine --> Analyzers
        
        Orchestrator --> JiraAgent[Jira Agent]
        Orchestrator --> GitAgent[Git/CI Agent]
        Orchestrator --> ReportAgent[Reporting Agent]
        Orchestrator --> RCAAgent[RCA Agent]
        
        RCAAgent --> GitAgent
        RCAAgent --> SlackAgent
        
        HygieneAgent[Jira Hygiene Agent] --> JiraAgent
        HygieneAgent --> SlackAgent
        
        subgraph MultiTenant["Multi-Tenancy"]
            TenantMW[Tenant Middleware]
            TenantRepo[Tenant Repository]
        end
    end
    
    subgraph External["External Systems"]
        JiraAgent --> Jira[Jira Cloud]
        GitAgent --> GitHub[GitHub]
        GitAgent --> Jenkins[Jenkins]
        ReportAgent --> Confluence[Confluence]
    end
```

## 🎯 Key Features

### 🎛️ Admin Dashboard
Web-based UI for system management and configuration:
- **Mode Switching**: Toggle Mock/Live mode instantly for all agents
- **Credential Management**: Securely update API keys and URLs
- **Health Monitoring**: Real-time status of all connected agents
- **Dynamic Configuration**: Change settings without service restart

![Admin Dashboard Preview](assets/mockups/admin-dashboard.svg)

### 🤖 Google Gemini Integration
Production-ready LLM client with full Gemini 2.0 support:
- **Async Generation**: Non-blocking API calls
- **Streaming**: Real-time token streaming
- **Function Calling**: Native tool use support
- **Cost Tracking**: Token usage and cost estimation
- **Fallback**: Automatic fallback to mock mode

### 🏢 Multi-Tenant Support
Enterprise-ready organization isolation:
- **Tenant Plans**: Free, Starter, Professional, Enterprise
- **Resource Limits**: Per-tenant API, LLM, and storage limits
- **Configuration Isolation**: Separate Jira, GitHub, Slack settings per tenant
- **Feature Flags**: Enable/disable features per organization

### 💡 AI-Powered Recommendations
Intelligent suggestions based on historical patterns:
- **Release Timing**: Best days to release, failure patterns
- **Hygiene Improvement**: Trend detection, violation patterns
- **Velocity Optimization**: Predictability scoring
- **Risk Mitigation**: Blocker and vulnerability assessment

### 🏠 Slack App Home Dashboard
Rich interactive dashboard when opening the app:
- **Quick Actions**: One-click status, hygiene, reports
- **Release Overview**: Current status, blockers, scores
- **Hygiene Widget**: Score with fix button
- **AI Recommendations**: Top suggestions preview

![Slack App Home Preview](assets/mockups/slack-app-home.svg)

### 🔧 Proactive Jira Hygiene
The Jira Hygiene Agent ensures data quality:
- **Scheduled Checks**: Weekdays at 9:00 AM
- **Field Validation**: Labels, Fix Version, Story Points, Team
- **Interactive Fixes**: Fix violations directly from Slack modals
- **Hygiene Scoring**: Track compliance percentage

### 🔍 Smart Root Cause Analysis (RCA)
AI-powered build failure analysis with auto-trigger:
- **Auto-Trigger**: Jenkins webhook for automatic analysis
- **Slack Notifications**: Results sent to release channel with @PR-owner
- **LLM Analysis**: Gemini 1.5 Pro correlates logs with code changes
- **Fix Suggestions**: Actionable code fixes with confidence scores
- **Git Correlation**: Maps errors to specific commits and files

### 📊 Advanced Analytics Dashboard
Comprehensive insights into your release automation metrics:

![Analytics Dashboard](assets/mockups/analytics-dashboard.svg)

- **DORA Metrics**: Deployment frequency, lead time, MTTR, change failure rate
- **Quality Scores**: Build success, hygiene, security scores in real-time
- **Predictive Analytics**: AI-powered release date and quality forecasting
- **Anomaly Detection**: Automatic alerts for unusual patterns
- **Team Performance**: Compare teams by velocity, quality, and efficiency
- **AI Insights**: Intelligent recommendations based on your data

### 📈 Real-time Observability
Full visibility into system performance:
- LLM token usage and costs
- Agent latency and error rates
- ReAct loop analytics
- Hygiene score tracking
- RCA analysis metrics
- Business metrics (Go/No-Go decisions)

### 💬 Slack Integration
Natural Slack interface with:
- `/nexus status` - Check release readiness
- `/jira-update` - Update tickets via modal
- App Home dashboard with widgets
- Hygiene notifications with fix buttons
- Block Kit rich messages

## 📖 Documentation

| Section | Description |
|---------|-------------|
| [User Guide](user_guide.md) | How to use Nexus commands and features |
| [Architecture](architecture.md) | System design and technical details |
| [API Reference](api-specs/overview.md) | OpenAPI specifications for all agents |
| [Deployment](runbooks/deployment.md) | Production deployment guide |

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, FastAPI, Pydantic |
| LLM | Google Gemini 2.0, OpenAI GPT-4 (configurable) |
| Vector Store | ChromaDB, PostgreSQL + pgvector |
| Messaging | Slack Bolt SDK |
| Scheduling | APScheduler |
| Multi-tenancy | Custom middleware with tenant isolation |
| Observability | Prometheus, Grafana, Jaeger, OpenTelemetry |
| Infrastructure | Docker, Kubernetes, Helm |

## 🔌 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Orchestrator | 8080 | Central brain with Gemini/GPT |
| Jira Agent | 8081 | Jira operations |
| Git/CI Agent | 8082 | GitHub + Jenkins |
| Reporting Agent | 8083 | Reports |
| Slack Agent | 8084 | Slack interface + App Home |
| **Jira Hygiene Agent** | **8005** | **Proactive quality checks** |
| **RCA Agent** | **8006** | **Root cause analysis** |
| **Analytics** | **8086** | **Advanced analytics** |
| **Webhooks** | **8087** | **Webhook integrations** |
| **Admin Dashboard** | **8088** | **System management UI** |

## 🆕 What's New

### v2.3 - Admin Dashboard
- ✅ **Admin Dashboard** - Web UI for system management
- ✅ **Dynamic Configuration** - Redis-backed live configuration
- ✅ **Mode Switching** - Instant Mock/Live toggle
- ✅ **Secure Credentials** - Masked secrets management

### v2.2 - Smart RCA
- ✅ **RCA Agent** - AI-powered build failure analysis
- ✅ **Auto-Trigger** - Jenkins webhook integration
- ✅ **Slack Notifications** - Results to release channel

### v2.1 - Analytics & Webhooks
- ✅ **Analytics Dashboard** - DORA metrics, predictions
- ✅ **Webhook Service** - Event delivery to external systems

### v2.0 - Core Platform
- ✅ **Google Gemini 2.0 Flash** - Production LLM integration
- ✅ **Multi-tenant Architecture** - Enterprise organization isolation
- ✅ **AI Recommendations Engine** - Intelligent pattern-based suggestions
- ✅ **Slack App Home** - Rich dashboard with widgets

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/LICENSE) file for details.

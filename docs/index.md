# Nexus Release Automation System

<div style="text-align: center; margin-bottom: 2em;">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
</div>

**Nexus** is an intelligent multi-agent system that automates release readiness assessments. It uses a ReAct (Reasoning + Acting) architecture powered by LLMs to coordinate specialized agents that gather data from Jira, GitHub, Jenkins, and other systems to provide Go/No-Go release decisions.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Kubernetes (for production deployment)

### Local Development

```bash
# Clone the repository
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# Start the development stack
cd infrastructure/docker
docker-compose up -d

# Access services
# - Orchestrator: http://localhost:8080
# - Grafana: http://localhost:3000 (admin/nexus_admin)
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
```

### Try it out

```bash
# Check health
curl http://localhost:8080/health

# Run a query
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the release readiness status for v2.0?"}'
```

## 🏗️ Architecture Overview

```mermaid
flowchart TB
    subgraph Slack["Slack Workspace"]
        User[User] --> SlackApp[Nexus Bot]
    end
    
    subgraph Nexus["Nexus System"]
        SlackApp --> SlackAgent[Slack Agent]
        SlackAgent --> Orchestrator[Central Orchestrator]
        
        Orchestrator --> ReAct[ReAct Engine]
        ReAct --> Memory[(Vector Memory)]
        ReAct --> LLM[LLM Provider]
        
        Orchestrator --> JiraAgent[Jira Agent]
        Orchestrator --> GitAgent[Git/CI Agent]
        Orchestrator --> ReportAgent[Reporting Agent]
    end
    
    subgraph External["External Systems"]
        JiraAgent --> Jira[Jira Cloud]
        GitAgent --> GitHub[GitHub]
        GitAgent --> Jenkins[Jenkins]
        ReportAgent --> Confluence[Confluence]
    end
```

## 🎯 Key Features

### 🤖 Intelligent Orchestration
The ReAct (Reasoning + Acting) engine uses LLMs to understand natural language queries, plan multi-step workflows, and coordinate specialized agents.

### 📊 Comprehensive Assessments
Automatically gathers data from:
- **Jira**: Ticket status, sprint progress, blockers
- **GitHub**: PR status, branch health, security scans
- **Jenkins**: Build status, test results, artifacts
- **Confluence**: Publishes rich HTML reports

### 📈 Real-time Observability
Full visibility into system performance:
- LLM token usage and costs
- Agent latency and error rates
- ReAct loop analytics
- Business metrics (Go/No-Go decisions)

### 💬 Slack Integration
Natural Slack interface with:
- `/nexus status` - Check release readiness
- `/jira-update` - Update tickets via modal
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
| LLM | Google Gemini, OpenAI GPT (configurable) |
| Vector Store | ChromaDB, PostgreSQL + pgvector |
| Messaging | Slack Bolt SDK |
| Observability | Prometheus, Grafana, Jaeger, OpenTelemetry |
| Infrastructure | Docker, Kubernetes, Helm |

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/LICENSE) file for details.

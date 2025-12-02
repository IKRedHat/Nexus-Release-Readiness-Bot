# Deployment Runbook

This runbook provides step-by-step instructions for deploying Nexus to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration Reference](#configuration-reference)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Runtime |
| Node.js | 18+ | MCP sidecar servers (GitHub, Slack) |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Local orchestration |
| kubectl | 1.24+ | Kubernetes CLI |
| Helm | 3.10+ | Kubernetes package manager |

### Required Credentials

| Service | Credential Type | Required For |
|---------|-----------------|--------------|
| Jira | API Token | Jira Agent, Hygiene Agent |
| GitHub | Personal Access Token | Git/CI Agent |
| Jenkins | API Token | Git/CI Agent |
| Confluence | API Token | Reporting Agent |
| Slack | Bot Token + App Token | Slack Agent |
| LLM Provider | API Key | Orchestrator (choose one) |

### LLM Provider Options

| Provider | API Key Format | Endpoint |
|----------|---------------|----------|
| OpenAI | `sk-proj-...` | api.openai.com |
| Azure OpenAI | Custom | your-resource.openai.azure.com |
| Google Gemini | `AIzaSy...` | generativelanguage.googleapis.com |
| Anthropic | `sk-ant-api03-...` | api.anthropic.com |
| Groq | `gsk_...` | api.groq.com |
| Ollama | N/A (self-hosted) | localhost:11434 |
| vLLM | Optional | your-server:8000 |

---

## Local Development

### Automated Setup (Recommended)

Use the one-click setup script for the fastest setup:

```bash
# Clone repository
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# Run automated setup
./scripts/setup.sh
```

The setup script automatically:
- Checks all prerequisites (Python, Node.js, Docker, etc.)
- Creates Python virtual environment
- Installs all dependencies
- Configures environment variables
- Builds and starts Docker services
- Verifies everything is working

**Setup Options:**

| Option | Description |
|--------|-------------|
| `--help` | Show all available options |
| `--dev` | Install development tools (pytest, black, mypy) |
| `--skip-docker` | Skip Docker services (Python setup only) |
| `--skip-venv` | Skip virtual environment creation |
| `--clean` | Remove existing setup before installing |

### Manual Setup

If you prefer manual setup:

#### 1. Clone Repository

```bash
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install shared library
pip install -e shared/

# Install service dependencies
pip install -r services/orchestrator/requirements.txt
pip install -r services/agents/jira_agent/requirements.txt
pip install -r services/agents/jira_hygiene_agent/requirements.txt
# ... repeat for other agents
```

#### 3. Install Node.js Dependencies (for MCP sidecars)

```bash
# Install MCP sidecar dependencies
cd infrastructure/mcp-servers
npm install
```

#### 4. Run Services Locally

```bash
# Terminal 1: Orchestrator
cd services/orchestrator
uvicorn main:app --reload --port 8080

# Terminal 2: Jira Agent (MCP)
cd services/agents/jira_agent
uvicorn main:app --reload --port 8001

# Terminal 3: Jira Hygiene Agent (MCP)
cd services/agents/jira_hygiene_agent
uvicorn main:app --reload --port 8005

# Terminal 4: RCA Agent (MCP)
cd services/agents/rca_agent
uvicorn main:app --reload --port 8006

# ... repeat for other agents
```

### Development Helper Scripts

Use the dev helper for common tasks:

```bash
./scripts/dev.sh start        # Start Docker services
./scripts/dev.sh stop         # Stop Docker services
./scripts/dev.sh logs         # View logs
./scripts/dev.sh health       # Check service health
./scripts/dev.sh test         # Run tests
./scripts/dev.sh query "..."  # Send query to orchestrator
```

---

## Docker Compose Deployment

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
vim .env
```

**Required Environment Variables:**

```bash
# System
NEXUS_ENV=development

# LLM Configuration (choose one provider)
LLM_PROVIDER=openai              # openai, google, anthropic, ollama, groq, vllm, mock
LLM_MODEL=gpt-4o                 # Model name
OPENAI_API_KEY=sk-proj-...       # If using OpenAI
GEMINI_API_KEY=AIzaSy...         # If using Google
ANTHROPIC_API_KEY=sk-ant-...     # If using Anthropic
GROQ_API_KEY=gsk_...             # If using Groq
OLLAMA_BASE_URL=http://ollama:11434  # If using Ollama
VLLM_API_BASE=http://vllm:8000/v1    # If using vLLM

# Jira
JIRA_URL=https://your-org.atlassian.net
JIRA_USERNAME=user@company.com
JIRA_API_TOKEN=your-token
JIRA_PROJECT_KEY=PROJ

# GitHub
GITHUB_TOKEN=ghp_...
GITHUB_ORG=your-org
GITHUB_REPO=your-repo

# Jenkins
JENKINS_URL=http://jenkins:8080
JENKINS_USERNAME=admin
JENKINS_API_TOKEN=your-token

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...

# Redis & PostgreSQL
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://nexus:nexus@postgres:5432/nexus
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Start with specific profile
docker-compose --profile full up -d        # All services
docker-compose --profile minimal up -d     # Core services only
docker-compose --profile observability up -d  # Include monitoring

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Service Endpoints

| Service | URL | Protocol |
|---------|-----|----------|
| Orchestrator | http://localhost:8080 | REST |
| Jira Agent | http://localhost:8001 | MCP/SSE |
| Git/CI Agent | http://localhost:8002 | MCP/SSE |
| Reporting Agent | http://localhost:8003 | MCP/SSE |
| Slack Agent | http://localhost:8084 | REST |
| **Jira Hygiene Agent** | **http://localhost:8005** | **MCP/SSE** |
| **RCA Agent** | **http://localhost:8006** | **MCP/SSE** |
| **Admin Dashboard** | **http://localhost:8088** | **REST** |
| Grafana | http://localhost:3000 | HTTP |
| Prometheus | http://localhost:9090 | HTTP |

### 4. Stop Services

```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

---

## Kubernetes Deployment

### 1. Prepare Namespace

```bash
kubectl create namespace nexus
kubectl config set-context --current --namespace=nexus
```

### 2. Create Secrets

```bash
# Create secrets file (do not commit!)
cat <<EOF > secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: nexus-secrets
  namespace: nexus
type: Opaque
stringData:
  NEXUS_JWT_SECRET: "your-jwt-secret-here"
  
  # LLM Configuration
  LLM_PROVIDER: "openai"
  LLM_MODEL: "gpt-4o"
  OPENAI_API_KEY: "sk-proj-..."
  # Or for other providers:
  # GEMINI_API_KEY: "AIzaSy..."
  # ANTHROPIC_API_KEY: "sk-ant-..."
  # GROQ_API_KEY: "gsk_..."
  
  # Jira
  JIRA_URL: "https://your-company.atlassian.net"
  JIRA_USERNAME: "your-email@company.com"
  JIRA_API_TOKEN: "your-jira-api-token"
  
  # GitHub
  GITHUB_TOKEN: "ghp_your-github-token"
  
  # Jenkins
  JENKINS_URL: "https://jenkins.company.com"
  JENKINS_USERNAME: "jenkins-user"
  JENKINS_API_TOKEN: "jenkins-api-token"
  
  # Confluence
  CONFLUENCE_URL: "https://your-company.atlassian.net/wiki"
  CONFLUENCE_USERNAME: "your-email@company.com"
  CONFLUENCE_API_TOKEN: "your-confluence-token"
  
  # Slack
  SLACK_BOT_TOKEN: "xoxb-your-bot-token"
  SLACK_SIGNING_SECRET: "your-signing-secret"
  SLACK_APP_TOKEN: "xapp-your-app-token"
  
  # Database
  POSTGRES_PASSWORD: "secure-postgres-password"
  REDIS_PASSWORD: "secure-redis-password"
EOF

kubectl apply -f secrets.yaml
```

### 3. Deploy with Helm

```bash
cd infrastructure/k8s/nexus-stack

# Update dependencies
helm dependency update

# Install/upgrade
helm upgrade --install nexus . \
  --namespace nexus \
  --values values.yaml \
  --set global.environment=production \
  --set global.imageTag=v3.0.0 \
  --set orchestrator.llm.provider=openai

# Wait for deployment
kubectl rollout status deployment/nexus-orchestrator
kubectl rollout status deployment/nexus-jira-hygiene-agent
kubectl rollout status deployment/nexus-rca-agent
```

### 4. Configure Ingress

```yaml
# ingress-values.yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: 10m
  hosts:
    - host: nexus.your-domain.com
      paths:
        - path: /api
          service: orchestrator
        - path: /slack
          service: slack-agent
        - path: /admin
          service: admin-dashboard
  tls:
    - secretName: nexus-tls
      hosts:
        - nexus.your-domain.com
```

```bash
helm upgrade nexus . --values values.yaml --values ingress-values.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -l app.kubernetes.io/name=nexus-stack

# Check services
kubectl get svc

# Check ingress
kubectl get ingress

# View logs
kubectl logs -l app.kubernetes.io/component=orchestrator -f
kubectl logs -l app.kubernetes.io/component=jira-hygiene-agent -f
kubectl logs -l app.kubernetes.io/component=rca-agent -f
```

---

## Configuration Reference

### Orchestrator Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment | development |
| `LLM_PROVIDER` | LLM backend (openai/google/anthropic/ollama/groq/vllm/mock) | mock |
| `LLM_MODEL` | LLM model name | gpt-4o |
| `LLM_TEMPERATURE` | Generation temperature | 0.7 |
| `LLM_MAX_TOKENS` | Max output tokens | 4096 |
| `LLM_BASE_URL` | Custom API endpoint (self-hosted) | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GROQ_API_KEY` | Groq API key | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure deployment name | - |
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `VLLM_API_BASE` | vLLM server URL | - |
| `MEMORY_BACKEND` | Vector store (chromadb/pgvector/mock) | mock |
| `ORCHESTRATOR_URL` | Self URL for agents | http://localhost:8080 |
| `RECOMMENDATIONS_ENABLED` | Enable AI recommendations | true |

### MCP Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `JIRA_AGENT_MCP_URL` | Jira Agent MCP endpoint | http://jira-agent:8001/sse |
| `GIT_AGENT_MCP_URL` | Git/CI Agent MCP endpoint | http://git-agent:8002/sse |
| `REPORTING_AGENT_MCP_URL` | Reporting Agent MCP endpoint | http://reporting-agent:8003/sse |
| `HYGIENE_AGENT_MCP_URL` | Hygiene Agent MCP endpoint | http://hygiene-agent:8005/sse |
| `RCA_AGENT_MCP_URL` | RCA Agent MCP endpoint | http://rca-agent:8006/sse |
| `MCP_AUTO_RECONNECT` | Auto-reconnect on disconnect | true |
| `MCP_RECONNECT_INTERVAL` | Reconnect interval (seconds) | 5 |

### LangGraph Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGGRAPH_CHECKPOINTER` | State persistence (postgres/memory) | postgres |
| `POSTGRES_URL` | PostgreSQL connection URL | - |
| `MAX_GRAPH_ITERATIONS` | Max LangGraph iterations | 10 |
| `HUMAN_APPROVAL_REQUIRED` | Require human approval for actions | false |
| `HUMAN_APPROVAL_TIMEOUT` | Approval timeout (seconds) | 300 |

### Multi-Tenancy Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MULTI_TENANT_ENABLED` | Enable multi-tenant mode | false |
| `TENANT_RESOLUTION_STRATEGY` | header/subdomain/path | header |
| `DEFAULT_TENANT_PLAN` | Default plan for new tenants | starter |
| `TENANT_DB_URL` | Database for tenant storage | - |
| `TENANT_CACHE_TTL` | Tenant cache TTL in seconds | 300 |

### AI Recommendations Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `RECOMMENDATIONS_ENABLED` | Enable recommendations | true |
| `RELEASE_HISTORY_DAYS` | Days of history to analyze | 90 |
| `HYGIENE_TREND_WINDOW` | Days for hygiene trend | 14 |
| `MIN_RELEASES_FOR_PATTERNS` | Min releases for analysis | 5 |

### Jira Hygiene Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `JIRA_MOCK_MODE` | Use mock Jira data | true |
| `JIRA_URL` | Jira instance URL | - |
| `JIRA_USERNAME` | Jira username/email | - |
| `JIRA_API_TOKEN` | Jira API token | - |
| `HYGIENE_SCHEDULE_HOUR` | Hour for scheduled checks (0-23) | 9 |
| `HYGIENE_SCHEDULE_MINUTE` | Minute for scheduled checks | 0 |
| `HYGIENE_SCHEDULE_DAYS` | Days to run (mon-fri/daily) | mon-fri |
| `HYGIENE_TIMEZONE` | Timezone for schedule | UTC |
| `HYGIENE_PROJECTS` | Projects to check (comma-separated) | (all) |
| `SLACK_AGENT_URL` | Slack Agent URL for DMs | http://slack-agent:8084 |

### RCA Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `RCA_AUTO_ANALYZE` | Enable auto-analysis | true |
| `RCA_MAX_LOG_CHARS` | Max log characters | 100000 |
| `RCA_MAX_DIFF_CHARS` | Max diff characters | 50000 |
| `SLACK_RELEASE_CHANNEL` | Slack channel for RCA notifications | #release-notifications |

### Slack Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SLACK_MOCK_MODE` | Use mock Slack | true |
| `SLACK_BOT_TOKEN` | Bot OAuth token | - |
| `SLACK_SIGNING_SECRET` | Request signing secret | - |
| `SLACK_APP_TOKEN` | App-level token | - |
| `ORCHESTRATOR_URL` | Orchestrator URL | http://orchestrator:8080 |
| `JIRA_AGENT_URL` | Jira Agent URL (for hygiene fixes) | http://jira-agent:8081 |

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Orchestrator
curl http://localhost:8080/health

# Admin Dashboard
curl http://localhost:8088/health

# Jira Hygiene Agent
curl http://localhost:8005/health

# RCA Agent
curl http://localhost:8006/health

# Expected response:
# {"status": "healthy", "service": "...", "mock_mode": true}
```

### 2. LLM Connection Test

```bash
# Test via Admin Dashboard API
curl -X POST http://localhost:8088/llm/test

# Expected response:
# {"status": "connected", "provider": "openai", "model": "gpt-4o", "latency_ms": 145}
```

### 3. MCP Tool Discovery

```bash
# List all discovered MCP tools
curl http://localhost:8080/tools

# Expected response:
# {"tools": ["get_ticket", "search_tickets", "analyze_build_failure", ...]}
```

### 4. Hygiene Agent Scheduler

```bash
# Check scheduler status
curl http://localhost:8005/status

# Expected: scheduler.running = true, next_run set
```

### 5. Test Hygiene Check

```bash
# Manual hygiene check (dry run)
curl -X POST http://localhost:8005/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": false, "dry_run": true}'
```

### 6. Test LangGraph Execution

```bash
# Execute a query via LangGraph
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the release status for v2.0?"}'
```

### 7. Slack Integration

1. Send `/nexus help` in Slack
2. Verify bot responds with command list
3. Test `/nexus status v1.0`

### 8. Grafana Dashboards

1. Access Grafana at http://localhost:3000
2. Import `infrastructure/grafana/dashboard.json`
3. Verify metrics are flowing

---

## Troubleshooting

### LLM Provider Issues

```bash
# Check LLM configuration
curl http://localhost:8088/llm/config

# Test LLM connection
curl -X POST http://localhost:8088/llm/test

# Common issues:
# - Invalid API key: Verify in Admin Dashboard
# - Rate limit: Switch to different provider
# - Model not found: Check model name is correct
```

### MCP Connection Issues

```bash
# Check MCP server status
curl http://localhost:8001/health  # Jira Agent
curl http://localhost:8005/health  # Hygiene Agent
curl http://localhost:8006/health  # RCA Agent

# Test SSE connection
curl -N http://localhost:8001/sse

# Common issues:
# - Connection refused: Agent container not running
# - SSE timeout: Network issues
# - Tool not found: Agent not exposing tool
```

### Hygiene Agent Not Sending Notifications

```bash
# Check if Slack Agent is reachable
curl http://slack-agent:8084/health

# Check Hygiene Agent logs
kubectl logs -l app.kubernetes.io/component=jira-hygiene-agent

# Common issues:
# - SLACK_AGENT_URL not configured
# - User email doesn't match Jira email
# - Slack DM permissions not granted
```

### LangGraph State Issues

```bash
# Check PostgreSQL connection
kubectl logs -l app.kubernetes.io/component=orchestrator | grep postgres

# Verify checkpointer is configured
# LANGGRAPH_CHECKPOINTER should be set

# Common issues:
# - State not persisting: Check POSTGRES_URL
# - Thread not found: Thread ID expired
```

### Scheduler Not Running

```bash
# Check scheduler status
curl http://localhost:8005/status

# Verify timezone configuration
# Check APScheduler logs in agent output
```

### Modal Not Opening on Button Click

```bash
# Check Slack Agent interaction logs
kubectl logs -l app.kubernetes.io/component=slack-agent | grep interactions

# Common issues:
# - Slack App not configured for interactivity
# - Request URL not set in Slack App settings
# - Trigger ID expired (clicks must be handled within 3 seconds)
```

### Jira Updates Failing

```bash
# Check Jira Agent logs
kubectl logs -l app.kubernetes.io/component=jira-agent

# Test Jira connectivity
curl http://localhost:8001/health

# Verify credentials
# Check Jira API token permissions
```

### Memory Issues

```bash
# Check pod memory usage
kubectl top pods -l app.kubernetes.io/name=nexus-stack

# Increase limits if needed
helm upgrade nexus . --set orchestrator.resources.limits.memory=2Gi
```

---

## Rollback Procedure

```bash
# List Helm releases
helm history nexus

# Rollback to previous version
helm rollback nexus 1

# Verify rollback
kubectl rollout status deployment/nexus-orchestrator
```

---

## Monitoring Alerts

### Recommended Alertmanager Rules

```yaml
groups:
  - name: nexus-alerts
    rules:
      - alert: HygieneScoreLow
        expr: nexus_project_hygiene_score < 50
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Project hygiene score is below 50%"
          
      - alert: AgentDown
        expr: up{job=~"nexus-.*"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Nexus agent is down"
          
      - alert: HighLLMCost
        expr: increase(nexus_llm_cost_dollars_total[1h]) > 10
        labels:
          severity: warning
        annotations:
          summary: "LLM costs exceeded $10 in the last hour"
          
      - alert: MCPServerDisconnected
        expr: nexus_mcp_server_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MCP server disconnected"
          
      - alert: LangGraphIterationLimit
        expr: nexus_langgraph_iteration_count > 8
        labels:
          severity: warning
        annotations:
          summary: "LangGraph execution approaching iteration limit"
```

---

## Security Checklist

- [ ] JWT secret is strong (32+ characters)
- [ ] LLM API keys stored securely (not in code)
- [ ] All API tokens have minimal required permissions
- [ ] Secrets are managed via Kubernetes Secrets or external vault
- [ ] Network policies restrict inter-pod communication
- [ ] Ingress has TLS enabled
- [ ] Pod security policies are configured
- [ ] Audit logging is enabled
- [ ] Regular credential rotation is scheduled
- [ ] MCP endpoints are not publicly exposed

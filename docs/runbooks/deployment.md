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
| LLM Provider | API Key | Orchestrator |

---

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot
```

### 2. Set Up Python Environment

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

### 3. Run Services Locally

```bash
# Terminal 1: Orchestrator
cd services/orchestrator
uvicorn main:app --reload --port 8080

# Terminal 2: Jira Agent
cd services/agents/jira_agent
uvicorn main:app --reload --port 8081

# Terminal 3: Jira Hygiene Agent
cd services/agents/jira_hygiene_agent
uvicorn main:app --reload --port 8005

# ... repeat for other agents
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

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Service Endpoints

| Service | URL |
|---------|-----|
| Orchestrator | http://localhost:8080 |
| Jira Agent | http://localhost:8081 |
| Git/CI Agent | http://localhost:8082 |
| Reporting Agent | http://localhost:8083 |
| Slack Agent | http://localhost:8084 |
| **Jira Hygiene Agent** | **http://localhost:8005** |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

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
  LLM_API_KEY: "your-llm-api-key"
  JIRA_URL: "https://your-company.atlassian.net"
  JIRA_USERNAME: "your-email@company.com"
  JIRA_API_TOKEN: "your-jira-api-token"
  GITHUB_TOKEN: "ghp_your-github-token"
  JENKINS_URL: "https://jenkins.company.com"
  JENKINS_USERNAME: "jenkins-user"
  JENKINS_API_TOKEN: "jenkins-api-token"
  CONFLUENCE_URL: "https://your-company.atlassian.net/wiki"
  CONFLUENCE_USERNAME: "your-email@company.com"
  CONFLUENCE_API_TOKEN: "your-confluence-token"
  SLACK_BOT_TOKEN: "xoxb-your-bot-token"
  SLACK_SIGNING_SECRET: "your-signing-secret"
  SLACK_APP_TOKEN: "xapp-your-app-token"
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
  --set global.imageTag=v1.1.0

# Wait for deployment
kubectl rollout status deployment/nexus-orchestrator
kubectl rollout status deployment/nexus-jira-hygiene-agent
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
```

---

## Configuration Reference

### Orchestrator Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment | development |
| `LLM_PROVIDER` | LLM backend (google/openai/mock) | mock |
| `LLM_MODEL` | LLM model name | gemini-2.0-flash |
| `LLM_API_KEY` | API key for LLM | - |
| `LLM_TEMPERATURE` | Generation temperature | 0.7 |
| `LLM_MAX_TOKENS` | Max output tokens | 4096 |
| `MEMORY_BACKEND` | Vector store (chromadb/pgvector/mock) | mock |
| `MAX_REACT_ITERATIONS` | Max reasoning steps | 10 |
| `ORCHESTRATOR_URL` | Self URL for agents | http://localhost:8080 |
| `RECOMMENDATIONS_ENABLED` | Enable AI recommendations | true |

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

# Jira Hygiene Agent
curl http://localhost:8005/health

# Expected response:
# {"status": "healthy", "service": "...", "mock_mode": true}
```

### 2. Hygiene Agent Scheduler

```bash
# Check scheduler status
curl http://localhost:8005/status

# Expected: scheduler.running = true, next_run set
```

### 3. Test Hygiene Check

```bash
# Manual hygiene check (dry run)
curl -X POST http://localhost:8005/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": false, "dry_run": true}'
```

### 4. Slack Integration

1. Send `/nexus help` in Slack
2. Verify bot responds with command list
3. Test `/nexus status v1.0`

### 5. Grafana Dashboards

1. Access Grafana at http://localhost:3000
2. Import `infrastructure/grafana/dashboard.json`
3. Verify metrics are flowing

---

## Troubleshooting

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
curl http://localhost:8081/health

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
```

---

## Security Checklist

- [ ] JWT secret is strong (32+ characters)
- [ ] All API tokens have minimal required permissions
- [ ] Secrets are managed via Kubernetes Secrets or external vault
- [ ] Network policies restrict inter-pod communication
- [ ] Ingress has TLS enabled
- [ ] Pod security policies are configured
- [ ] Audit logging is enabled
- [ ] Regular credential rotation is scheduled

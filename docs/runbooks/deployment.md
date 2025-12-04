# Deployment Runbook

This runbook provides step-by-step instructions for deploying Nexus to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Cloud Deployment (Render + Vercel)](#cloud-deployment-render--vercel)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Authentication Configuration](#authentication-configuration)
7. [Configuration Reference](#configuration-reference)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Troubleshooting](#troubleshooting)

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
- Checks all prerequisites (Python, Docker, etc.)
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

#### 3. Run Services Locally

```bash
# Terminal 1: Orchestrator
cd services/orchestrator
uvicorn main:app --reload --port 8080

# Terminal 2: Jira Agent
cd services/agents/jira_agent
uvicorn main:app --reload --port 8081

# Terminal 3: Jira Hygiene Agent
cd services/agents/jira_hygiene_agent
uvicorn main:app --reload --port 8085

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

> 📖 **New to Docker?** See our [Docker for Beginners Guide](../docker-for-beginners.md) for a visual, beginner-friendly explanation.

### Docker Architecture (v2.5.0)

Nexus uses optimized multi-stage Dockerfiles with modern best practices:

| Dockerfile | Purpose | Key Features |
|------------|---------|--------------|
| `Dockerfile.base` | Shared foundation | Non-root user, Python health check |
| `Dockerfile.orchestrator` | Central brain | 3-stage build, UV package manager |
| `Dockerfile.agent` | All specialist agents | Build args for agent selection |
| `Dockerfile.admin-dashboard` | Web UI | React frontend + FastAPI backend |
| `Dockerfile.analytics` | Analytics service | Optimized for data processing |
| `Dockerfile.webhooks` | Event delivery | High-throughput optimized |

**Key Optimizations:**
- 🚀 **UV Package Manager** - 10x faster than pip
- 📦 **Multi-stage builds** - 85% smaller images (~150MB vs ~1.2GB)
- 🔒 **Non-root containers** - All services run as UID 1000
- 🏥 **Python health checks** - No curl dependency
- 📋 **OCI labels** - Standard metadata

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
vim .env
```

### 2. Start Services

```bash
# Start all services (uses docker-compose.yml in infrastructure/docker/)
cd infrastructure/docker
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker compose ps
```

### 3. Service Endpoints

| Service | URL |
|---------|-----|
| Orchestrator | http://localhost:8080 |
| Jira Agent | http://localhost:8081 |
| Git/CI Agent | http://localhost:8082 |
| Reporting Agent | http://localhost:8083 |
| Slack Agent | http://localhost:8084 |
| **Jira Hygiene Agent** | **http://localhost:8085** |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

### 4. Stop Services

```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

---

## Cloud Deployment (Render + Vercel)

For production cloud hosting, deploy the backend to Render and frontend to Vercel.

### Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Vercel (CDN)      │     │   Render (Cloud)    │
│                     │     │                     │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │  React App    │  │────▶│  │  FastAPI      │  │
│  │  (Frontend)   │  │ API │  │  (Backend)    │  │
│  └───────────────┘  │     │  └───────────────┘  │
│                     │     │         │           │
└─────────────────────┘     │         ▼           │
                            │  ┌───────────────┐  │
                            │  │  Redis        │  │
                            │  │  (Optional)   │  │
                            │  └───────────────┘  │
                            └─────────────────────┘
```

### 1. Deploy Backend to Render

#### Option A: Blueprint (Recommended)

The repository includes a `render.yaml` Blueprint for one-click deployment:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render auto-detects `render.yaml`
5. Review and click **"Apply"**

#### Option B: Manual Setup

1. Create a new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `nexus-admin-api` |
| **Region** | Oregon (or closest) |
| **Branch** | `main` |
| **Root Directory** | `.` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r services/admin_dashboard/backend/requirements.txt` |
| **Start Command** | `cd services/admin_dashboard/backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. Add Environment Variables:

```bash
PYTHONPATH=/opt/render/project/src/shared
NEXUS_ENV=production
NEXUS_RBAC_ENABLED=true
NEXUS_JWT_SECRET=<generate-secure-secret>
NEXUS_ADMIN_EMAIL=admin@nexus.dev
NEXUS_CORS_ORIGINS=https://your-app.vercel.app
```

### 2. Deploy Frontend to Vercel

#### Option A: Using Deployment Script

```bash
# Run automated deployment
python scripts/deploy_frontend.py --env production \
  --api-url https://nexus-admin-api.onrender.com
```

#### Option B: Manual Vercel Deployment

1. Install Vercel CLI:
```bash
npm install -g vercel
vercel login
```

2. Deploy:
```bash
cd services/admin_dashboard/frontend
vercel --yes
```

3. Set Environment Variable:
```bash
vercel env add VITE_API_URL production
# Enter: https://nexus-admin-api.onrender.com
```

4. Redeploy with env:
```bash
vercel --prod
```

### 3. Configure CORS

Update Render backend with your Vercel URL:

```bash
# In Render Dashboard → Environment
NEXUS_CORS_ORIGINS=https://your-app.vercel.app,https://*.vercel.app
NEXUS_FRONTEND_URL=https://your-app.vercel.app
```

### 4. Verify Deployment

```bash
# Test backend health
curl https://nexus-admin-api.onrender.com/health

# Test frontend (should load login page)
open https://your-app.vercel.app
```

### Production URLs

| Service | URL |
|---------|-----|
| **Backend API** | `https://nexus-admin-api.onrender.com` |
| **Frontend UI** | `https://your-app.vercel.app` |
| **API Docs** | `https://nexus-admin-api.onrender.com/docs` |

---

## Authentication Configuration

### SSO Provider Setup

#### Okta Configuration

1. Create an OIDC Application in Okta Admin Console
2. Set the following:
   - **Sign-in redirect URI**: `https://your-api.onrender.com/auth/callback/okta`
   - **Sign-out redirect URI**: `https://your-app.vercel.app`
   - **Allowed grant types**: Authorization Code

3. Add environment variables:
```bash
NEXUS_SSO_PROVIDER=okta
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret
```

#### Azure AD Configuration

1. Register an application in Azure Portal
2. Configure:
   - **Redirect URI**: `https://your-api.onrender.com/auth/callback/azure_ad`
   - **Supported account types**: Single tenant or Multi-tenant

3. Add environment variables:
```bash
NEXUS_SSO_PROVIDER=azure_ad
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

#### Google OAuth Configuration

1. Create OAuth 2.0 credentials in Google Cloud Console
2. Configure:
   - **Authorized redirect URI**: `https://your-api.onrender.com/auth/callback/google`
   - **Application type**: Web application

3. Add environment variables:
```bash
NEXUS_SSO_PROVIDER=google
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

#### GitHub OAuth Configuration

1. Create an OAuth App in GitHub Developer Settings
2. Configure:
   - **Authorization callback URL**: `https://your-api.onrender.com/auth/callback/github`

3. Add environment variables:
```bash
NEXUS_SSO_PROVIDER=github
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
```

### JWT Configuration

```bash
# Generate a secure secret (at least 32 characters)
NEXUS_JWT_SECRET=$(openssl rand -base64 32)

# Token lifetimes
NEXUS_TOKEN_EXPIRE_MINUTES=60
NEXUS_REFRESH_TOKEN_DAYS=7
```

### Default Admin User

The system creates a default admin user on first startup:

```bash
NEXUS_ADMIN_EMAIL=admin@nexus.dev
```

In development mode, any password works. In production, use SSO.

---

## Kubernetes Deployment

> 📖 **Full Helm Documentation:** See [Helm Chart README](../../infrastructure/k8s/nexus-stack/README.md) for comprehensive deployment guide.

### Helm Chart Overview (v2.4.0)

The enterprise-grade Helm chart includes:

| Feature | Description |
|---------|-------------|
| **High Availability** | Pod anti-affinity, topology spread constraints |
| **Auto-Scaling** | HPA with CPU, memory, and custom metrics |
| **Security** | Network policies, pod security, non-root |
| **Observability** | ServiceMonitors for Prometheus Operator |
| **Secret Management** | External Secrets support (AWS, Vault) |

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

# Development deployment (mock mode, minimal resources)
helm upgrade --install nexus-dev . \
  --namespace nexus-dev \
  --values values-dev.yaml

# Production deployment (full HA, security features)
helm upgrade --install nexus . \
  --namespace nexus \
  --values values-prod.yaml \
  --set global.imageTag=v2.4.0

# Wait for deployment
kubectl rollout status deployment/nexus-orchestrator
kubectl rollout status deployment/nexus-hygiene-agent
```

**Environment-Specific Values Files:**

| File | Purpose | Features |
|------|---------|----------|
| `values.yaml` | Default production config | Full documentation |
| `values-dev.yaml` | Development | Mock mode, single replica, minimal resources |
| `values-prod.yaml` | Production | HA, security, external secrets |

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
curl http://localhost:8085/health

# Expected response:
# {"status": "healthy", "service": "...", "mock_mode": true}
```

### 2. Hygiene Agent Scheduler

```bash
# Check scheduler status
curl http://localhost:8085/status

# Expected: scheduler.running = true, next_run set
```

### 3. Test Hygiene Check

```bash
# Manual hygiene check (dry run)
curl -X POST http://localhost:8085/run-check \
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

### Cloud Deployment Issues

#### Render Health Check Failing

```bash
# Check logs in Render Dashboard → Logs
# Common issues:

# 1. PYTHONPATH not set correctly
# Ensure PYTHONPATH includes shared library path:
PYTHONPATH=/opt/render/project/src/shared

# 2. Missing dependencies
# Check if all packages are installed during build

# 3. Import errors
# Check logs for specific import failures
```

#### Vercel Frontend Can't Connect to Backend

```bash
# 1. Check CORS configuration
# Backend should allow Vercel origin:
NEXUS_CORS_ORIGINS=https://your-app.vercel.app

# 2. Verify API URL in Vercel
vercel env ls
# Should show VITE_API_URL pointing to Render backend

# 3. Check backend is running
curl https://nexus-admin-api.onrender.com/health
```

#### SSO Login Not Working

```bash
# 1. Verify callback URLs match exactly
# Check SSO provider settings for redirect URI

# 2. Check environment variables are set
# Provider-specific client ID and secret

# 3. Check logs for OAuth errors
# Look for "authorization code" or "token exchange" errors

# 4. Verify HTTPS is used for all URLs
# SSO providers require HTTPS for production
```

#### JWT Token Issues

```bash
# 1. Token expired
# Default is 60 minutes; adjust with:
NEXUS_TOKEN_EXPIRE_MINUTES=120

# 2. Invalid signature
# Ensure JWT_SECRET is the same across deployments
# Generate a new one if needed:
openssl rand -base64 32

# 3. Token not included in requests
# Check Authorization header format: "Bearer <token>"
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

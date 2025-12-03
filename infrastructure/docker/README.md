# 🐳 Nexus Docker Infrastructure

> Production-optimized, multi-stage Dockerfiles for the Nexus Release Automation System.

## 📋 Overview

This directory contains highly optimized Docker configurations for all Nexus services. Our Dockerfiles follow modern best practices:

| Feature | Implementation |
|---------|----------------|
| **Multi-stage builds** | 3-stage builds for minimal image size (~150MB) |
| **BuildKit cache mounts** | 10x faster rebuilds with dependency caching |
| **UV package manager** | Rust-based pip alternative (10x faster) |
| **Non-root users** | Security hardening with UID 1000 |
| **Python-native health checks** | No curl dependency needed |
| **OCI-compliant labels** | Standards-compliant image metadata |
| **Graceful shutdown** | Proper SIGTERM handling |
| **Resource limits** | Memory caps for container orchestration |

## 🗂️ File Structure

```
infrastructure/docker/
├── Dockerfile.base           # Shared base image (optional)
├── Dockerfile.orchestrator   # Central orchestrator
├── Dockerfile.agent          # Universal agent (all 6 specialist agents)
├── Dockerfile.admin-dashboard# React + FastAPI dashboard
├── Dockerfile.analytics      # DORA metrics service
├── Dockerfile.webhooks       # Event webhook service
├── docker-compose.yml        # Full development stack
├── prometheus.yml           # Prometheus configuration
├── .dockerignore            # Build context optimization
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.20+
- 8GB+ RAM recommended

### Start All Services

```bash
# Navigate to docker directory
cd infrastructure/docker

# Start the full stack
docker compose up -d

# View logs
docker compose logs -f

# Check health
docker compose ps
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Orchestrator API** | http://localhost:8080 | - |
| **Admin Dashboard** | http://localhost:8088 | - |
| **Grafana** | http://localhost:3000 | admin / nexus_admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger UI** | http://localhost:16686 | - |

## 🏗️ Building Images

### Build All Services

```bash
docker compose build
```

### Build Specific Service

```bash
# Orchestrator
docker compose build orchestrator

# Jira Agent
docker compose build jira-agent

# Admin Dashboard
docker compose build admin-dashboard
```

### Build with No Cache

```bash
docker compose build --no-cache --pull
```

### Build Agent with Custom Args

```bash
docker build \
  --build-arg AGENT_NAME=jira_agent \
  --build-arg AGENT_PORT=8081 \
  -t nexus-jira-agent:latest \
  -f Dockerfile.agent ../..
```

## 📦 Dockerfile Architecture

### Multi-Stage Build Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: UV Package Manager                                │
│  └── Fetch UV binary from ghcr.io/astral-sh/uv             │
├─────────────────────────────────────────────────────────────┤
│  Stage 2: Dependency Builder                                │
│  ├── Install build tools (gcc, libpq-dev)                  │
│  ├── Build wheel files with UV (10x faster than pip)       │
│  └── Compile shared library                                 │
├─────────────────────────────────────────────────────────────┤
│  Stage 3: Production Runtime                                │
│  ├── Minimal base image (python:3.11-slim-bookworm)        │
│  ├── Install only runtime dependencies                      │
│  ├── Copy pre-built wheels (no compilation needed)         │
│  ├── Copy application code                                  │
│  ├── Configure non-root user (UID 1000)                    │
│  └── Set up health checks and entrypoint                   │
└─────────────────────────────────────────────────────────────┘
```

### Image Sizes

| Service | Base | Final | Savings |
|---------|------|-------|---------|
| Orchestrator | ~1.2GB | ~180MB | 85% |
| Agents | ~1.0GB | ~150MB | 85% |
| Admin Dashboard | ~1.5GB | ~200MB | 87% |
| Analytics | ~1.1GB | ~170MB | 85% |
| Webhooks | ~900MB | ~140MB | 84% |

## 🔧 Configuration

### Environment Variables

All services support these common environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXUS_ENV` | Environment (development/production) | `development` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Jaeger endpoint | `http://jaeger:4317` |
| `LLM_PROVIDER` | LLM provider (mock/google/openai) | `mock` |

### Agent-Specific Variables

```bash
# Jira Agent
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=user@example.com
JIRA_API_TOKEN=your-token
JIRA_MOCK_MODE=true

# GitHub Agent
GITHUB_TOKEN=ghp_xxxx
GITHUB_MOCK_MODE=true

# Slack Agent
SLACK_BOT_TOKEN=xoxb-xxxx
SLACK_SIGNING_SECRET=xxxx
SLACK_MOCK_MODE=true
```

## 🛡️ Security Features

### Non-Root User

All containers run as user `nexus` (UID 1000):

```dockerfile
RUN groupadd --gid 1000 nexus \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home nexus
USER nexus
```

### Health Checks (No Curl)

Python-native health checks without external dependencies:

```dockerfile
COPY --chmod=755 <<'EOF' /usr/local/bin/healthcheck
#!/usr/bin/env python3
import sys, urllib.request, urllib.error
try:
    with urllib.request.urlopen("http://localhost:8080/health", timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except: sys.exit(1)
EOF
```

### Resource Limits

Memory limits prevent container escape:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

## 🔄 Development Workflow

### Hot Reload (Development)

For development with hot reload, mount source code:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Rebuild Single Service

```bash
docker compose up -d --build jira-agent
```

### View Service Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f orchestrator

# Last 100 lines
docker compose logs --tail=100 orchestrator
```

### Shell Access

```bash
docker compose exec orchestrator /bin/bash
```

## 📊 Monitoring

### Prometheus Metrics

All services expose metrics at `/metrics`:

```bash
curl http://localhost:8080/metrics
curl http://localhost:8081/metrics
# ... etc
```

### Grafana Dashboards

Pre-configured dashboards available at http://localhost:3000:

- **Nexus Overview** - Service health and request rates
- **LLM Economics** - Token usage and costs
- **Agent Performance** - Latency and error rates

### Jaeger Tracing

Distributed traces at http://localhost:16686

## 🧹 Maintenance

### Clean Up

```bash
# Stop all containers
docker compose down

# Stop and remove volumes
docker compose down -v

# Remove all Nexus images
docker images | grep nexus | awk '{print $3}' | xargs docker rmi

# Full cleanup (careful!)
docker system prune -a --volumes
```

### Update Base Images

```bash
docker compose build --pull --no-cache
```

### Check Image Vulnerabilities

```bash
# Using Trivy
trivy image nexus-orchestrator:latest

# Using Docker Scout
docker scout cves nexus-orchestrator:latest
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs orchestrator

# Check health
docker inspect --format='{{.State.Health.Status}}' nexus-orchestrator
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Use different ports in .env
echo "ORCHESTRATOR_PORT=8090" >> .env
```

### Out of Memory

Increase Docker memory limit or adjust resource limits in docker-compose.yml.

### Build Cache Issues

```bash
# Clear BuildKit cache
docker builder prune -a

# Rebuild without cache
docker compose build --no-cache
```

## 📚 References

- [Docker BuildKit](https://docs.docker.com/build/buildkit/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [OCI Image Spec](https://github.com/opencontainers/image-spec)
- [Container Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)


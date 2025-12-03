# 🚀 Nexus Helm Chart

> Enterprise-grade Kubernetes deployment for Nexus Release Automation System

[![Helm Version](https://img.shields.io/badge/Helm-v3.12+-blue)](https://helm.sh)
[![Kubernetes Version](https://img.shields.io/badge/Kubernetes-v1.23+-green)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Prerequisites](#-prerequisites)
3. [Quick Start](#-quick-start)
4. [Architecture](#-architecture)
5. [Configuration](#-configuration)
6. [Environment-Specific Deployments](#-environment-specific-deployments)
7. [Security](#-security)
8. [Observability](#-observability)
9. [High Availability](#-high-availability)
10. [Troubleshooting](#-troubleshooting)
11. [Upgrading](#-upgrading)

---

## 🎯 Overview

This Helm chart deploys the complete Nexus Release Automation System on Kubernetes with enterprise-grade features:

| Feature | Description |
|---------|-------------|
| **High Availability** | Multi-replica deployments with pod anti-affinity |
| **Auto-Scaling** | HPA with CPU, memory, and custom metrics |
| **Security** | Network policies, pod security, non-root containers |
| **Observability** | Prometheus ServiceMonitors, OpenTelemetry tracing |
| **Secret Management** | External Secrets support (AWS, Vault) |
| **Graceful Shutdown** | Lifecycle hooks with proper drain time |

### Deployed Services

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXUS KUBERNETES DEPLOYMENT                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐                                             │
│  │  Orchestrator │ ← ReAct AI Engine (Port 8080)               │
│  └───────┬───────┘                                             │
│          │                                                      │
│  ┌───────┴───────────────────────────────────────────┐         │
│  │              SPECIALIST AGENTS                     │         │
│  ├────────────┬───────────┬───────────┬─────────────┤         │
│  │ Jira Agent │ Git Agent │ Slack     │ Reporting   │         │
│  │ (8081)     │ (8082)    │ (8084)    │ (8083)      │         │
│  ├────────────┴───────────┼───────────┴─────────────┤         │
│  │ Hygiene Agent (8085)   │ RCA Agent (8006)        │         │
│  └────────────────────────┴─────────────────────────┘         │
│                                                                 │
│  ┌────────────┬────────────┬────────────────────────┐         │
│  │ Analytics  │ Webhooks   │ Admin Dashboard        │         │
│  │ (8086)     │ (8087)     │ (8088)                 │         │
│  └────────────┴────────────┴────────────────────────┘         │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  DATA STORES: Redis • PostgreSQL (pgvector)            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

| Component | Version | Required |
|-----------|---------|----------|
| Kubernetes | ≥ 1.23 | ✅ |
| Helm | ≥ 3.12 | ✅ |
| kubectl | Latest | ✅ |
| cert-manager | ≥ 1.0 | For TLS |
| Ingress Controller | nginx | For external access |
| Prometheus Operator | Latest | For ServiceMonitors |

### Optional Dependencies

```bash
# Add Bitnami repo for Redis and PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add Prometheus community for monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Update repos
helm repo update
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot/infrastructure/k8s
```

### 2. Create Namespace

```bash
kubectl create namespace nexus
```

### 3. Create Secrets (Recommended: Use External Secrets)

```bash
# Create secrets manually for quick start
kubectl create secret generic nexus-orchestrator-secrets \
  --from-literal=NEXUS_JWT_SECRET=$(openssl rand -base64 32) \
  --from-literal=LLM_API_KEY=your-api-key \
  --from-literal=POSTGRES_PASSWORD=your-db-password \
  -n nexus

kubectl create secret generic nexus-jira-secrets \
  --from-literal=JIRA_URL=https://your-company.atlassian.net \
  --from-literal=JIRA_EMAIL=your-email@company.com \
  --from-literal=JIRA_API_TOKEN=your-jira-token \
  -n nexus

# Add more secrets as needed...
```

### 4. Install Dependencies

```bash
# Update dependencies
cd nexus-stack
helm dependency update
```

### 5. Install the Chart

```bash
# Development
helm install nexus . -f values-dev.yaml -n nexus

# Production
helm install nexus . -f values-prod.yaml -n nexus
```

### 6. Verify Installation

```bash
# Check pods
kubectl get pods -n nexus -w

# Check services
kubectl get svc -n nexus

# View installation notes
helm status nexus -n nexus
```

---

## 🏗️ Architecture

### Pod Distribution (Production)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZONE-A                ZONE-B                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Node 1              Node 2              Node 3                │
│   ┌─────────────┐    ┌─────────────┐     ┌─────────────┐       │
│   │Orchestrator │    │Orchestrator │     │Orchestrator │       │
│   │Jira Agent   │    │Git Agent    │     │Slack Agent  │       │
│   │RCA Agent    │    │Analytics    │     │Webhooks     │       │
│   └─────────────┘    └─────────────┘     └─────────────┘       │
│                                                                 │
│   Pod Anti-Affinity ensures spread across nodes and zones       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Network Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Internet   │────▶│   Ingress    │────▶│ Network      │
│              │     │   Controller │     │ Policy       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                     ┌───────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────┐
│                    NEXUS NAMESPACE                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │ Orchestrator│◀─▶│   Agents    │◀─▶│   Database  │   │
│  └─────────────┘   └─────────────┘   └─────────────┘   │
│         │                                    ▲          │
│         └────────────────────────────────────┘          │
│                      Internal Only                      │
└──────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |
| `global.imageTag` | Default image tag | `2.4.0` |
| `global.highAvailability.enabled` | Enable HA features | `true` |
| `orchestrator.replicas` | Orchestrator replicas | `2` |
| `orchestrator.autoscaling.enabled` | Enable HPA | `true` |
| `ingress.enabled` | Enable Ingress | `true` |
| `networkPolicy.enabled` | Enable NetworkPolicies | `true` |
| `serviceMonitor.enabled` | Enable ServiceMonitors | `true` |

### Full Configuration Reference

See [`values.yaml`](values.yaml) for the complete list of configurable parameters.

### Using External Secrets

For production, use External Secrets Operator:

```yaml
orchestrator:
  existingSecret: nexus-orchestrator-secrets
  externalSecrets:
    enabled: true
    secretStoreRef:
      name: aws-secrets-manager
      kind: ClusterSecretStore
    data:
      - secretKey: LLM_API_KEY
        remoteRef:
          key: nexus/prod/llm
          property: api_key
```

---

## 🌍 Environment-Specific Deployments

### Development

```bash
helm install nexus-dev . -f values-dev.yaml -n nexus-dev --create-namespace
```

**Characteristics:**
- Single replicas
- Mock mode enabled
- Minimal resources
- No HA features
- Debug logging

### Staging

```bash
helm install nexus-staging . \
  -f values.yaml \
  --set global.environment=staging \
  --set global.imageTag=staging \
  -n nexus-staging
```

### Production

```bash
helm install nexus . -f values-prod.yaml -n nexus-prod
```

**Characteristics:**
- Multi-replica (3+)
- Full HA enabled
- Production resources
- Network policies
- External secrets
- Full observability

---

## 🔒 Security

### Pod Security Standards

All pods run with:
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped capabilities
- Seccomp profiles

### Network Policies

Network policies enforce:
- Default deny all ingress/egress
- Explicit allow rules for:
  - Inter-service communication
  - Ingress controller
  - Prometheus scraping
  - External APIs (HTTPS only)

### Secrets Management

**Recommended:** Use External Secrets Operator with:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- GCP Secret Manager

```yaml
# Example ExternalSecret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: nexus-orchestrator-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: nexus-orchestrator-secrets
  data:
    - secretKey: LLM_API_KEY
      remoteRef:
        key: nexus/prod/llm-api-key
```

---

## 📊 Observability

### Prometheus Metrics

ServiceMonitors are created for all services when `serviceMonitor.enabled=true`.

**Key Metrics:**
- `nexus_query_total` - Total queries processed
- `nexus_llm_tokens_total` - LLM token usage
- `nexus_tool_calls_total` - Tool invocations
- `nexus_hygiene_score` - Jira hygiene scores
- `nexus_rca_analysis_total` - RCA analyses performed

### Grafana Dashboards

Import dashboards from:
```
infrastructure/grafana/dashboard.json
```

### OpenTelemetry Tracing

Enable distributed tracing:

```yaml
observability:
  tracing:
    enabled: true
    endpoint: "http://jaeger-collector:4317"
    samplingRatio: 0.1  # 10% in production
```

---

## 🔄 High Availability

### Pod Distribution

- **Pod Anti-Affinity:** Spreads pods across nodes and zones
- **Topology Spread Constraints:** Ensures even distribution
- **PodDisruptionBudgets:** Protects against voluntary disruptions

### Auto-Scaling

```yaml
orchestrator:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 60
    targetMemoryUtilizationPercentage: 70
    customMetrics:
      - type: Pods
        pods:
          metric:
            name: nexus_query_rate
          target:
            type: AverageValue
            averageValue: 100
```

### Database HA

For production, enable Redis Sentinel and PostgreSQL replication:

```yaml
redis:
  architecture: replication
  sentinel:
    enabled: true
    quorum: 2

postgresql:
  readReplicas:
    replicaCount: 2
```

---

## 🔧 Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n nexus

# Check events
kubectl get events -n nexus --sort-by='.lastTimestamp'
```

#### Database Connection Issues

```bash
# Check PostgreSQL
kubectl exec -it nexus-postgresql-0 -n nexus -- psql -U nexus -d nexus -c "SELECT 1"

# Check Redis
kubectl exec -it nexus-redis-master-0 -n nexus -- redis-cli ping
```

#### Health Check Failures

```bash
# Check orchestrator health
kubectl exec -it deploy/nexus-orchestrator -n nexus -- curl localhost:8080/health
```

### Logs

```bash
# Orchestrator logs
kubectl logs -f deploy/nexus-orchestrator -n nexus

# All Nexus logs
kubectl logs -l app.kubernetes.io/part-of=nexus -n nexus --tail=100
```

---

## ⬆️ Upgrading

### Minor Updates

```bash
helm upgrade nexus . -f values-prod.yaml -n nexus
```

### Major Updates

1. Review CHANGELOG for breaking changes
2. Backup databases
3. Test in staging first
4. Perform rolling upgrade:

```bash
# Dry-run first
helm upgrade nexus . -f values-prod.yaml -n nexus --dry-run

# Apply upgrade
helm upgrade nexus . -f values-prod.yaml -n nexus
```

### Rollback

```bash
# List revisions
helm history nexus -n nexus

# Rollback to previous
helm rollback nexus -n nexus
```

---

## 📚 Additional Resources

- [Main Documentation](../../../docs/)
- [API Reference](../../../docs/api-testing-guide.md)
- [Architecture Guide](../../../docs/architecture.md)
- [Docker Documentation](../docker/README.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes to chart
4. Test with `helm lint` and `helm template`
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](../../../LICENSE) for details.


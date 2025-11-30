# Deployment Runbook

This runbook covers deploying the Nexus Release Automation System to production.

## Prerequisites

- Kubernetes cluster (1.24+)
- Helm 3.x
- kubectl configured
- Container registry access
- External secrets configured

## Quick Deploy

```bash
# Add Helm dependencies
helm dependency update infrastructure/k8s/nexus-stack

# Deploy with production values
helm upgrade --install nexus infrastructure/k8s/nexus-stack \
  --namespace nexus \
  --create-namespace \
  --values production-values.yaml
```

## Step-by-Step Deployment

### 1. Build and Push Images

```bash
# Build orchestrator
docker build -t nexus/orchestrator:v1.0.0 \
  -f infrastructure/docker/Dockerfile.orchestrator .

# Build agents
for agent in jira_agent git_ci_agent reporting_agent slack_agent; do
  docker build -t nexus/${agent}:v1.0.0 \
    --build-arg AGENT_NAME=${agent} \
    -f infrastructure/docker/Dockerfile.generic-agent .
done

# Push to registry
docker push nexus/orchestrator:v1.0.0
# ... push all agent images
```

### 2. Configure Secrets

Create a `secrets.yaml` for production:

```yaml
orchestrator:
  secrets:
    NEXUS_JWT_SECRET: "<generate-strong-secret>"
    LLM_API_KEY: "<your-gemini-or-openai-key>"
    POSTGRES_PASSWORD: "<db-password>"

jiraAgent:
  secrets:
    JIRA_URL: "https://your-company.atlassian.net"
    JIRA_USERNAME: "automation@company.com"
    JIRA_API_TOKEN: "<jira-api-token>"

gitCiAgent:
  secrets:
    GITHUB_TOKEN: "<github-pat>"
    JENKINS_URL: "https://jenkins.company.com"
    JENKINS_USERNAME: "automation"
    JENKINS_API_TOKEN: "<jenkins-token>"

slackAgent:
  secrets:
    SLACK_BOT_TOKEN: "xoxb-..."
    SLACK_SIGNING_SECRET: "<signing-secret>"
```

### 3. Deploy with Helm

```bash
helm upgrade --install nexus infrastructure/k8s/nexus-stack \
  --namespace nexus \
  --create-namespace \
  --set global.imageTag=v1.0.0 \
  --values secrets.yaml \
  --values production-overrides.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n nexus

# Check services
kubectl get svc -n nexus

# Verify health
kubectl exec -it deploy/nexus-orchestrator -n nexus \
  -- curl localhost:8080/health
```

## Configuration

### Production Overrides

`production-overrides.yaml`:

```yaml
global:
  environment: production
  imageTag: v1.0.0

orchestrator:
  replicas: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10

ingress:
  enabled: true
  hosts:
    - host: nexus.company.com
      paths:
        - path: /api
          service: orchestrator
          port: 8080
        - path: /slack
          service: slack-agent
          port: 8084
  tls:
    - secretName: nexus-tls
      hosts:
        - nexus.company.com
```

## Rollback

```bash
# View history
helm history nexus -n nexus

# Rollback to previous
helm rollback nexus -n nexus

# Rollback to specific revision
helm rollback nexus 3 -n nexus
```

## Monitoring

After deployment, verify metrics are flowing:

1. Access Grafana: `https://grafana.company.com`
2. Import dashboard from `infrastructure/grafana/dashboard.json`
3. Verify all panels are populating

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl describe pod <pod-name> -n nexus

# Check logs
kubectl logs <pod-name> -n nexus --previous
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl run psql-test --rm -it --image=postgres:16 \
  --env="PGPASSWORD=<password>" \
  -- psql -h nexus-postgresql -U nexus -d nexus -c "SELECT 1"
```

### Memory Issues

If pods are OOMKilled, increase limits:

```yaml
orchestrator:
  resources:
    limits:
      memory: "4Gi"
```


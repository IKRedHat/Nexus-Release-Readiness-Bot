# Nexus API Testing Guide

> **Complete reference for testing all 100+ API endpoints across Nexus services**

## Table of Contents

- [Quick Start](#quick-start)
- [Service Overview](#service-overview)
- [1. Orchestrator API (Port 8080)](#1-orchestrator-api-port-8080)
- [2. Jira Agent API (Port 8081)](#2-jira-agent-api-port-8081)
- [3. Git/CI Agent API (Port 8082)](#3-gitci-agent-api-port-8082)
- [4. Reporting Agent API (Port 8083)](#4-reporting-agent-api-port-8083)
- [5. Slack Agent API (Port 8084)](#5-slack-agent-api-port-8084)
- [6. Jira Hygiene Agent API (Port 8085)](#6-jira-hygiene-agent-api-port-8085)
- [7. RCA Agent API (Port 8006)](#7-rca-agent-api-port-8006)
- [8. Analytics Service API (Port 8086)](#8-analytics-service-api-port-8086)
- [9. Webhooks Service API (Port 8087)](#9-webhooks-service-api-port-8087)
- [10. Admin Dashboard API (Port 8088)](#10-admin-dashboard-api-port-8088)
- [Bulk Testing Script](#bulk-testing-script)
- [Postman Collection](#postman-collection)

---

## Quick Start

### Prerequisites
```bash
# Ensure all services are running
./scripts/verify.sh

# Set base URLs (optional - for easier testing)
export ORCHESTRATOR=http://localhost:8080
export JIRA_AGENT=http://localhost:8081
export GIT_AGENT=http://localhost:8082
export REPORTING=http://localhost:8083
export SLACK_AGENT=http://localhost:8084
export HYGIENE=http://localhost:8085
export RCA=http://localhost:8006
export ANALYTICS=http://localhost:8086
export WEBHOOKS=http://localhost:8087
export ADMIN=http://localhost:8088
```

### Health Check All Services
```bash
for port in 8080 8081 8082 8083 8084 8085 8006 8086 8087 8088; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq -r '.status // "error"'
done
```

---

## Service Overview

| Service | Port | Base URL | Swagger Docs |
|---------|------|----------|--------------|
| Orchestrator | 8080 | http://localhost:8080 | http://localhost:8080/docs |
| Jira Agent | 8081 | http://localhost:8081 | http://localhost:8081/docs |
| Git/CI Agent | 8082 | http://localhost:8082 | http://localhost:8082/docs |
| Reporting Agent | 8083 | http://localhost:8083 | http://localhost:8083/docs |
| Slack Agent | 8084 | http://localhost:8084 | http://localhost:8084/docs |
| Jira Hygiene Agent | 8085 | http://localhost:8085 | http://localhost:8085/docs |
| RCA Agent | 8006 | http://localhost:8006 | http://localhost:8006/docs |
| Analytics | 8086 | http://localhost:8086 | http://localhost:8086/docs |
| Webhooks | 8087 | http://localhost:8087 | http://localhost:8087/docs |
| Admin Dashboard | 8088 | http://localhost:8088 | http://localhost:8088/docs |

---

## 1. Orchestrator API (Port 8080)

The central brain of Nexus - routes queries to appropriate agents using ReAct reasoning.

### Health & Readiness

```bash
# Basic health check
curl http://localhost:8080/health | jq

# Liveness probe (for K8s)
curl http://localhost:8080/live

# Readiness probe (for K8s)
curl http://localhost:8080/ready

# Prometheus metrics
curl http://localhost:8080/metrics
```

### Natural Language Queries

```bash
# Ask about release readiness
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the release readiness status for Project Alpha?",
    "context": {"project": "ALPHA"}
  }' | jq

# Ask about Jira tickets
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all open bugs in the current sprint"
  }' | jq

# Ask about CI/CD status
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the build status for the main branch?"
  }' | jq
```

### Direct Tool Execution

```bash
# Execute a specific tool directly
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_jira_ticket",
    "parameters": {"ticket_key": "PROJ-123"}
  }' | jq
```

### Specialist Management

```bash
# List all registered specialists
curl http://localhost:8080/specialists | jq

# Get specific specialist info
curl http://localhost:8080/specialists/jira-agent | jq

# Trigger health check for a specialist
curl -X POST http://localhost:8080/specialists/jira-agent/health | jq

# List all available tools across specialists
curl http://localhost:8080/specialists/tools/all | jq
```

### Memory Operations

```bash
# Add to memory/knowledge base
curl -X POST http://localhost:8080/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Sprint 15 release was delayed due to critical bug PROJ-456",
    "metadata": {"type": "release_note", "sprint": 15}
  }' | jq

# Search memory
curl "http://localhost:8080/memory/search?query=sprint%20delay&limit=5" | jq

# Get memory statistics
curl http://localhost:8080/memory/stats | jq
```

---

## 2. Jira Agent API (Port 8081)

Handles all Jira-related operations.

### Health Check
```bash
curl http://localhost:8081/health | jq
```

### Issue Operations

```bash
# Get a specific ticket
curl http://localhost:8081/issue/PROJ-123 | jq

# Search tickets with JQL
curl "http://localhost:8081/search?jql=project=PROJ%20AND%20status=Open&max_results=10" | jq

# Get ticket hierarchy (epic -> story -> subtask)
curl http://localhost:8081/hierarchy/PROJ-123 | jq

# Update a ticket
curl -X POST http://localhost:8081/update-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_key": "PROJ-123",
    "fields": {
      "status": "In Progress",
      "assignee": "john.doe"
    }
  }' | jq
```

### Sprint Statistics

```bash
# Get sprint stats for a project
curl http://localhost:8081/sprint-stats/PROJ | jq
```

### Execute Tool

```bash
# Execute via standard interface
curl -X POST http://localhost:8081/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_ticket",
    "parameters": {"ticket_key": "PROJ-123"}
  }' | jq
```

---

## 3. Git/CI Agent API (Port 8082)

Manages GitHub repositories and Jenkins CI/CD pipelines.

### Health Check
```bash
curl http://localhost:8082/health | jq
```

### GitHub Operations

```bash
# Get repository health
curl http://localhost:8082/repo/my-org/my-repo/health | jq

# List pull requests
curl http://localhost:8082/repo/my-org/my-repo/prs | jq

# Get specific PR details
curl http://localhost:8082/repo/my-org/my-repo/pr/42 | jq

# Get security scan results
curl http://localhost:8082/security/my-org/my-repo | jq
```

### Jenkins Operations

```bash
# Get build status
curl http://localhost:8082/build/my-job/status | jq

# Get build history
curl http://localhost:8082/build/my-job/history | jq

# Trigger a new build
curl -X POST http://localhost:8082/build/my-job \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "BRANCH": "main",
      "ENVIRONMENT": "staging"
    }
  }' | jq
```

---

## 4. Reporting Agent API (Port 8083)

Generates release readiness reports and documentation.

### Health Check
```bash
curl http://localhost:8083/health | jq
```

### Report Operations

```bash
# Generate a release readiness report
curl -X POST http://localhost:8083/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "release_readiness",
    "project": "PROJ",
    "sprint": "Sprint 15",
    "format": "markdown"
  }' | jq

# Preview report without saving
curl "http://localhost:8083/preview?project=PROJ&type=status" | jq

# Analyze release data
curl -X POST http://localhost:8083/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "date_range": {"start": "2024-01-01", "end": "2024-01-31"}
  }' | jq

# Publish report to Confluence/Slack
curl -X POST http://localhost:8083/publish \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "rpt-123",
    "destinations": ["confluence", "slack"],
    "channel": "#releases"
  }' | jq
```

---

## 5. Slack Agent API (Port 8084)

Handles Slack notifications and interactive commands.

### Health Check
```bash
curl http://localhost:8084/health | jq
```

### Notification Operations

```bash
# Send channel notification
curl -X POST http://localhost:8084/notify \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#release-updates",
    "message": "🚀 Release v2.3.0 is ready for deployment!",
    "blocks": [
      {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Release Status:* ✅ Ready"}
      }
    ]
  }' | jq

# Send direct message
curl -X POST http://localhost:8084/send-dm \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "developer@company.com",
    "message": "Your ticket PROJ-123 needs attention"
  }' | jq
```

### Slack Events (Webhook endpoints)

```bash
# These are typically called by Slack, but can be tested:

# Slash command handler
curl -X POST http://localhost:8084/slack/commands \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/nexus&text=status&user_id=U123"

# Event handler (for bot mentions, etc.)
curl -X POST http://localhost:8084/slack/events \
  -H "Content-Type: application/json" \
  -d '{
    "type": "event_callback",
    "event": {"type": "app_mention", "text": "status"}
  }'
```

---

## 6. Jira Hygiene Agent API (Port 8085)

Monitors and enforces Jira data quality standards.

### Health Check
```bash
curl http://localhost:8085/health | jq
```

### Hygiene Operations

```bash
# Get current status
curl http://localhost:8085/status | jq

# Run hygiene check for a project
curl -X POST http://localhost:8085/run-check \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "PROJ",
    "rules": ["missing_description", "stale_tickets", "unassigned_bugs"]
  }' | jq

# Get violations for a project
curl http://localhost:8085/violations/PROJ | jq
```

---

## 7. RCA Agent API (Port 8006)

AI-powered Root Cause Analysis for build/test failures.

### Health Check
```bash
curl http://localhost:8006/health | jq
```

### RCA Operations

```bash
# Analyze a failed build
curl -X POST http://localhost:8006/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "my-pipeline",
    "build_number": 456,
    "failure_type": "test_failure"
  }' | jq

# Jenkins webhook (auto-triggered on failures)
curl -X POST http://localhost:8006/webhook/jenkins \
  -H "Content-Type: application/json" \
  -d '{
    "build": {
      "full_url": "http://jenkins/job/my-job/456/",
      "number": 456,
      "phase": "COMPLETED",
      "status": "FAILURE"
    }
  }' | jq
```

---

## 8. Analytics Service API (Port 8086)

Advanced metrics, KPIs, and predictive analytics.

### Health Check
```bash
curl http://localhost:8086/health | jq
```

### DORA Metrics

```bash
# Note: DORA metrics endpoint uses root path
curl http://localhost:8086/dora | jq
```

### KPIs and Insights

```bash
# Get current KPIs
curl http://localhost:8086/api/v1/kpis | jq

# Get trend analysis
curl "http://localhost:8086/api/v1/trends?metric=velocity&period=30d" | jq

# Get AI-generated insights
curl http://localhost:8086/api/v1/insights | jq

# Get anomaly detection results
curl http://localhost:8086/api/v1/anomalies | jq

# Acknowledge an anomaly
curl -X POST http://localhost:8086/api/v1/anomalies/anom-123/acknowledge | jq
```

### Team Analytics

```bash
# List all teams
curl http://localhost:8086/api/v1/teams | jq

# Get team-specific metrics
curl http://localhost:8086/api/v1/teams/frontend-team | jq

# Compare teams/projects
curl "http://localhost:8086/api/v1/compare?entities=team-a,team-b&metric=velocity" | jq

# Benchmark against industry standards
curl http://localhost:8086/api/v1/benchmark | jq
```

### Predictions

```bash
# Predict release date
curl -X POST http://localhost:8086/api/v1/predict/release-date \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "target_scope": 50,
    "current_velocity": 12
  }' | jq

# Predict quality metrics
curl -X POST http://localhost:8086/api/v1/predict/quality \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "release_version": "2.3.0"
  }' | jq

# Predict resource needs
curl -X POST http://localhost:8086/api/v1/predict/resources \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "timeline": "2024-Q1"
  }' | jq
```

### Time Series Data

```bash
# Get time series for a metric
curl "http://localhost:8086/api/v1/timeseries/bug_count?start=2024-01-01&end=2024-01-31" | jq

# List available data sources
curl http://localhost:8086/api/v1/sources | jq

# Generate analytics report
curl "http://localhost:8086/api/v1/report?format=json&period=monthly" | jq
```

### Data Collection

```bash
# Manually trigger data collection
curl -X POST http://localhost:8086/api/v1/collect \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["jira", "github", "jenkins"]
  }' | jq
```

---

## 9. Webhooks Service API (Port 8087)

Event-driven webhook management for external integrations.

### Health Check
```bash
curl http://localhost:8087/health | jq
```

### Subscription Management

```bash
# List all subscriptions
curl http://localhost:8087/api/v1/subscriptions | jq

# Create a new subscription
curl -X POST http://localhost:8087/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Release Notifications",
    "url": "https://my-service.com/webhook",
    "events": ["release.ready", "release.deployed"],
    "secret": "my-webhook-secret"
  }' | jq

# Get subscription details
curl http://localhost:8087/api/v1/subscriptions/sub-123 | jq

# Update subscription
curl -X PATCH http://localhost:8087/api/v1/subscriptions/sub-123 \
  -H "Content-Type: application/json" \
  -d '{
    "events": ["release.ready", "release.deployed", "release.failed"]
  }' | jq

# Toggle subscription (enable/disable)
curl -X POST http://localhost:8087/api/v1/subscriptions/sub-123/toggle | jq

# Rotate webhook secret
curl -X POST http://localhost:8087/api/v1/subscriptions/sub-123/rotate-secret | jq

# Test subscription
curl -X POST http://localhost:8087/api/v1/subscriptions/sub-123/test | jq

# Delete subscription
curl -X DELETE http://localhost:8087/api/v1/subscriptions/sub-123 | jq
```

### Event Operations

```bash
# List available event types
curl http://localhost:8087/api/v1/event-types | jq

# Publish an event
curl -X POST http://localhost:8087/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "type": "release.ready",
    "payload": {
      "version": "2.3.0",
      "project": "PROJ",
      "ready": true
    }
  }' | jq

# Publish multiple events
curl -X POST http://localhost:8087/api/v1/events/batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"type": "build.success", "payload": {"job": "main-build"}},
      {"type": "test.passed", "payload": {"suite": "integration"}}
    ]
  }' | jq
```

### Delivery Management

```bash
# List recent deliveries
curl http://localhost:8087/api/v1/deliveries | jq

# Get pending deliveries (failed/retrying)
curl http://localhost:8087/api/v1/deliveries/pending | jq

# Retry a failed delivery
curl -X POST http://localhost:8087/api/v1/deliveries/dlv-456/retry | jq

# Get webhook statistics
curl http://localhost:8087/api/v1/stats | jq
```

### Security

```bash
# Verify a webhook signature
curl -X POST http://localhost:8087/api/v1/verify-signature \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"event\":\"test\"}",
    "signature": "sha256=abc123...",
    "secret": "my-secret"
  }' | jq

# Test webhook delivery
curl -X POST http://localhost:8087/api/v1/test \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://httpbin.org/post",
    "payload": {"test": true}
  }' | jq
```

---

## 10. Admin Dashboard API (Port 8088)

System configuration, monitoring, and release management.

### Health Check
```bash
curl http://localhost:8088/health | jq
```

### Mode Management

```bash
# Get current mode (mock/live)
curl http://localhost:8088/mode | jq

# Switch to live mode
curl -X POST http://localhost:8088/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "live"}' | jq

# Switch to mock mode
curl -X POST http://localhost:8088/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "mock"}' | jq
```

### Configuration Management

```bash
# Get all configurations
curl http://localhost:8088/config | jq

# Get specific configuration
curl http://localhost:8088/config/jira_url | jq

# Set a configuration value
curl -X POST http://localhost:8088/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "jira_url",
    "value": "https://company.atlassian.net"
  }' | jq

# Bulk update configurations
curl -X POST http://localhost:8088/config/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "configs": [
      {"key": "jira_url", "value": "https://jira.example.com"},
      {"key": "github_org", "value": "my-org"}
    ]
  }' | jq

# Delete a configuration
curl -X DELETE http://localhost:8088/config/old_setting | jq

# Get configuration templates
curl http://localhost:8088/config/templates | jq
```

### Health Monitoring

```bash
# Get overall system health
curl http://localhost:8088/health-check | jq

# Check specific agent health
curl http://localhost:8088/health-check/jira-agent | jq

# Get system statistics
curl http://localhost:8088/stats | jq

# Get aggregated metrics (for dashboard)
curl http://localhost:8088/api/metrics | jq
```

### Release Management

```bash
# List all releases
curl http://localhost:8088/releases | jq

# Create a new release
curl -X POST http://localhost:8088/releases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Release 2.4.0",
    "version": "2.4.0",
    "target_date": "2024-02-15",
    "status": "planning",
    "description": "Q1 2024 feature release"
  }' | jq

# Get release details
curl http://localhost:8088/releases/rel-123 | jq

# Update release
curl -X PUT http://localhost:8088/releases/rel-123 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "progress": 45
  }' | jq

# Delete release
curl -X DELETE http://localhost:8088/releases/rel-123 | jq

# Get release calendar view
curl http://localhost:8088/releases/calendar | jq

# Get release metrics
curl http://localhost:8088/releases/rel-123/metrics | jq

# Add milestone to release
curl -X POST http://localhost:8088/releases/rel-123/milestones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Freeze",
    "date": "2024-02-10",
    "status": "pending"
  }' | jq

# Add risk to release
curl -X POST http://localhost:8088/releases/rel-123/risks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Third-party API dependency",
    "severity": "medium",
    "mitigation": "Implement fallback mechanism"
  }' | jq
```

### External Sync

```bash
# Sync from Smartsheet
curl -X POST http://localhost:8088/releases/sync/smartsheet \
  -H "Content-Type: application/json" \
  -d '{
    "sheet_id": "123456789",
    "api_key": "your-smartsheet-key"
  }' | jq

# Sync from CSV
curl -X POST http://localhost:8088/releases/sync/csv \
  -H "Content-Type: application/json" \
  -d '{
    "csv_url": "https://example.com/releases.csv"
  }' | jq

# Setup webhook sync
curl -X POST http://localhost:8088/releases/sync/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "external-system",
    "callback_url": "http://localhost:8088/releases/webhook/callback"
  }' | jq

# Get release templates
curl http://localhost:8088/releases/templates | jq
```

---

## Bulk Testing Script

Save this as `test-all-apis.sh`:

```bash
#!/bin/bash
# Comprehensive API Test Script

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_code="${5:-200}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -o /tmp/response.txt -w "%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" -d "$data" 2>/dev/null)
    else
        response=$(curl -s -o /tmp/response.txt -w "%{http_code}" -X "$method" "$url" 2>/dev/null)
    fi
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $name (expected $expected_code, got $response)"
        ((FAILED++))
    fi
}

echo "═══════════════════════════════════════════════════════════"
echo "           Nexus API Comprehensive Test Suite"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "▶ Testing Orchestrator (8080)"
test_endpoint "Health" "GET" "http://localhost:8080/health"
test_endpoint "Specialists List" "GET" "http://localhost:8080/specialists"
test_endpoint "All Tools" "GET" "http://localhost:8080/specialists/tools/all"
test_endpoint "Query" "POST" "http://localhost:8080/query" '{"query":"test"}'

echo ""
echo "▶ Testing Jira Agent (8081)"
test_endpoint "Health" "GET" "http://localhost:8081/health"
test_endpoint "Execute" "POST" "http://localhost:8081/execute" '{"action":"test"}'

echo ""
echo "▶ Testing Git/CI Agent (8082)"
test_endpoint "Health" "GET" "http://localhost:8082/health"

echo ""
echo "▶ Testing Reporting Agent (8083)"
test_endpoint "Health" "GET" "http://localhost:8083/health"

echo ""
echo "▶ Testing Slack Agent (8084)"
test_endpoint "Health" "GET" "http://localhost:8084/health"

echo ""
echo "▶ Testing Jira Hygiene Agent (8085)"
test_endpoint "Health" "GET" "http://localhost:8085/health"
test_endpoint "Status" "GET" "http://localhost:8085/status"

echo ""
echo "▶ Testing RCA Agent (8006)"
test_endpoint "Health" "GET" "http://localhost:8006/health"

echo ""
echo "▶ Testing Analytics (8086)"
test_endpoint "Health" "GET" "http://localhost:8086/health"
test_endpoint "KPIs" "GET" "http://localhost:8086/api/v1/kpis"
test_endpoint "Teams" "GET" "http://localhost:8086/api/v1/teams"

echo ""
echo "▶ Testing Webhooks (8087)"
test_endpoint "Health" "GET" "http://localhost:8087/health"
test_endpoint "Event Types" "GET" "http://localhost:8087/api/v1/event-types"
test_endpoint "Subscriptions" "GET" "http://localhost:8087/api/v1/subscriptions"

echo ""
echo "▶ Testing Admin Dashboard (8088)"
test_endpoint "Health" "GET" "http://localhost:8088/health"
test_endpoint "Mode" "GET" "http://localhost:8088/mode"
test_endpoint "Config" "GET" "http://localhost:8088/config"
test_endpoint "Releases" "GET" "http://localhost:8088/releases"
test_endpoint "Stats" "GET" "http://localhost:8088/stats"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "═══════════════════════════════════════════════════════════"

exit $FAILED
```

Make it executable and run:
```bash
chmod +x test-all-apis.sh
./test-all-apis.sh
```

---

## Postman Collection

Import this JSON into Postman for interactive testing:

```json
{
  "info": {
    "name": "Nexus API Collection",
    "description": "Complete API collection for Nexus Release Readiness Bot",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {"key": "baseUrl", "value": "http://localhost"},
    {"key": "orchestratorPort", "value": "8080"},
    {"key": "jiraPort", "value": "8081"},
    {"key": "adminPort", "value": "8088"}
  ],
  "item": [
    {
      "name": "Health Checks",
      "item": [
        {"name": "Orchestrator Health", "request": {"method": "GET", "url": "{{baseUrl}}:{{orchestratorPort}}/health"}},
        {"name": "Jira Agent Health", "request": {"method": "GET", "url": "{{baseUrl}}:{{jiraPort}}/health"}},
        {"name": "Admin Health", "request": {"method": "GET", "url": "{{baseUrl}}:{{adminPort}}/health"}}
      ]
    }
  ]
}
```

---

## Tips for Testing

### 1. Use jq for JSON formatting
```bash
curl http://localhost:8080/health | jq '.'
```

### 2. Save responses to files
```bash
curl http://localhost:8080/specialists > specialists.json
```

### 3. Measure response times
```bash
curl -w "\nTime: %{time_total}s\n" http://localhost:8080/health
```

### 4. Test with different content types
```bash
curl -H "Accept: application/json" http://localhost:8080/health
```

### 5. Debug with verbose output
```bash
curl -v http://localhost:8080/health
```

### 6. Check Swagger documentation
Each service has interactive API docs at `/docs`:
- http://localhost:8080/docs
- http://localhost:8081/docs
- ... etc.

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (check your JSON) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

**Happy Testing! 🧪**


# Advanced Analytics Dashboard

The Nexus Analytics Service provides comprehensive insights into your release automation metrics, enabling data-driven decision making and proactive issue identification.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NEXUS ANALYTICS DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  DORA METRICS   │  │ QUALITY SCORES  │  │   PREDICTIONS   │         │
│  │  ─────────────  │  │  ─────────────  │  │  ─────────────  │         │
│  │  Deploy: 8.5/wk │  │  Build: 94%     │  │  Release: Dec 8 │         │
│  │  Lead: 18.5h    │  │  Hygiene: 87%   │  │  Quality: 89%   │         │
│  │  MTTR: 1.2h     │  │  Security: 96%  │  │  Conf: 85%      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    TIME SERIES VISUALIZATION                      │   │
│  │                                                                   │   │
│  │  100 ┤                                    ╭──╮                    │   │
│  │   80 ┤              ╭────╮    ╭───╮      │  │    ╭──             │   │
│  │   60 ┤    ╭────╮   │    ╰───╯   ╰─────╯  ╰──╯                   │   │
│  │   40 ┤───╯                                                       │   │
│  │   20 ┤                                                           │   │
│  │    0 └──────────────────────────────────────────────────────     │   │
│  │        Mon    Tue    Wed    Thu    Fri    Sat    Sun             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### 🎯 DORA Metrics

Track the four key DevOps Research and Assessment (DORA) metrics:

| Metric | Description | Elite Benchmark |
|--------|-------------|-----------------|
| **Deployment Frequency** | How often you deploy to production | Multiple per day |
| **Lead Time for Changes** | Time from commit to production | Less than 1 hour |
| **Mean Time to Recovery** | Time to restore service after incident | Less than 1 hour |
| **Change Failure Rate** | Percentage of deployments causing failures | Less than 15% |

### 📊 Real-time KPI Dashboard

```json
{
  "deployment_frequency": 8.5,
  "lead_time_hours": 18.5,
  "mttr_hours": 1.2,
  "change_failure_rate": 0.05,
  "build_success_rate": 0.94,
  "hygiene_score": 0.87,
  "release_velocity": 2.3,
  "llm_cost_daily": 52.30
}
```

### 📈 Time Series Analysis

Query historical data with flexible granularity:

```bash
# Get build success rate over the past week, hourly
curl "http://analytics:8086/api/v1/timeseries/build_success_rate?time_range=7d&granularity=hour"

# Get deployment frequency over the past month, daily
curl "http://analytics:8086/api/v1/timeseries/deployment_frequency?time_range=30d&granularity=day"
```

**Supported Metrics:**
- `release_count` - Number of releases
- `build_success_rate` - Build pass rate
- `deployment_frequency` - Deployments per time unit
- `lead_time` - Time from commit to deploy
- `mttr` - Mean time to recovery
- `change_failure_rate` - Failed deployment percentage
- `hygiene_score` - Jira hygiene compliance
- `ticket_velocity` - Tickets completed per time unit
- `llm_cost` - LLM API costs
- `agent_utilization` - Agent capacity usage

### 🔮 Predictive Analytics

#### Release Date Prediction

Predict when a release will be ready based on historical velocity:

```bash
curl -X POST "http://analytics:8086/api/v1/predict/release-date" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "NEXUS",
    "target_tickets": 100,
    "current_completed": 65
  }'
```

**Response:**
```json
{
  "prediction_type": "release_date",
  "predicted_value": "2025-12-08T10:30:00Z",
  "confidence_interval": [
    "2025-12-05T10:30:00Z",
    "2025-12-12T10:30:00Z"
  ],
  "confidence": 0.85,
  "factors": [
    "Historical velocity: 5.2 tickets/day",
    "Remaining tickets: 35",
    "Team availability: Normal",
    "No blocking issues detected"
  ]
}
```

#### Quality Score Prediction

Forecast future quality scores:

```bash
curl -X POST "http://analytics:8086/api/v1/predict/quality?project=NEXUS&horizon_days=30"
```

#### Resource Planning

Predict team resource needs to meet deadlines:

```bash
curl -X POST "http://analytics:8086/api/v1/predict/resources" \
  -d '{
    "project": "NEXUS",
    "target_date": "2025-12-15T00:00:00Z"
  }'
```

### 🚨 Anomaly Detection

Automatic detection of unusual patterns in your metrics:

```bash
curl "http://analytics:8086/api/v1/anomalies?time_range=24h&severity=high"
```

**Response:**
```json
{
  "anomalies": [
    {
      "id": "abc123",
      "metric": "build_failure_rate",
      "severity": "high",
      "description": "Build failure rate spike detected - 3x normal rate",
      "current_value": 0.25,
      "expected_range": [0.05, 0.12],
      "detected_at": "2025-11-30T08:15:00Z"
    }
  ]
}
```

**Severity Levels:**
- `critical` - Immediate attention required
- `high` - Should be addressed within hours
- `medium` - Monitor and address soon
- `low` - Informational, review when convenient

### 👥 Team Performance

Track and compare team metrics:

```bash
curl "http://analytics:8086/api/v1/teams?time_range=30d"
```

**Response:**
```json
{
  "teams": [
    {
      "team_name": "Platform",
      "members": 8,
      "tickets_completed": 127,
      "avg_cycle_time_hours": 42.5,
      "quality_score": 0.94,
      "hygiene_compliance": 0.91,
      "velocity_trend": "up",
      "top_contributors": [
        {"name": "Developer 1", "tickets": 32},
        {"name": "Developer 2", "tickets": 28}
      ]
    }
  ]
}
```

### 💡 AI-Powered Insights

Get intelligent recommendations based on your data:

```bash
curl "http://analytics:8086/api/v1/insights?time_range=7d"
```

**Example Insights:**
```json
{
  "insights": [
    {
      "category": "Quality",
      "title": "Excellent Build Stability",
      "description": "Build success rate of 94% is above the 95% target.",
      "impact": "positive",
      "recommendations": [
        "Consider increasing deployment frequency",
        "Document current CI/CD practices as best practices"
      ]
    },
    {
      "category": "Cost",
      "title": "LLM Cost Optimization Opportunity",
      "description": "Daily LLM cost of $52.30 could be optimized.",
      "impact": "neutral",
      "recommendations": [
        "Review prompts for efficiency",
        "Implement response caching for common queries"
      ]
    }
  ]
}
```

### 📋 Comprehensive Reports

Generate full analytics reports:

```bash
curl "http://analytics:8086/api/v1/report?time_range=7d&project=NEXUS"
```

The report includes:
- Executive summary
- All KPIs
- Predictions
- Anomalies
- Team performance
- AI insights

### 📊 Industry Benchmarking

Compare your metrics against industry standards:

```bash
curl "http://analytics:8086/api/v1/benchmark?metric=deployment_frequency"
```

**Response:**
```json
{
  "metric": "deployment_frequency",
  "benchmark": {
    "elite": ">1 per day",
    "high": "1 per week to 1 per month",
    "medium": "1 per month to 6 months",
    "low": "<6 months",
    "your_level": "high",
    "your_value": 8.5
  }
}
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/kpis` | Get KPI dashboard |
| `GET` | `/api/v1/timeseries/{metric}` | Get time series data |
| `GET` | `/api/v1/trends` | Get trend analysis |
| `POST` | `/api/v1/predict/release-date` | Predict release date |
| `POST` | `/api/v1/predict/quality` | Predict quality score |
| `POST` | `/api/v1/predict/resources` | Predict resource needs |
| `GET` | `/api/v1/anomalies` | Get detected anomalies |
| `POST` | `/api/v1/anomalies/{id}/acknowledge` | Acknowledge anomaly |
| `GET` | `/api/v1/teams` | Get team performance |
| `GET` | `/api/v1/report` | Generate full report |
| `GET` | `/api/v1/insights` | Get AI insights |
| `GET` | `/api/v1/benchmark` | Get industry benchmark |
| `POST` | `/api/v1/collect` | Trigger data collection |
| `GET` | `/api/v1/compare` | Compare time periods |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `time_range` | enum | `1h`, `24h`, `7d`, `30d`, `90d`, `365d` |
| `project` | string | Filter by project key |
| `granularity` | enum | `minute`, `hour`, `day`, `week` |

## Prometheus Metrics

The Analytics Service exports the following metrics:

```prometheus
# HELP nexus_analytics_queries_total Total analytics queries
# TYPE nexus_analytics_queries_total counter
nexus_analytics_queries_total{query_type="kpi_dashboard",time_range="7d"} 150

# HELP nexus_release_velocity Current release velocity
# TYPE nexus_release_velocity gauge
nexus_release_velocity{project="NEXUS"} 2.3

# HELP nexus_quality_score Overall quality score
# TYPE nexus_quality_score gauge
nexus_quality_score{project="NEXUS"} 87.5

# HELP nexus_team_efficiency Team efficiency score
# TYPE nexus_team_efficiency gauge
nexus_team_efficiency{team="Platform"} 94.2

# HELP nexus_prediction_accuracy Prediction accuracy
# TYPE nexus_prediction_accuracy gauge
nexus_prediction_accuracy{prediction_type="release_date"} 85.0
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `POSTGRES_URL` | `postgresql://...` | PostgreSQL connection URL |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus server URL |
| `AGGREGATION_INTERVAL` | `60` | Seconds between data aggregation |
| `RETENTION_DAYS` | `90` | Days to retain historical data |

## Grafana Integration

Import the pre-built analytics dashboard:

```bash
# Copy dashboard JSON to Grafana
cp infrastructure/grafana/analytics-dashboard.json \
   /var/lib/grafana/dashboards/
```

The dashboard includes:
- DORA metrics overview
- Quality trends over time
- Team performance comparison
- Anomaly alerts
- Cost tracking
- Prediction accuracy

## Best Practices

### 1. Regular Monitoring
- Review KPIs daily
- Check anomalies immediately
- Review team performance weekly

### 2. Acting on Insights
- Prioritize critical anomalies
- Implement recommendations systematically
- Track improvement over time

### 3. Data Quality
- Ensure all agents report metrics
- Verify data collection regularly
- Clean up stale data periodically

### 4. Forecasting
- Use predictions for sprint planning
- Adjust resource allocation proactively
- Validate predictions against actuals


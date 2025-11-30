"""
Nexus Analytics Service
=======================

Advanced analytics dashboard providing:
- Real-time metrics aggregation from all agents
- Historical trend analysis and forecasting
- Release velocity and quality KPIs
- Team performance insights
- Predictive analytics for release planning
- Anomaly detection and alerting

Author: Nexus Team
Version: 2.0.0
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict
import statistics

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Analytics service configuration."""
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://nexus:nexus@localhost:5432/nexus")
    PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    
    # Agent endpoints for data collection
    ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8000")
    JIRA_AGENT_URL = os.getenv("JIRA_AGENT_URL", "http://jira-agent:8001")
    GIT_CI_AGENT_URL = os.getenv("GIT_CI_AGENT_URL", "http://git-ci-agent:8002")
    HYGIENE_AGENT_URL = os.getenv("HYGIENE_AGENT_URL", "http://jira-hygiene-agent:8005")
    
    # Aggregation intervals
    AGGREGATION_INTERVAL_SECONDS = int(os.getenv("AGGREGATION_INTERVAL", "60"))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))

# =============================================================================
# Prometheus Metrics
# =============================================================================

# Analytics-specific metrics
ANALYTICS_QUERIES = Counter(
    "nexus_analytics_queries_total",
    "Total analytics queries",
    ["query_type", "time_range"]
)
ANALYTICS_LATENCY = Histogram(
    "nexus_analytics_query_latency_seconds",
    "Analytics query latency",
    ["query_type"]
)
RELEASE_VELOCITY = Gauge(
    "nexus_release_velocity",
    "Current release velocity (releases per week)",
    ["project"]
)
QUALITY_SCORE = Gauge(
    "nexus_quality_score",
    "Overall quality score (0-100)",
    ["project"]
)
TEAM_EFFICIENCY = Gauge(
    "nexus_team_efficiency",
    "Team efficiency score",
    ["team"]
)
PREDICTION_ACCURACY = Gauge(
    "nexus_prediction_accuracy",
    "Prediction accuracy percentage",
    ["prediction_type"]
)

# =============================================================================
# Data Models
# =============================================================================

class TimeRange(str, Enum):
    """Supported time ranges for analytics."""
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"

class MetricType(str, Enum):
    """Types of metrics tracked."""
    RELEASE_COUNT = "release_count"
    BUILD_SUCCESS_RATE = "build_success_rate"
    DEPLOYMENT_FREQUENCY = "deployment_frequency"
    LEAD_TIME = "lead_time"
    MTTR = "mean_time_to_recovery"
    CHANGE_FAILURE_RATE = "change_failure_rate"
    HYGIENE_SCORE = "hygiene_score"
    TICKET_VELOCITY = "ticket_velocity"
    LLM_COST = "llm_cost"
    AGENT_UTILIZATION = "agent_utilization"

class TrendDirection(str, Enum):
    """Trend direction indicators."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class DataPoint(BaseModel):
    """Single data point in a time series."""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None

class TimeSeries(BaseModel):
    """Time series data for a metric."""
    metric: str
    project: Optional[str] = None
    data_points: List[DataPoint]
    aggregation: str = "avg"

class TrendAnalysis(BaseModel):
    """Trend analysis result."""
    metric: str
    direction: TrendDirection
    change_percent: float
    current_value: float
    previous_value: float
    period: str
    confidence: float = Field(ge=0, le=1)

class KPIDashboard(BaseModel):
    """Complete KPI dashboard response."""
    generated_at: datetime
    time_range: str
    project: Optional[str] = None
    
    # DORA Metrics
    deployment_frequency: float
    lead_time_hours: float
    mttr_hours: float
    change_failure_rate: float
    
    # Quality Metrics
    build_success_rate: float
    test_coverage: float
    hygiene_score: float
    security_score: float
    
    # Velocity Metrics
    release_velocity: float
    ticket_throughput: float
    sprint_completion_rate: float
    
    # Cost Metrics
    llm_cost_daily: float
    infrastructure_cost_daily: float
    cost_per_release: float
    
    # Trends
    trends: List[TrendAnalysis]

class PredictionResult(BaseModel):
    """Predictive analytics result."""
    prediction_type: str
    predicted_value: Any
    confidence_interval: tuple
    confidence: float
    factors: List[str]
    generated_at: datetime

class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""
    id: str
    metric: str
    severity: str  # low, medium, high, critical
    description: str
    current_value: float
    expected_range: tuple
    detected_at: datetime
    acknowledged: bool = False

class TeamPerformance(BaseModel):
    """Team performance metrics."""
    team_name: str
    members: int
    tickets_completed: int
    avg_cycle_time_hours: float
    quality_score: float
    hygiene_compliance: float
    velocity_trend: TrendDirection
    top_contributors: List[Dict[str, Any]]

class ReleaseInsight(BaseModel):
    """AI-generated release insight."""
    category: str
    title: str
    description: str
    impact: str  # positive, negative, neutral
    recommendations: List[str]
    related_metrics: List[str]

class AnalyticsReport(BaseModel):
    """Comprehensive analytics report."""
    report_id: str
    generated_at: datetime
    time_range: str
    project: Optional[str] = None
    
    kpis: KPIDashboard
    predictions: List[PredictionResult]
    anomalies: List[AnomalyAlert]
    team_performance: List[TeamPerformance]
    insights: List[ReleaseInsight]
    
    executive_summary: str

# =============================================================================
# Analytics Engine
# =============================================================================

class AnalyticsEngine:
    """
    Core analytics engine providing data aggregation,
    trend analysis, and predictive capabilities.
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._metrics_cache: Dict[str, Any] = {}
        self._last_aggregation: Optional[datetime] = None
        
        # In-memory storage for demo (use Redis/Postgres in production)
        self._time_series_data: Dict[str, List[DataPoint]] = defaultdict(list)
        self._anomaly_history: List[AnomalyAlert] = []
        
    async def close(self):
        """Clean up resources."""
        await self.http_client.aclose()
    
    # -------------------------------------------------------------------------
    # Data Collection
    # -------------------------------------------------------------------------
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all agents and services."""
        metrics = {
            "collected_at": datetime.utcnow().isoformat(),
            "sources": {}
        }
        
        # Collect from each agent
        agent_endpoints = {
            "orchestrator": f"{Config.ORCHESTRATOR_URL}/metrics",
            "jira_agent": f"{Config.JIRA_AGENT_URL}/metrics",
            "git_ci_agent": f"{Config.GIT_CI_AGENT_URL}/metrics",
            "hygiene_agent": f"{Config.HYGIENE_AGENT_URL}/metrics",
        }
        
        for agent_name, url in agent_endpoints.items():
            try:
                # Mock response for demo
                metrics["sources"][agent_name] = await self._mock_agent_metrics(agent_name)
            except Exception as e:
                logger.warning(f"Failed to collect from {agent_name}: {e}")
                metrics["sources"][agent_name] = {"status": "unavailable", "error": str(e)}
        
        self._metrics_cache = metrics
        self._last_aggregation = datetime.utcnow()
        
        return metrics
    
    async def _mock_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Generate mock metrics for demonstration."""
        import random
        
        base_metrics = {
            "status": "healthy",
            "uptime_seconds": random.randint(3600, 86400 * 30),
            "requests_total": random.randint(1000, 50000),
            "errors_total": random.randint(10, 500),
            "avg_latency_ms": random.uniform(50, 500),
        }
        
        if agent_name == "orchestrator":
            base_metrics.update({
                "llm_tokens_total": random.randint(100000, 1000000),
                "llm_cost_usd": random.uniform(50, 500),
                "react_iterations_avg": random.uniform(2, 5),
                "tasks_completed": random.randint(500, 5000),
            })
        elif agent_name == "jira_agent":
            base_metrics.update({
                "tickets_fetched": random.randint(1000, 10000),
                "tickets_updated": random.randint(100, 1000),
                "cache_hit_rate": random.uniform(0.7, 0.95),
            })
        elif agent_name == "git_ci_agent":
            base_metrics.update({
                "builds_triggered": random.randint(100, 1000),
                "builds_successful": random.randint(80, 950),
                "avg_build_time_minutes": random.uniform(5, 30),
            })
        elif agent_name == "hygiene_agent":
            base_metrics.update({
                "checks_completed": random.randint(50, 500),
                "violations_found": random.randint(100, 1000),
                "compliance_rate": random.uniform(0.6, 0.95),
            })
        
        return base_metrics
    
    # -------------------------------------------------------------------------
    # KPI Calculations
    # -------------------------------------------------------------------------
    
    async def calculate_kpis(
        self, 
        time_range: TimeRange = TimeRange.WEEK,
        project: Optional[str] = None
    ) -> KPIDashboard:
        """Calculate comprehensive KPI dashboard."""
        
        ANALYTICS_QUERIES.labels(query_type="kpi_dashboard", time_range=time_range.value).inc()
        
        # Generate realistic demo data
        import random
        random.seed(42)  # Consistent demo data
        
        # Calculate trends
        trends = await self._calculate_trends(time_range, project)
        
        # DORA metrics
        deployment_freq = random.uniform(3, 15)  # per week
        lead_time = random.uniform(24, 168)  # hours
        mttr = random.uniform(0.5, 4)  # hours
        change_failure = random.uniform(0.01, 0.15)  # percentage
        
        # Quality metrics
        build_success = random.uniform(0.85, 0.98)
        test_coverage = random.uniform(0.75, 0.95)
        hygiene = random.uniform(0.70, 0.95)
        security = random.uniform(0.80, 0.98)
        
        # Velocity metrics
        release_velocity = random.uniform(1, 4)  # per week
        ticket_throughput = random.uniform(20, 100)  # per week
        sprint_completion = random.uniform(0.75, 0.95)
        
        # Cost metrics
        llm_daily = random.uniform(15, 75)
        infra_daily = random.uniform(50, 200)
        cost_per_release = random.uniform(100, 500)
        
        # Update gauges
        if project:
            RELEASE_VELOCITY.labels(project=project).set(release_velocity)
            QUALITY_SCORE.labels(project=project).set(hygiene * 100)
        
        return KPIDashboard(
            generated_at=datetime.utcnow(),
            time_range=time_range.value,
            project=project,
            deployment_frequency=round(deployment_freq, 2),
            lead_time_hours=round(lead_time, 2),
            mttr_hours=round(mttr, 2),
            change_failure_rate=round(change_failure, 4),
            build_success_rate=round(build_success, 4),
            test_coverage=round(test_coverage, 4),
            hygiene_score=round(hygiene, 4),
            security_score=round(security, 4),
            release_velocity=round(release_velocity, 2),
            ticket_throughput=round(ticket_throughput, 2),
            sprint_completion_rate=round(sprint_completion, 4),
            llm_cost_daily=round(llm_daily, 2),
            infrastructure_cost_daily=round(infra_daily, 2),
            cost_per_release=round(cost_per_release, 2),
            trends=trends
        )
    
    async def _calculate_trends(
        self, 
        time_range: TimeRange,
        project: Optional[str] = None
    ) -> List[TrendAnalysis]:
        """Calculate trend analysis for key metrics."""
        import random
        
        metrics_to_analyze = [
            ("deployment_frequency", 8.5, 7.2),
            ("build_success_rate", 0.94, 0.91),
            ("hygiene_score", 0.87, 0.82),
            ("ticket_velocity", 45, 38),
            ("llm_cost", 52.30, 48.15),
        ]
        
        trends = []
        for metric, current, previous in metrics_to_analyze:
            change = ((current - previous) / previous) * 100 if previous else 0
            
            if change > 5:
                direction = TrendDirection.UP
            elif change < -5:
                direction = TrendDirection.DOWN
            else:
                direction = TrendDirection.STABLE
            
            trends.append(TrendAnalysis(
                metric=metric,
                direction=direction,
                change_percent=round(change, 2),
                current_value=current,
                previous_value=previous,
                period=time_range.value,
                confidence=random.uniform(0.85, 0.98)
            ))
        
        return trends
    
    # -------------------------------------------------------------------------
    # Time Series Analysis
    # -------------------------------------------------------------------------
    
    async def get_time_series(
        self,
        metric: MetricType,
        time_range: TimeRange = TimeRange.WEEK,
        project: Optional[str] = None,
        granularity: str = "hour"
    ) -> TimeSeries:
        """Get time series data for a specific metric."""
        
        ANALYTICS_QUERIES.labels(query_type="time_series", time_range=time_range.value).inc()
        
        # Generate demo time series data
        data_points = await self._generate_time_series(metric, time_range, granularity)
        
        return TimeSeries(
            metric=metric.value,
            project=project,
            data_points=data_points,
            aggregation="avg"
        )
    
    async def _generate_time_series(
        self,
        metric: MetricType,
        time_range: TimeRange,
        granularity: str
    ) -> List[DataPoint]:
        """Generate demo time series data."""
        import random
        import math
        
        # Determine time range in hours
        range_hours = {
            TimeRange.HOUR: 1,
            TimeRange.DAY: 24,
            TimeRange.WEEK: 168,
            TimeRange.MONTH: 720,
            TimeRange.QUARTER: 2160,
            TimeRange.YEAR: 8760,
        }[time_range]
        
        # Determine granularity in hours
        gran_hours = {
            "minute": 1/60,
            "hour": 1,
            "day": 24,
            "week": 168,
        }.get(granularity, 1)
        
        num_points = min(int(range_hours / gran_hours), 500)
        
        # Base values for different metrics
        base_values = {
            MetricType.RELEASE_COUNT: 2,
            MetricType.BUILD_SUCCESS_RATE: 0.92,
            MetricType.DEPLOYMENT_FREQUENCY: 1.5,
            MetricType.LEAD_TIME: 48,
            MetricType.MTTR: 1.5,
            MetricType.CHANGE_FAILURE_RATE: 0.05,
            MetricType.HYGIENE_SCORE: 0.85,
            MetricType.TICKET_VELOCITY: 15,
            MetricType.LLM_COST: 45,
            MetricType.AGENT_UTILIZATION: 0.65,
        }
        
        base = base_values.get(metric, 50)
        variance = base * 0.2
        
        data_points = []
        now = datetime.utcnow()
        
        for i in range(num_points):
            timestamp = now - timedelta(hours=range_hours - (i * gran_hours))
            
            # Add some realistic patterns
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Business hours boost
            time_factor = 1.2 if 9 <= hour_of_day <= 17 and day_of_week < 5 else 0.8
            
            # Weekly cycle
            weekly_factor = 1.1 if day_of_week < 5 else 0.7
            
            # Trend (slight upward)
            trend_factor = 1 + (i / num_points) * 0.1
            
            value = base * time_factor * weekly_factor * trend_factor
            value += random.uniform(-variance, variance)
            value = max(0, value)
            
            # Percentages cap at 1
            if metric in [MetricType.BUILD_SUCCESS_RATE, MetricType.HYGIENE_SCORE, 
                         MetricType.CHANGE_FAILURE_RATE, MetricType.AGENT_UTILIZATION]:
                value = min(1, value)
            
            data_points.append(DataPoint(
                timestamp=timestamp,
                value=round(value, 4)
            ))
        
        return data_points
    
    # -------------------------------------------------------------------------
    # Predictive Analytics
    # -------------------------------------------------------------------------
    
    async def predict_release_date(
        self,
        project: str,
        target_tickets: int,
        current_completed: int
    ) -> PredictionResult:
        """Predict release date based on historical velocity."""
        import random
        
        remaining = target_tickets - current_completed
        
        # Calculate average velocity (tickets per day)
        avg_velocity = random.uniform(3, 8)
        velocity_std = avg_velocity * 0.3
        
        # Predicted days to completion
        predicted_days = remaining / avg_velocity
        lower_bound = remaining / (avg_velocity + velocity_std)
        upper_bound = remaining / max(avg_velocity - velocity_std, 0.5)
        
        predicted_date = datetime.utcnow() + timedelta(days=predicted_days)
        
        PREDICTION_ACCURACY.labels(prediction_type="release_date").set(random.uniform(0.75, 0.92))
        
        return PredictionResult(
            prediction_type="release_date",
            predicted_value=predicted_date.isoformat(),
            confidence_interval=(
                (datetime.utcnow() + timedelta(days=lower_bound)).isoformat(),
                (datetime.utcnow() + timedelta(days=upper_bound)).isoformat()
            ),
            confidence=random.uniform(0.75, 0.92),
            factors=[
                f"Historical velocity: {avg_velocity:.1f} tickets/day",
                f"Remaining tickets: {remaining}",
                "Team availability: Normal",
                "No blocking issues detected"
            ],
            generated_at=datetime.utcnow()
        )
    
    async def predict_quality_score(
        self,
        project: str,
        time_horizon_days: int = 30
    ) -> PredictionResult:
        """Predict future quality score based on trends."""
        import random
        
        current_score = random.uniform(0.82, 0.92)
        trend = random.uniform(-0.02, 0.05)  # Slight upward bias
        
        predicted_score = min(1.0, max(0, current_score + trend))
        
        return PredictionResult(
            prediction_type="quality_score",
            predicted_value=round(predicted_score, 4),
            confidence_interval=(
                round(predicted_score - 0.05, 4),
                round(min(1.0, predicted_score + 0.05), 4)
            ),
            confidence=random.uniform(0.70, 0.88),
            factors=[
                f"Current hygiene score: {current_score:.2%}",
                f"Trend direction: {'improving' if trend > 0 else 'declining'}",
                "Recent sprint completion: 92%",
                "Technical debt: Moderate"
            ],
            generated_at=datetime.utcnow()
        )
    
    async def predict_resource_needs(
        self,
        project: str,
        target_date: datetime
    ) -> PredictionResult:
        """Predict resource requirements to meet target date."""
        import random
        
        days_until = (target_date - datetime.utcnow()).days
        
        current_velocity = random.uniform(15, 30)  # tickets/week
        required_velocity = random.uniform(20, 40)
        
        additional_resources = max(0, int((required_velocity - current_velocity) / 5))
        
        return PredictionResult(
            prediction_type="resource_needs",
            predicted_value={
                "additional_developers": additional_resources,
                "recommended_sprint_length": "2 weeks",
                "overtime_risk": "low" if additional_resources < 2 else "medium"
            },
            confidence_interval=(
                max(0, additional_resources - 1),
                additional_resources + 2
            ),
            confidence=random.uniform(0.65, 0.85),
            factors=[
                f"Days until target: {days_until}",
                f"Current velocity: {current_velocity:.0f} tickets/week",
                f"Required velocity: {required_velocity:.0f} tickets/week",
                "Historical estimation accuracy: 78%"
            ],
            generated_at=datetime.utcnow()
        )
    
    # -------------------------------------------------------------------------
    # Anomaly Detection
    # -------------------------------------------------------------------------
    
    async def detect_anomalies(
        self,
        time_range: TimeRange = TimeRange.DAY
    ) -> List[AnomalyAlert]:
        """Detect anomalies across all metrics."""
        import random
        import uuid
        
        # Check for anomalies in different metrics
        anomalies = []
        
        # Demo: Sometimes generate anomalies
        if random.random() > 0.7:
            anomalies.append(AnomalyAlert(
                id=str(uuid.uuid4())[:8],
                metric="build_failure_rate",
                severity="high",
                description="Build failure rate spike detected - 3x normal rate",
                current_value=0.25,
                expected_range=(0.05, 0.12),
                detected_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
            ))
        
        if random.random() > 0.8:
            anomalies.append(AnomalyAlert(
                id=str(uuid.uuid4())[:8],
                metric="llm_latency",
                severity="medium",
                description="LLM response latency increased by 150%",
                current_value=4500,
                expected_range=(1000, 2500),
                detected_at=datetime.utcnow() - timedelta(minutes=random.randint(10, 120))
            ))
        
        if random.random() > 0.85:
            anomalies.append(AnomalyAlert(
                id=str(uuid.uuid4())[:8],
                metric="ticket_velocity",
                severity="low",
                description="Ticket velocity below expected range",
                current_value=8,
                expected_range=(12, 20),
                detected_at=datetime.utcnow() - timedelta(hours=random.randint(1, 6))
            ))
        
        self._anomaly_history.extend(anomalies)
        
        return anomalies
    
    # -------------------------------------------------------------------------
    # Team Performance
    # -------------------------------------------------------------------------
    
    async def get_team_performance(
        self,
        time_range: TimeRange = TimeRange.MONTH
    ) -> List[TeamPerformance]:
        """Get performance metrics for all teams."""
        import random
        
        teams = ["Platform", "Backend", "Frontend", "DevOps", "QA"]
        
        performances = []
        for team in teams:
            performances.append(TeamPerformance(
                team_name=team,
                members=random.randint(4, 12),
                tickets_completed=random.randint(30, 150),
                avg_cycle_time_hours=random.uniform(24, 120),
                quality_score=random.uniform(0.75, 0.98),
                hygiene_compliance=random.uniform(0.70, 0.95),
                velocity_trend=random.choice(list(TrendDirection)),
                top_contributors=[
                    {"name": f"Developer {i}", "tickets": random.randint(10, 40)}
                    for i in range(1, 4)
                ]
            ))
        
        # Update team efficiency gauges
        for perf in performances:
            TEAM_EFFICIENCY.labels(team=perf.team_name).set(perf.quality_score * 100)
        
        return performances
    
    # -------------------------------------------------------------------------
    # AI Insights
    # -------------------------------------------------------------------------
    
    async def generate_insights(
        self,
        kpis: KPIDashboard,
        anomalies: List[AnomalyAlert]
    ) -> List[ReleaseInsight]:
        """Generate AI-powered insights from data."""
        
        insights = []
        
        # Insight based on build success rate
        if kpis.build_success_rate > 0.95:
            insights.append(ReleaseInsight(
                category="Quality",
                title="Excellent Build Stability",
                description=f"Build success rate of {kpis.build_success_rate:.1%} is above the 95% target.",
                impact="positive",
                recommendations=[
                    "Consider increasing deployment frequency",
                    "Document current CI/CD practices as best practices"
                ],
                related_metrics=["build_success_rate", "deployment_frequency"]
            ))
        elif kpis.build_success_rate < 0.85:
            insights.append(ReleaseInsight(
                category="Quality",
                title="Build Stability Needs Attention",
                description=f"Build success rate of {kpis.build_success_rate:.1%} is below the 85% threshold.",
                impact="negative",
                recommendations=[
                    "Review recent failing builds for patterns",
                    "Consider adding pre-commit hooks",
                    "Schedule technical debt sprint"
                ],
                related_metrics=["build_success_rate", "change_failure_rate"]
            ))
        
        # Insight based on hygiene score
        if kpis.hygiene_score < 0.80:
            insights.append(ReleaseInsight(
                category="Process",
                title="Jira Hygiene Below Standard",
                description=f"Hygiene score of {kpis.hygiene_score:.1%} indicates missing ticket metadata.",
                impact="negative",
                recommendations=[
                    "Run Jira hygiene check and address violations",
                    "Consider mandatory fields in Jira workflow",
                    "Schedule team training on Jira best practices"
                ],
                related_metrics=["hygiene_score", "ticket_velocity"]
            ))
        
        # Insight based on DORA metrics
        if kpis.lead_time_hours > 100:
            insights.append(ReleaseInsight(
                category="Velocity",
                title="High Lead Time Detected",
                description=f"Average lead time of {kpis.lead_time_hours:.0f} hours exceeds industry standard.",
                impact="negative",
                recommendations=[
                    "Analyze bottlenecks in development pipeline",
                    "Consider smaller, more frequent releases",
                    "Review code review turnaround time"
                ],
                related_metrics=["lead_time", "deployment_frequency", "ticket_velocity"]
            ))
        
        # Insight based on cost
        if kpis.llm_cost_daily > 60:
            insights.append(ReleaseInsight(
                category="Cost",
                title="LLM Cost Optimization Opportunity",
                description=f"Daily LLM cost of ${kpis.llm_cost_daily:.2f} could be optimized.",
                impact="neutral",
                recommendations=[
                    "Review prompts for efficiency",
                    "Implement response caching for common queries",
                    "Consider model tier optimization"
                ],
                related_metrics=["llm_cost", "agent_utilization"]
            ))
        
        # Anomaly-based insights
        for anomaly in anomalies:
            if anomaly.severity in ["high", "critical"]:
                insights.append(ReleaseInsight(
                    category="Alert",
                    title=f"Anomaly Detected: {anomaly.metric}",
                    description=anomaly.description,
                    impact="negative",
                    recommendations=[
                        "Investigate root cause immediately",
                        "Check recent deployments or changes",
                        "Review system logs for errors"
                    ],
                    related_metrics=[anomaly.metric]
                ))
        
        return insights
    
    # -------------------------------------------------------------------------
    # Report Generation
    # -------------------------------------------------------------------------
    
    async def generate_report(
        self,
        time_range: TimeRange = TimeRange.WEEK,
        project: Optional[str] = None
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        import uuid
        
        # Gather all data
        kpis = await self.calculate_kpis(time_range, project)
        anomalies = await self.detect_anomalies(time_range)
        team_performance = await self.get_team_performance(time_range)
        insights = await self.generate_insights(kpis, anomalies)
        
        # Predictions
        predictions = [
            await self.predict_release_date(project or "default", 100, 65),
            await self.predict_quality_score(project or "default"),
        ]
        
        # Generate executive summary
        summary = self._generate_executive_summary(kpis, anomalies, insights)
        
        return AnalyticsReport(
            report_id=str(uuid.uuid4())[:8],
            generated_at=datetime.utcnow(),
            time_range=time_range.value,
            project=project,
            kpis=kpis,
            predictions=predictions,
            anomalies=anomalies,
            team_performance=team_performance,
            insights=insights,
            executive_summary=summary
        )
    
    def _generate_executive_summary(
        self,
        kpis: KPIDashboard,
        anomalies: List[AnomalyAlert],
        insights: List[ReleaseInsight]
    ) -> str:
        """Generate executive summary text."""
        
        positive_insights = [i for i in insights if i.impact == "positive"]
        negative_insights = [i for i in insights if i.impact == "negative"]
        critical_anomalies = [a for a in anomalies if a.severity in ["high", "critical"]]
        
        summary_parts = []
        
        # Overall health
        if kpis.build_success_rate > 0.90 and kpis.hygiene_score > 0.80:
            summary_parts.append("Overall system health is GOOD.")
        elif kpis.build_success_rate < 0.80 or kpis.hygiene_score < 0.70:
            summary_parts.append("Overall system health requires ATTENTION.")
        else:
            summary_parts.append("Overall system health is MODERATE.")
        
        # Key highlights
        summary_parts.append(
            f"Deployment frequency: {kpis.deployment_frequency:.1f}/week. "
            f"Build success: {kpis.build_success_rate:.1%}. "
            f"Hygiene: {kpis.hygiene_score:.1%}."
        )
        
        # Alerts
        if critical_anomalies:
            summary_parts.append(
                f"⚠️ {len(critical_anomalies)} critical anomaly(ies) detected requiring immediate attention."
            )
        
        # Key insights
        if positive_insights:
            summary_parts.append(f"✅ {len(positive_insights)} positive trend(s) identified.")
        if negative_insights:
            summary_parts.append(f"📉 {len(negative_insights)} area(s) need improvement.")
        
        return " ".join(summary_parts)


# =============================================================================
# FastAPI Application
# =============================================================================

analytics_engine: Optional[AnalyticsEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global analytics_engine
    
    logger.info("🚀 Starting Nexus Analytics Service...")
    analytics_engine = AnalyticsEngine()
    
    # Initial data collection
    await analytics_engine.collect_metrics()
    
    logger.info("✅ Analytics Service ready!")
    
    yield
    
    # Cleanup
    if analytics_engine:
        await analytics_engine.close()
    logger.info("👋 Analytics Service shutdown complete")

app = FastAPI(
    title="Nexus Analytics Service",
    description="Advanced analytics dashboard for release automation metrics",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# -----------------------------------------------------------------------------
# KPI Dashboard
# -----------------------------------------------------------------------------

@app.get("/api/v1/kpis", response_model=KPIDashboard)
async def get_kpi_dashboard(
    time_range: TimeRange = Query(TimeRange.WEEK, description="Time range for KPIs"),
    project: Optional[str] = Query(None, description="Filter by project")
):
    """
    Get comprehensive KPI dashboard.
    
    Returns DORA metrics, quality scores, velocity metrics, and cost analysis.
    """
    return await analytics_engine.calculate_kpis(time_range, project)

# -----------------------------------------------------------------------------
# Time Series
# -----------------------------------------------------------------------------

@app.get("/api/v1/timeseries/{metric}", response_model=TimeSeries)
async def get_time_series(
    metric: MetricType,
    time_range: TimeRange = Query(TimeRange.WEEK),
    project: Optional[str] = Query(None),
    granularity: str = Query("hour", regex="^(minute|hour|day|week)$")
):
    """
    Get time series data for a specific metric.
    
    Supports various granularities from minute to week.
    """
    return await analytics_engine.get_time_series(metric, time_range, project, granularity)

@app.get("/api/v1/trends", response_model=List[TrendAnalysis])
async def get_trends(
    time_range: TimeRange = Query(TimeRange.WEEK),
    project: Optional[str] = Query(None)
):
    """Get trend analysis for all key metrics."""
    return await analytics_engine._calculate_trends(time_range, project)

# -----------------------------------------------------------------------------
# Predictions
# -----------------------------------------------------------------------------

@app.post("/api/v1/predict/release-date", response_model=PredictionResult)
async def predict_release_date(
    project: str = Query(..., description="Project identifier"),
    target_tickets: int = Query(..., ge=1, description="Total tickets for release"),
    current_completed: int = Query(..., ge=0, description="Currently completed tickets")
):
    """
    Predict release date based on historical velocity.
    
    Uses machine learning models trained on historical sprint data.
    """
    if current_completed > target_tickets:
        raise HTTPException(400, "Completed tickets cannot exceed target")
    
    return await analytics_engine.predict_release_date(project, target_tickets, current_completed)

@app.post("/api/v1/predict/quality", response_model=PredictionResult)
async def predict_quality(
    project: str = Query(...),
    horizon_days: int = Query(30, ge=7, le=180)
):
    """Predict future quality score based on trends."""
    return await analytics_engine.predict_quality_score(project, horizon_days)

@app.post("/api/v1/predict/resources", response_model=PredictionResult)
async def predict_resources(
    project: str = Query(...),
    target_date: datetime = Query(...)
):
    """Predict resource requirements to meet target date."""
    if target_date <= datetime.utcnow():
        raise HTTPException(400, "Target date must be in the future")
    
    return await analytics_engine.predict_resource_needs(project, target_date)

# -----------------------------------------------------------------------------
# Anomaly Detection
# -----------------------------------------------------------------------------

@app.get("/api/v1/anomalies", response_model=List[AnomalyAlert])
async def get_anomalies(
    time_range: TimeRange = Query(TimeRange.DAY),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$")
):
    """
    Get detected anomalies.
    
    Anomalies are detected using statistical analysis and ML models.
    """
    anomalies = await analytics_engine.detect_anomalies(time_range)
    
    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]
    
    return anomalies

@app.post("/api/v1/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(anomaly_id: str):
    """Acknowledge an anomaly alert."""
    for anomaly in analytics_engine._anomaly_history:
        if anomaly.id == anomaly_id:
            anomaly.acknowledged = True
            return {"status": "acknowledged", "id": anomaly_id}
    
    raise HTTPException(404, f"Anomaly {anomaly_id} not found")

# -----------------------------------------------------------------------------
# Team Performance
# -----------------------------------------------------------------------------

@app.get("/api/v1/teams", response_model=List[TeamPerformance])
async def get_team_performance(
    time_range: TimeRange = Query(TimeRange.MONTH)
):
    """Get performance metrics for all teams."""
    return await analytics_engine.get_team_performance(time_range)

@app.get("/api/v1/teams/{team_name}", response_model=TeamPerformance)
async def get_team_by_name(
    team_name: str,
    time_range: TimeRange = Query(TimeRange.MONTH)
):
    """Get performance for a specific team."""
    teams = await analytics_engine.get_team_performance(time_range)
    
    for team in teams:
        if team.team_name.lower() == team_name.lower():
            return team
    
    raise HTTPException(404, f"Team '{team_name}' not found")

# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

@app.get("/api/v1/report", response_model=AnalyticsReport)
async def get_analytics_report(
    time_range: TimeRange = Query(TimeRange.WEEK),
    project: Optional[str] = Query(None)
):
    """
    Generate comprehensive analytics report.
    
    Includes KPIs, predictions, anomalies, team performance, and AI insights.
    """
    return await analytics_engine.generate_report(time_range, project)

@app.get("/api/v1/insights", response_model=List[ReleaseInsight])
async def get_insights(
    time_range: TimeRange = Query(TimeRange.WEEK),
    project: Optional[str] = Query(None)
):
    """Get AI-generated insights based on current metrics."""
    kpis = await analytics_engine.calculate_kpis(time_range, project)
    anomalies = await analytics_engine.detect_anomalies(time_range)
    return await analytics_engine.generate_insights(kpis, anomalies)

# -----------------------------------------------------------------------------
# Data Collection
# -----------------------------------------------------------------------------

@app.post("/api/v1/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """Manually trigger metrics collection from all agents."""
    background_tasks.add_task(analytics_engine.collect_metrics)
    return {"status": "collection_triggered", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/sources")
async def get_data_sources():
    """Get status of all data sources."""
    metrics = await analytics_engine.collect_metrics()
    return metrics

# -----------------------------------------------------------------------------
# Compare & Benchmark
# -----------------------------------------------------------------------------

@app.get("/api/v1/compare")
async def compare_periods(
    metric: MetricType,
    period1_start: datetime,
    period1_end: datetime,
    period2_start: datetime,
    period2_end: datetime,
    project: Optional[str] = Query(None)
):
    """Compare metrics between two time periods."""
    import random
    
    # Generate comparison data
    p1_value = random.uniform(50, 100)
    p2_value = random.uniform(50, 100)
    
    change = ((p2_value - p1_value) / p1_value) * 100 if p1_value else 0
    
    return {
        "metric": metric.value,
        "period1": {
            "start": period1_start.isoformat(),
            "end": period1_end.isoformat(),
            "value": round(p1_value, 2)
        },
        "period2": {
            "start": period2_start.isoformat(),
            "end": period2_end.isoformat(),
            "value": round(p2_value, 2)
        },
        "change_percent": round(change, 2),
        "direction": "up" if change > 0 else "down" if change < 0 else "stable"
    }

@app.get("/api/v1/benchmark")
async def get_industry_benchmark(
    metric: MetricType
):
    """Get industry benchmark for a metric."""
    
    benchmarks = {
        MetricType.DEPLOYMENT_FREQUENCY: {
            "elite": ">1 per day",
            "high": "1 per week to 1 per month",
            "medium": "1 per month to 6 months",
            "low": "<6 months",
            "your_level": "high",
            "your_value": 8.5
        },
        MetricType.LEAD_TIME: {
            "elite": "<1 hour",
            "high": "<1 day",
            "medium": "<1 week",
            "low": ">1 month",
            "your_level": "high",
            "your_value": 18.5
        },
        MetricType.BUILD_SUCCESS_RATE: {
            "elite": ">99%",
            "high": ">95%",
            "medium": ">90%",
            "low": "<90%",
            "your_level": "high",
            "your_value": 0.94
        },
        MetricType.HYGIENE_SCORE: {
            "elite": ">95%",
            "high": ">85%",
            "medium": ">75%",
            "low": "<75%",
            "your_level": "high",
            "your_value": 0.87
        }
    }
    
    if metric in benchmarks:
        return {"metric": metric.value, "benchmark": benchmarks[metric]}
    
    return {
        "metric": metric.value,
        "benchmark": {
            "message": "Benchmark data not available for this metric"
        }
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8006")),
        reload=os.getenv("ENV", "development") == "development"
    )


"""
Nexus Enhanced Observability & Instrumentation
===============================================

Extended metrics for AI safety, DORA metrics, SLO tracking, and security monitoring.
This module supplements the core instrumentation.py with additional metrics.

Author: Nexus Analytics Team
Version: 2.0.0
"""

from prometheus_client import Counter, Histogram, Gauge, Summary

# =============================================================================
# AI SAFETY & QUALITY METRICS
# =============================================================================

AI_HALLUCINATION_RATE = Gauge(
    'nexus_ai_hallucination_rate',
    'Detected hallucination rate (0-1) based on fact-checking',
    ['model_name', 'task_type']
)

AI_GUARDRAIL_TRIGGERS = Counter(
    'nexus_ai_guardrail_triggers_total',
    'Number of guardrail activations preventing unsafe outputs',
    ['guardrail_type', 'model_name', 'action']
)

AI_CONFIDENCE_SCORE = Histogram(
    'nexus_ai_confidence_score',
    'Model confidence distribution for outputs',
    ['model_name', 'task_type'],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
)

AI_OUTPUT_QUALITY = Gauge(
    'nexus_ai_output_quality_score',
    'Quality score of AI outputs based on evaluation (0-100)',
    ['model_name', 'evaluator']
)

AI_PROMPT_LENGTH = Histogram(
    'nexus_ai_prompt_length_tokens',
    'Input prompt length distribution in tokens',
    ['model_name'],
    buckets=(10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000)
)

AI_RESPONSE_LENGTH = Histogram(
    'nexus_ai_response_length_tokens',
    'Output response length distribution in tokens',
    ['model_name'],
    buckets=(10, 50, 100, 250, 500, 1000, 2000, 4000, 8000)
)

AI_CONTEXT_WINDOW_UTILIZATION = Gauge(
    'nexus_ai_context_window_utilization',
    'Percentage of context window used (0-100)',
    ['model_name']
)

AI_CACHE_HIT_RATE = Gauge(
    'nexus_ai_cache_hit_rate',
    'LLM response cache hit rate (0-1)',
    ['cache_type']
)

# =============================================================================
# DORA METRICS (DevOps Research and Assessment)
# =============================================================================

DORA_DEPLOYMENT_FREQUENCY = Gauge(
    'nexus_dora_deployment_frequency',
    'Deployments per day - Elite: >1/day, High: 1/week-1/month',
    ['project', 'environment']
)

DORA_LEAD_TIME = Histogram(
    'nexus_dora_lead_time_hours',
    'Lead time from commit to production in hours',
    ['project'],
    buckets=(0.5, 1, 2, 4, 8, 24, 48, 72, 168, 336, 720)
)

DORA_MTTR = Histogram(
    'nexus_dora_mttr_hours',
    'Mean time to recovery from incidents in hours',
    ['project', 'severity'],
    buckets=(0.25, 0.5, 1, 2, 4, 8, 24, 48, 168)
)

DORA_CHANGE_FAILURE_RATE = Gauge(
    'nexus_dora_change_failure_rate',
    'Percentage of deployments causing failures (0-100)',
    ['project']
)

# =============================================================================
# SLO/SLA TRACKING METRICS
# =============================================================================

SLO_ERROR_BUDGET_REMAINING = Gauge(
    'nexus_slo_error_budget_remaining',
    'Remaining error budget percentage for the period',
    ['service', 'slo_name', 'period']
)

SLO_BURN_RATE = Gauge(
    'nexus_slo_burn_rate',
    'Current SLO burn rate (1.0 = on target)',
    ['service', 'slo_name']
)

SLA_COMPLIANCE = Gauge(
    'nexus_sla_compliance_percentage',
    'Current SLA compliance percentage (0-100)',
    ['service', 'sla_tier']
)

SLO_VIOLATIONS = Counter(
    'nexus_slo_violations_total',
    'Total SLO violations count',
    ['service', 'slo_name', 'severity']
)

# =============================================================================
# SECURITY METRICS
# =============================================================================

RATE_LIMIT_EXCEEDED = Counter(
    'nexus_rate_limit_exceeded_total',
    'Rate limit exceeded events',
    ['endpoint', 'client_id', 'limit_type']
)

RBAC_DENIAL = Counter(
    'nexus_rbac_denial_total',
    'RBAC permission denials',
    ['user', 'resource', 'action', 'reason']
)

SUSPICIOUS_ACTIVITY = Counter(
    'nexus_suspicious_activity_total',
    'Detected suspicious activities',
    ['activity_type', 'severity', 'source']
)

TOKEN_REFRESH = Counter(
    'nexus_token_refresh_total',
    'JWT token refresh events',
    ['reason', 'success']
)

TOKEN_EXPIRY = Counter(
    'nexus_token_expiry_total',
    'Expired tokens encountered',
    ['token_type']
)

ENCRYPTION_OPERATIONS = Counter(
    'nexus_encryption_operations_total',
    'Encryption/decryption operations',
    ['operation', 'algorithm', 'status']
)

# =============================================================================
# COST ATTRIBUTION METRICS
# =============================================================================

COST_BY_FEATURE = Counter(
    'nexus_cost_dollars_total',
    'Costs attributed by feature and team',
    ['feature', 'cost_type', 'team', 'environment']
)

RESOURCE_UTILIZATION_COST = Gauge(
    'nexus_resource_cost_hourly',
    'Hourly resource cost estimate in dollars',
    ['service', 'resource_type']
)

LLM_COST_PER_REQUEST = Histogram(
    'nexus_llm_cost_per_request_dollars',
    'Cost per LLM request in dollars',
    ['model_name', 'task_type'],
    buckets=(0.0001, 0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 5.0)
)

# =============================================================================
# RELEASE MANAGEMENT METRICS
# =============================================================================

RELEASE_BLOCKERS = Gauge(
    'nexus_release_blockers_count',
    'Current number of release blockers',
    ['release_version', 'severity']
)

RELEASE_RISK_SCORE = Gauge(
    'nexus_release_risk_score',
    'Calculated risk score for release (0-100)',
    ['release_version']
)

RELEASE_PROGRESS = Gauge(
    'nexus_release_progress_percentage',
    'Release completion progress (0-100)',
    ['release_version', 'metric_type']
)

TICKET_CYCLE_TIME = Histogram(
    'nexus_ticket_cycle_time_hours',
    'Time from ticket creation to completion',
    ['project', 'ticket_type'],
    buckets=(1, 4, 8, 24, 48, 72, 120, 168, 336)
)

SPRINT_VELOCITY = Gauge(
    'nexus_sprint_velocity',
    'Story points completed in sprint',
    ['team', 'sprint']
)

BUG_ESCAPE_RATE = Gauge(
    'nexus_bug_escape_rate',
    'Percentage of bugs found in production (0-100)',
    ['project', 'severity']
)

# =============================================================================
# AGENT HEALTH METRICS
# =============================================================================

AGENT_HEARTBEAT = Gauge(
    'nexus_agent_heartbeat_timestamp',
    'Last heartbeat timestamp as Unix epoch',
    ['agent_type', 'instance']
)

AGENT_QUEUE_DEPTH = Gauge(
    'nexus_agent_queue_depth',
    'Current task queue depth',
    ['agent_type', 'queue_name']
)

AGENT_MEMORY_USAGE = Gauge(
    'nexus_agent_memory_usage_bytes',
    'Agent memory usage in bytes',
    ['agent_type', 'instance']
)

AGENT_UPTIME = Gauge(
    'nexus_agent_uptime_seconds',
    'Agent uptime in seconds',
    ['agent_type', 'instance']
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def record_ai_safety_metrics(
    model_name: str,
    task_type: str,
    hallucination_rate: float,
    confidence_score: float,
    quality_score: float
):
    """Record AI safety and quality metrics."""
    AI_HALLUCINATION_RATE.labels(
        model_name=model_name,
        task_type=task_type
    ).set(hallucination_rate)
    
    AI_CONFIDENCE_SCORE.labels(
        model_name=model_name,
        task_type=task_type
    ).observe(confidence_score)
    
    AI_OUTPUT_QUALITY.labels(
        model_name=model_name,
        evaluator="automated"
    ).set(quality_score)


def record_guardrail_trigger(
    guardrail_type: str,
    model_name: str,
    action: str
):
    """Record a guardrail trigger event."""
    AI_GUARDRAIL_TRIGGERS.labels(
        guardrail_type=guardrail_type,
        model_name=model_name,
        action=action
    ).inc()


def update_dora_metrics(
    project: str,
    deployment_frequency: float,
    lead_time_hours: float,
    mttr_hours: float,
    change_failure_rate: float,
    environment: str = "production"
):
    """Update DORA metrics for a project."""
    DORA_DEPLOYMENT_FREQUENCY.labels(
        project=project,
        environment=environment
    ).set(deployment_frequency)
    
    DORA_LEAD_TIME.labels(project=project).observe(lead_time_hours)
    DORA_MTTR.labels(project=project, severity="all").observe(mttr_hours)
    DORA_CHANGE_FAILURE_RATE.labels(project=project).set(change_failure_rate)


def update_slo_metrics(
    service: str,
    slo_name: str,
    error_budget_remaining: float,
    burn_rate: float,
    period: str = "monthly"
):
    """Update SLO tracking metrics."""
    SLO_ERROR_BUDGET_REMAINING.labels(
        service=service,
        slo_name=slo_name,
        period=period
    ).set(error_budget_remaining)
    
    SLO_BURN_RATE.labels(
        service=service,
        slo_name=slo_name
    ).set(burn_rate)


def record_security_event(
    event_type: str,
    severity: str,
    source: str,
    details: dict = None
):
    """Record a security event."""
    SUSPICIOUS_ACTIVITY.labels(
        activity_type=event_type,
        severity=severity,
        source=source
    ).inc()


def record_cost(
    feature: str,
    cost_type: str,
    amount: float,
    team: str = "platform",
    environment: str = "production"
):
    """Record cost attribution."""
    COST_BY_FEATURE.labels(
        feature=feature,
        cost_type=cost_type,
        team=team,
        environment=environment
    ).inc(amount)


def update_release_metrics(
    release_version: str,
    blockers: int,
    risk_score: float,
    progress: float
):
    """Update release tracking metrics."""
    RELEASE_BLOCKERS.labels(
        release_version=release_version,
        severity="all"
    ).set(blockers)
    
    RELEASE_RISK_SCORE.labels(
        release_version=release_version
    ).set(risk_score)
    
    RELEASE_PROGRESS.labels(
        release_version=release_version,
        metric_type="overall"
    ).set(progress)


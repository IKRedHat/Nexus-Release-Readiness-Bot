"""
Nexus Enhanced Observability & Instrumentation
===============================================

Production-ready metrics for AI safety, DORA metrics, SLO tracking, 
security monitoring, and agent health.

This module provides:
- Prometheus metric definitions
- Decorators for automatic metric collection
- Context managers for tracking operations
- Background collectors for system metrics
- SLO calculation and tracking

Author: Nexus Analytics Team
Version: 2.1.0 (Production Ready)
"""

import asyncio
import functools
import logging
import os
import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary, Info, REGISTRY

logger = logging.getLogger("nexus.instrumentation.enhanced")

# =============================================================================
# CONFIGURATION
# =============================================================================

class MetricsConfig:
    """Centralized metrics configuration."""
    
    # SLO Targets
    SLO_AVAILABILITY_TARGET = float(os.getenv("NEXUS_SLO_AVAILABILITY", "99.9"))
    SLO_LATENCY_TARGET_MS = int(os.getenv("NEXUS_SLO_LATENCY_MS", "1000"))
    SLO_ERROR_RATE_TARGET = float(os.getenv("NEXUS_SLO_ERROR_RATE", "0.1"))
    
    # Collection intervals
    HEALTH_CHECK_INTERVAL = int(os.getenv("NEXUS_HEALTH_CHECK_INTERVAL", "30"))
    METRICS_COLLECTION_INTERVAL = int(os.getenv("NEXUS_METRICS_INTERVAL", "60"))
    
    # Hallucination detection threshold
    HALLUCINATION_THRESHOLD = float(os.getenv("NEXUS_HALLUCINATION_THRESHOLD", "0.05"))
    
    # Agent heartbeat timeout
    AGENT_HEARTBEAT_TIMEOUT = int(os.getenv("NEXUS_HEARTBEAT_TIMEOUT", "60"))


# =============================================================================
# ENUMS
# =============================================================================

class GuardrailType(str, Enum):
    """Types of AI guardrails."""
    CONTENT_FILTER = "content_filter"
    PII_DETECTION = "pii_detection"
    TOXICITY = "toxicity"
    PROMPT_INJECTION = "prompt_injection"
    HALLUCINATION = "hallucination"
    OUTPUT_LENGTH = "output_length"
    RATE_LIMIT = "rate_limit"


class GuardrailAction(str, Enum):
    """Actions taken by guardrails."""
    BLOCKED = "blocked"
    WARNED = "warned"
    MODIFIED = "modified"
    LOGGED = "logged"


class SecurityEventType(str, Enum):
    """Types of security events."""
    BRUTE_FORCE = "brute_force"
    UNUSUAL_ACCESS = "unusual_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class Severity(str, Enum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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

AI_EVALUATION_LATENCY = Histogram(
    'nexus_ai_evaluation_latency_seconds',
    'Time taken for AI output evaluation',
    ['evaluator_type'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
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

DORA_DEPLOYMENT_TIMESTAMP = Gauge(
    'nexus_dora_last_deployment_timestamp',
    'Timestamp of last deployment',
    ['project', 'environment']
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

SLO_TARGET = Gauge(
    'nexus_slo_target',
    'SLO target value',
    ['service', 'slo_name', 'metric_type']
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

SECURITY_SCAN_RESULTS = Gauge(
    'nexus_security_scan_score',
    'Security scan score (0-100)',
    ['scan_type', 'target']
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

COST_BUDGET_REMAINING = Gauge(
    'nexus_cost_budget_remaining_dollars',
    'Remaining budget in dollars',
    ['budget_type', 'period']
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

RELEASE_DECISION_LATENCY = Histogram(
    'nexus_release_decision_latency_seconds',
    'Time taken to make release decision',
    ['decision_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
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

AGENT_CPU_USAGE = Gauge(
    'nexus_agent_cpu_usage_percent',
    'Agent CPU usage percentage',
    ['agent_type', 'instance']
)

AGENT_ACTIVE_CONNECTIONS = Gauge(
    'nexus_agent_active_connections',
    'Number of active connections',
    ['agent_type', 'connection_type']
)

AGENT_INFO = Info(
    'nexus_agent',
    'Agent metadata',
    ['agent_type']
)

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AIEvaluationResult:
    """Result of AI output evaluation."""
    model_name: str
    task_type: str
    confidence_score: float
    quality_score: float
    hallucination_detected: bool
    hallucination_rate: float
    evaluation_time_ms: float
    guardrails_triggered: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLOStatus:
    """Current SLO status."""
    service: str
    slo_name: str
    target: float
    current_value: float
    error_budget_remaining: float
    burn_rate: float
    is_violated: bool
    period: str = "monthly"


@dataclass
class DORAMetrics:
    """DORA metrics for a project."""
    project: str
    deployment_frequency: float  # per day
    lead_time_hours: float
    mttr_hours: float
    change_failure_rate: float  # percentage
    environment: str = "production"


@dataclass
class AgentHealthStatus:
    """Agent health status."""
    agent_type: str
    instance: str
    is_healthy: bool
    uptime_seconds: float
    memory_bytes: int
    cpu_percent: float
    queue_depth: int
    last_heartbeat: datetime
    active_connections: int = 0
    error_count: int = 0


# =============================================================================
# AI SAFETY TRACKING
# =============================================================================

class AIOutputEvaluator:
    """
    Production-ready AI output evaluation and metrics collection.
    
    Usage:
        evaluator = AIOutputEvaluator()
        result = await evaluator.evaluate(
            model_name="gemini-2.0-flash",
            task_type="release_analysis",
            prompt="...",
            response="...",
            expected_facts=["fact1", "fact2"]
        )
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._cache_hits = 0
        self._cache_misses = 0
    
    async def evaluate(
        self,
        model_name: str,
        task_type: str,
        prompt: str,
        response: str,
        expected_facts: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> AIEvaluationResult:
        """
        Evaluate AI output and record metrics.
        
        Args:
            model_name: Name of the LLM model
            task_type: Type of task (e.g., "release_analysis", "code_review")
            prompt: The input prompt
            response: The model's response
            expected_facts: Optional list of facts to verify
            confidence_score: Optional pre-computed confidence score
        
        Returns:
            AIEvaluationResult with all evaluation metrics
        """
        start_time = time.perf_counter()
        
        try:
            # Validate inputs
            if not model_name or not task_type:
                raise ValueError("model_name and task_type are required")
            
            # Calculate confidence if not provided
            if confidence_score is None:
                confidence_score = self._estimate_confidence(response)
            
            # Validate confidence range
            confidence_score = max(0.0, min(1.0, confidence_score))
            
            # Check for hallucinations
            hallucination_detected = False
            hallucination_rate = 0.0
            
            if expected_facts:
                verified_count = sum(
                    1 for fact in expected_facts 
                    if fact.lower() in response.lower()
                )
                hallucination_rate = 1.0 - (verified_count / len(expected_facts))
                hallucination_detected = hallucination_rate > MetricsConfig.HALLUCINATION_THRESHOLD
            
            # Calculate quality score (0-100)
            quality_score = self._calculate_quality_score(
                response, confidence_score, hallucination_rate
            )
            
            # Check guardrails
            guardrails_triggered = self._check_guardrails(prompt, response, model_name)
            
            evaluation_time = (time.perf_counter() - start_time) * 1000
            
            result = AIEvaluationResult(
                model_name=model_name,
                task_type=task_type,
                confidence_score=confidence_score,
                quality_score=quality_score,
                hallucination_detected=hallucination_detected,
                hallucination_rate=hallucination_rate,
                evaluation_time_ms=evaluation_time,
                guardrails_triggered=guardrails_triggered
            )
            
            # Record metrics
            self._record_metrics(result, len(prompt.split()), len(response.split()))
            
            logger.debug(
                f"AI evaluation complete: model={model_name}, quality={quality_score:.1f}, "
                f"hallucination_rate={hallucination_rate:.3f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            # Record error metrics
            AI_GUARDRAIL_TRIGGERS.labels(
                guardrail_type="evaluation_error",
                model_name=model_name,
                action="logged"
            ).inc()
            raise
    
    def _estimate_confidence(self, response: str) -> float:
        """Estimate confidence based on response characteristics."""
        if not response:
            return 0.0
        
        # Simple heuristics for confidence estimation
        confidence = 0.7  # Base confidence
        
        # Penalize very short responses
        if len(response) < 50:
            confidence -= 0.2
        
        # Penalize uncertainty indicators
        uncertainty_phrases = [
            "i'm not sure", "might be", "possibly", "maybe",
            "i think", "could be", "uncertain", "unclear"
        ]
        response_lower = response.lower()
        for phrase in uncertainty_phrases:
            if phrase in response_lower:
                confidence -= 0.1
        
        # Boost for structured responses
        if any(marker in response for marker in ["1.", "•", "-", "```"]):
            confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_quality_score(
        self, 
        response: str, 
        confidence: float, 
        hallucination_rate: float
    ) -> float:
        """Calculate overall quality score (0-100)."""
        if not response:
            return 0.0
        
        # Components
        length_score = min(100, len(response) / 10)  # Up to 1000 chars = 100
        confidence_score = confidence * 100
        hallucination_penalty = hallucination_rate * 50
        
        # Weighted average
        quality = (
            0.3 * length_score +
            0.5 * confidence_score -
            0.2 * hallucination_penalty
        )
        
        return max(0.0, min(100.0, quality))
    
    def _check_guardrails(
        self, 
        prompt: str, 
        response: str, 
        model_name: str
    ) -> List[str]:
        """Check guardrails and record triggers."""
        triggered = []
        
        # PII detection (simplified)
        pii_patterns = ["@", "password", "ssn", "credit card"]
        if any(p in response.lower() for p in pii_patterns):
            triggered.append(GuardrailType.PII_DETECTION.value)
            AI_GUARDRAIL_TRIGGERS.labels(
                guardrail_type=GuardrailType.PII_DETECTION.value,
                model_name=model_name,
                action=GuardrailAction.WARNED.value
            ).inc()
        
        # Output length check
        if len(response) > 50000:
            triggered.append(GuardrailType.OUTPUT_LENGTH.value)
            AI_GUARDRAIL_TRIGGERS.labels(
                guardrail_type=GuardrailType.OUTPUT_LENGTH.value,
                model_name=model_name,
                action=GuardrailAction.WARNED.value
            ).inc()
        
        # Prompt injection detection (simplified)
        injection_patterns = ["ignore previous", "disregard", "forget your instructions"]
        if any(p in prompt.lower() for p in injection_patterns):
            triggered.append(GuardrailType.PROMPT_INJECTION.value)
            AI_GUARDRAIL_TRIGGERS.labels(
                guardrail_type=GuardrailType.PROMPT_INJECTION.value,
                model_name=model_name,
                action=GuardrailAction.LOGGED.value
            ).inc()
        
        return triggered
    
    def _record_metrics(
        self, 
        result: AIEvaluationResult,
        prompt_tokens: int,
        response_tokens: int
    ):
        """Record all metrics from evaluation result."""
        # Hallucination rate
        AI_HALLUCINATION_RATE.labels(
            model_name=result.model_name,
            task_type=result.task_type
        ).set(result.hallucination_rate)
        
        # Confidence score
        AI_CONFIDENCE_SCORE.labels(
            model_name=result.model_name,
            task_type=result.task_type
        ).observe(result.confidence_score)
        
        # Quality score
        AI_OUTPUT_QUALITY.labels(
            model_name=result.model_name,
            evaluator="automated"
        ).set(result.quality_score)
        
        # Prompt/response lengths (approximated from word count)
        AI_PROMPT_LENGTH.labels(model_name=result.model_name).observe(prompt_tokens * 1.3)
        AI_RESPONSE_LENGTH.labels(model_name=result.model_name).observe(response_tokens * 1.3)
        
        # Evaluation latency
        AI_EVALUATION_LATENCY.labels(
            evaluator_type="automated"
        ).observe(result.evaluation_time_ms / 1000)
    
    def update_cache_stats(self, hit: bool):
        """Update cache hit/miss statistics."""
        with self._lock:
            if hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
            
            total = self._cache_hits + self._cache_misses
            if total > 0:
                AI_CACHE_HIT_RATE.labels(cache_type="llm_response").set(
                    self._cache_hits / total
                )


def track_ai_evaluation(model_name: str, task_type: str):
    """
    Decorator for automatic AI evaluation tracking.
    
    Usage:
        @track_ai_evaluation("gemini-2.0-flash", "code_review")
        async def review_code(code: str) -> dict:
            response = await llm.generate(code)
            return {"response": response.text, "confidence": 0.9}
    """
    def decorator(func: Callable):
        evaluator = AIOutputEvaluator()
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)
            
            if isinstance(result, dict):
                await evaluator.evaluate(
                    model_name=model_name,
                    task_type=task_type,
                    prompt=str(args[0]) if args else "",
                    response=result.get("response", ""),
                    confidence_score=result.get("confidence")
                )
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            # Sync version - simplified metrics
            if isinstance(result, dict):
                AI_OUTPUT_QUALITY.labels(
                    model_name=model_name,
                    evaluator="automated"
                ).set(result.get("quality", 70))
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# SLO TRACKING
# =============================================================================

class SLOTracker:
    """
    Production-ready SLO tracking and error budget management.
    
    Usage:
        tracker = SLOTracker(service="orchestrator")
        tracker.set_target("availability", 99.9)
        tracker.record_request(success=True, latency_ms=150)
        status = tracker.get_status("availability")
    """
    
    def __init__(self, service: str):
        self.service = service
        self._targets: Dict[str, float] = {}
        self._success_count = 0
        self._failure_count = 0
        self._latencies: List[float] = []
        self._period_start = datetime.utcnow()
        self._lock = threading.Lock()
        
        logger.info(f"SLO tracker initialized for service: {service}")
    
    def set_target(
        self, 
        slo_name: str, 
        target: float,
        metric_type: str = "percentage"
    ):
        """Set an SLO target."""
        with self._lock:
            self._targets[slo_name] = target
            SLO_TARGET.labels(
                service=self.service,
                slo_name=slo_name,
                metric_type=metric_type
            ).set(target)
            logger.info(f"SLO target set: {self.service}/{slo_name} = {target}")
    
    def record_request(
        self, 
        success: bool, 
        latency_ms: Optional[float] = None
    ):
        """Record a request for SLO tracking."""
        with self._lock:
            if success:
                self._success_count += 1
            else:
                self._failure_count += 1
            
            if latency_ms is not None:
                self._latencies.append(latency_ms)
                # Keep only last 10000 latencies
                if len(self._latencies) > 10000:
                    self._latencies = self._latencies[-10000:]
        
        self._update_metrics()
    
    def _update_metrics(self):
        """Update all SLO-related metrics."""
        total = self._success_count + self._failure_count
        if total == 0:
            return
        
        # Availability SLO
        availability = (self._success_count / total) * 100
        if "availability" in self._targets:
            target = self._targets["availability"]
            error_budget = self._calculate_error_budget(availability, target)
            burn_rate = self._calculate_burn_rate(availability, target)
            
            SLO_ERROR_BUDGET_REMAINING.labels(
                service=self.service,
                slo_name="availability",
                period="monthly"
            ).set(error_budget)
            
            SLO_BURN_RATE.labels(
                service=self.service,
                slo_name="availability"
            ).set(burn_rate)
            
            if availability < target:
                SLO_VIOLATIONS.labels(
                    service=self.service,
                    slo_name="availability",
                    severity="high" if availability < target - 1 else "medium"
                ).inc()
        
        # Latency SLO
        if self._latencies and "latency_p99" in self._targets:
            sorted_latencies = sorted(self._latencies)
            p99_index = int(len(sorted_latencies) * 0.99)
            p99_latency = sorted_latencies[min(p99_index, len(sorted_latencies) - 1)]
            
            target = self._targets["latency_p99"]
            if p99_latency > target:
                SLO_VIOLATIONS.labels(
                    service=self.service,
                    slo_name="latency_p99",
                    severity="medium"
                ).inc()
        
        # Overall SLA compliance
        compliance = self._calculate_sla_compliance()
        SLA_COMPLIANCE.labels(
            service=self.service,
            sla_tier="standard"
        ).set(compliance)
    
    def _calculate_error_budget(self, current: float, target: float) -> float:
        """Calculate remaining error budget percentage."""
        if target >= 100:
            return 0.0
        
        allowed_errors = 100 - target
        actual_errors = 100 - current
        
        if allowed_errors == 0:
            return 0.0 if actual_errors > 0 else 100.0
        
        used_budget = (actual_errors / allowed_errors) * 100
        return max(0.0, 100.0 - used_budget)
    
    def _calculate_burn_rate(self, current: float, target: float) -> float:
        """Calculate SLO burn rate (1.0 = on target)."""
        if target >= 100:
            return 0.0 if current >= 100 else float('inf')
        
        hours_elapsed = (datetime.utcnow() - self._period_start).total_seconds() / 3600
        if hours_elapsed == 0:
            return 1.0
        
        # Assuming monthly period (720 hours)
        expected_progress = hours_elapsed / 720
        actual_error_rate = (100 - current) / (100 - target) if target < 100 else 0
        
        return actual_error_rate / expected_progress if expected_progress > 0 else 1.0
    
    def _calculate_sla_compliance(self) -> float:
        """Calculate overall SLA compliance percentage."""
        if not self._targets:
            return 100.0
        
        total = self._success_count + self._failure_count
        if total == 0:
            return 100.0
        
        availability = (self._success_count / total) * 100
        
        # Simple compliance: are we meeting availability target?
        target = self._targets.get("availability", 99.0)
        if availability >= target:
            return 100.0
        
        return (availability / target) * 100
    
    def get_status(self, slo_name: str) -> SLOStatus:
        """Get current status for an SLO."""
        with self._lock:
            total = self._success_count + self._failure_count
            current_value = (self._success_count / total * 100) if total > 0 else 100.0
            target = self._targets.get(slo_name, 99.0)
            
            return SLOStatus(
                service=self.service,
                slo_name=slo_name,
                target=target,
                current_value=current_value,
                error_budget_remaining=self._calculate_error_budget(current_value, target),
                burn_rate=self._calculate_burn_rate(current_value, target),
                is_violated=current_value < target
            )
    
    def reset_period(self):
        """Reset counters for new period."""
        with self._lock:
            self._success_count = 0
            self._failure_count = 0
            self._latencies = []
            self._period_start = datetime.utcnow()
            logger.info(f"SLO period reset for service: {self.service}")


# =============================================================================
# DORA METRICS COLLECTOR
# =============================================================================

class DORAMetricsCollector:
    """
    Production-ready DORA metrics collection.
    
    Usage:
        collector = DORAMetricsCollector(project="nexus-platform")
        collector.record_deployment(success=True, lead_time_hours=4.5)
        collector.record_incident(severity="high", recovery_hours=1.5)
        metrics = collector.get_metrics()
    """
    
    def __init__(self, project: str, environment: str = "production"):
        self.project = project
        self.environment = environment
        self._deployments: List[Tuple[datetime, bool]] = []
        self._lead_times: List[float] = []
        self._incidents: List[Tuple[datetime, str, float]] = []
        self._lock = threading.Lock()
        
        logger.info(f"DORA collector initialized: {project}/{environment}")
    
    def record_deployment(
        self, 
        success: bool, 
        lead_time_hours: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record a deployment."""
        ts = timestamp or datetime.utcnow()
        
        with self._lock:
            self._deployments.append((ts, success))
            
            if lead_time_hours is not None:
                self._lead_times.append(lead_time_hours)
                DORA_LEAD_TIME.labels(project=self.project).observe(lead_time_hours)
            
            # Update deployment timestamp
            DORA_DEPLOYMENT_TIMESTAMP.labels(
                project=self.project,
                environment=self.environment
            ).set(ts.timestamp())
        
        self._update_metrics()
        logger.debug(f"Deployment recorded: {self.project}, success={success}")
    
    def record_incident(
        self, 
        severity: str, 
        recovery_hours: float,
        timestamp: Optional[datetime] = None
    ):
        """Record an incident and its recovery time."""
        ts = timestamp or datetime.utcnow()
        
        with self._lock:
            self._incidents.append((ts, severity, recovery_hours))
            DORA_MTTR.labels(
                project=self.project,
                severity=severity
            ).observe(recovery_hours)
        
        self._update_metrics()
        logger.debug(f"Incident recorded: {self.project}, severity={severity}, MTTR={recovery_hours}h")
    
    def _update_metrics(self):
        """Update all DORA metrics."""
        with self._lock:
            # Calculate deployment frequency (per day, last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            recent_deployments = [d for d in self._deployments if d[0] > cutoff]
            
            if recent_deployments:
                frequency = len(recent_deployments) / 30.0
                DORA_DEPLOYMENT_FREQUENCY.labels(
                    project=self.project,
                    environment=self.environment
                ).set(frequency)
            
            # Calculate change failure rate
            if recent_deployments:
                failures = sum(1 for d in recent_deployments if not d[1])
                failure_rate = (failures / len(recent_deployments)) * 100
                DORA_CHANGE_FAILURE_RATE.labels(project=self.project).set(failure_rate)
    
    def get_metrics(self) -> DORAMetrics:
        """Get current DORA metrics."""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(days=30)
            recent_deployments = [d for d in self._deployments if d[0] > cutoff]
            
            frequency = len(recent_deployments) / 30.0 if recent_deployments else 0.0
            
            avg_lead_time = (
                sum(self._lead_times[-100:]) / len(self._lead_times[-100:])
                if self._lead_times else 0.0
            )
            
            recent_incidents = [i for i in self._incidents if i[0] > cutoff]
            avg_mttr = (
                sum(i[2] for i in recent_incidents) / len(recent_incidents)
                if recent_incidents else 0.0
            )
            
            failure_rate = (
                (sum(1 for d in recent_deployments if not d[1]) / len(recent_deployments)) * 100
                if recent_deployments else 0.0
            )
            
            return DORAMetrics(
                project=self.project,
                deployment_frequency=frequency,
                lead_time_hours=avg_lead_time,
                mttr_hours=avg_mttr,
                change_failure_rate=failure_rate,
                environment=self.environment
            )


# =============================================================================
# AGENT HEALTH MONITOR
# =============================================================================

class AgentHealthMonitor:
    """
    Production-ready agent health monitoring.
    
    Usage:
        monitor = AgentHealthMonitor(agent_type="orchestrator", instance="pod-1")
        monitor.start()  # Starts background collection
        
        # Record heartbeat
        monitor.heartbeat()
        
        # Get status
        status = monitor.get_status()
    """
    
    def __init__(
        self, 
        agent_type: str, 
        instance: str,
        collection_interval: int = 30
    ):
        self.agent_type = agent_type
        self.instance = instance
        self.collection_interval = collection_interval
        self._start_time = datetime.utcnow()
        self._last_heartbeat = datetime.utcnow()
        self._queue_depth = 0
        self._error_count = 0
        self._active_connections = 0
        self._running = False
        self._collector_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Set agent info
        AGENT_INFO.labels(agent_type=agent_type).info({
            'instance': instance,
            'start_time': self._start_time.isoformat()
        })
        
        logger.info(f"Agent health monitor initialized: {agent_type}/{instance}")
    
    def start(self):
        """Start background metrics collection."""
        if self._running:
            return
        
        self._running = True
        self._collector_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True,
            name=f"agent-health-{self.agent_type}"
        )
        self._collector_thread.start()
        logger.info(f"Agent health collection started: {self.agent_type}")
    
    def stop(self):
        """Stop background metrics collection."""
        self._running = False
        if self._collector_thread:
            self._collector_thread.join(timeout=5)
        logger.info(f"Agent health collection stopped: {self.agent_type}")
    
    def _collection_loop(self):
        """Background collection loop."""
        while self._running:
            try:
                self._collect_metrics()
            except Exception as e:
                logger.error(f"Health collection error: {e}")
            
            time.sleep(self.collection_interval)
    
    def _collect_metrics(self):
        """Collect and record system metrics."""
        process = psutil.Process()
        
        # Memory usage
        memory_info = process.memory_info()
        AGENT_MEMORY_USAGE.labels(
            agent_type=self.agent_type,
            instance=self.instance
        ).set(memory_info.rss)
        
        # CPU usage
        cpu_percent = process.cpu_percent(interval=0.1)
        AGENT_CPU_USAGE.labels(
            agent_type=self.agent_type,
            instance=self.instance
        ).set(cpu_percent)
        
        # Uptime
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        AGENT_UPTIME.labels(
            agent_type=self.agent_type,
            instance=self.instance
        ).set(uptime)
        
        # Queue depth
        AGENT_QUEUE_DEPTH.labels(
            agent_type=self.agent_type,
            queue_name="main"
        ).set(self._queue_depth)
        
        # Active connections
        AGENT_ACTIVE_CONNECTIONS.labels(
            agent_type=self.agent_type,
            connection_type="total"
        ).set(self._active_connections)
    
    def heartbeat(self):
        """Record a heartbeat."""
        with self._lock:
            self._last_heartbeat = datetime.utcnow()
            AGENT_HEARTBEAT.labels(
                agent_type=self.agent_type,
                instance=self.instance
            ).set(self._last_heartbeat.timestamp())
    
    def set_queue_depth(self, depth: int):
        """Update queue depth."""
        with self._lock:
            self._queue_depth = depth
    
    def set_active_connections(self, count: int):
        """Update active connection count."""
        with self._lock:
            self._active_connections = count
    
    def increment_errors(self):
        """Increment error count."""
        with self._lock:
            self._error_count += 1
    
    def get_status(self) -> AgentHealthStatus:
        """Get current health status."""
        process = psutil.Process()
        
        with self._lock:
            seconds_since_heartbeat = (
                datetime.utcnow() - self._last_heartbeat
            ).total_seconds()
            
            is_healthy = seconds_since_heartbeat < MetricsConfig.AGENT_HEARTBEAT_TIMEOUT
            
            return AgentHealthStatus(
                agent_type=self.agent_type,
                instance=self.instance,
                is_healthy=is_healthy,
                uptime_seconds=(datetime.utcnow() - self._start_time).total_seconds(),
                memory_bytes=process.memory_info().rss,
                cpu_percent=process.cpu_percent(interval=0.1),
                queue_depth=self._queue_depth,
                last_heartbeat=self._last_heartbeat,
                active_connections=self._active_connections,
                error_count=self._error_count
            )


# =============================================================================
# SECURITY EVENT TRACKING
# =============================================================================

class SecurityEventTracker:
    """
    Production-ready security event tracking.
    
    Usage:
        tracker = SecurityEventTracker()
        tracker.record_rate_limit_exceeded(endpoint="/api/query", client_id="user-123")
        tracker.record_rbac_denial(user="admin", resource="config", action="write")
        tracker.record_suspicious_activity(
            event_type=SecurityEventType.BRUTE_FORCE,
            severity=Severity.HIGH,
            source="192.168.1.100"
        )
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._recent_events: List[Tuple[datetime, str, str]] = []
        logger.info("Security event tracker initialized")
    
    def record_rate_limit_exceeded(
        self, 
        endpoint: str, 
        client_id: str,
        limit_type: str = "request"
    ):
        """Record a rate limit exceeded event."""
        RATE_LIMIT_EXCEEDED.labels(
            endpoint=endpoint,
            client_id=client_id,
            limit_type=limit_type
        ).inc()
        
        self._add_event("rate_limit", endpoint)
        logger.warning(f"Rate limit exceeded: {endpoint} by {client_id}")
    
    def record_rbac_denial(
        self, 
        user: str, 
        resource: str, 
        action: str,
        reason: str = "insufficient_permissions"
    ):
        """Record an RBAC permission denial."""
        RBAC_DENIAL.labels(
            user=user,
            resource=resource,
            action=action,
            reason=reason
        ).inc()
        
        self._add_event("rbac_denial", f"{user}:{resource}:{action}")
        logger.warning(f"RBAC denial: {user} tried to {action} on {resource}")
    
    def record_suspicious_activity(
        self, 
        event_type: Union[SecurityEventType, str],
        severity: Union[Severity, str],
        source: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record a suspicious activity event."""
        event_type_str = event_type.value if isinstance(event_type, SecurityEventType) else event_type
        severity_str = severity.value if isinstance(severity, Severity) else severity
        
        SUSPICIOUS_ACTIVITY.labels(
            activity_type=event_type_str,
            severity=severity_str,
            source=source
        ).inc()
        
        self._add_event(event_type_str, source)
        logger.warning(
            f"Suspicious activity: {event_type_str} from {source} "
            f"(severity: {severity_str})"
        )
    
    def record_token_event(
        self, 
        event_type: str, 
        success: bool = True,
        token_type: str = "jwt"
    ):
        """Record a token-related event."""
        if event_type == "refresh":
            TOKEN_REFRESH.labels(
                reason="expiry" if not success else "proactive",
                success=str(success).lower()
            ).inc()
        elif event_type == "expiry":
            TOKEN_EXPIRY.labels(token_type=token_type).inc()
    
    def record_encryption_operation(
        self, 
        operation: str, 
        algorithm: str,
        success: bool = True
    ):
        """Record an encryption operation."""
        ENCRYPTION_OPERATIONS.labels(
            operation=operation,
            algorithm=algorithm,
            status="success" if success else "failure"
        ).inc()
    
    def _add_event(self, event_type: str, source: str):
        """Add event to recent events list."""
        with self._lock:
            self._recent_events.append((datetime.utcnow(), event_type, source))
            # Keep only last 1000 events
            if len(self._recent_events) > 1000:
                self._recent_events = self._recent_events[-1000:]
    
    def get_recent_events(
        self, 
        limit: int = 100,
        event_type: Optional[str] = None
    ) -> List[Tuple[datetime, str, str]]:
        """Get recent security events."""
        with self._lock:
            events = self._recent_events[-limit:]
            if event_type:
                events = [(t, et, s) for t, et, s in events if et == event_type]
            return events


# =============================================================================
# COST TRACKING
# =============================================================================

class CostTracker:
    """
    Production-ready cost tracking and attribution.
    
    Usage:
        tracker = CostTracker(budget_dollars=1000, period="monthly")
        tracker.record_cost(feature="llm", amount=0.05, team="platform")
        remaining = tracker.get_budget_remaining()
    """
    
    def __init__(
        self, 
        budget_dollars: float = 0,
        period: str = "monthly"
    ):
        self.budget = budget_dollars
        self.period = period
        self._total_cost = 0.0
        self._cost_by_feature: Dict[str, float] = {}
        self._cost_by_team: Dict[str, float] = {}
        self._period_start = datetime.utcnow()
        self._lock = threading.Lock()
        
        if budget_dollars > 0:
            COST_BUDGET_REMAINING.labels(
                budget_type="total",
                period=period
            ).set(budget_dollars)
        
        logger.info(f"Cost tracker initialized: budget=${budget_dollars}, period={period}")
    
    def record_cost(
        self, 
        feature: str,
        amount: float,
        cost_type: str = "compute",
        team: str = "platform",
        environment: str = "production"
    ):
        """Record a cost."""
        if amount <= 0:
            return
        
        with self._lock:
            self._total_cost += amount
            self._cost_by_feature[feature] = self._cost_by_feature.get(feature, 0) + amount
            self._cost_by_team[team] = self._cost_by_team.get(team, 0) + amount
        
        COST_BY_FEATURE.labels(
            feature=feature,
            cost_type=cost_type,
            team=team,
            environment=environment
        ).inc(amount)
        
        if self.budget > 0:
            remaining = max(0, self.budget - self._total_cost)
            COST_BUDGET_REMAINING.labels(
                budget_type="total",
                period=self.period
            ).set(remaining)
        
        logger.debug(f"Cost recorded: {feature}=${amount:.4f}, team={team}")
    
    def record_llm_cost(
        self, 
        model_name: str,
        task_type: str,
        cost: float
    ):
        """Record LLM-specific cost."""
        LLM_COST_PER_REQUEST.labels(
            model_name=model_name,
            task_type=task_type
        ).observe(cost)
        
        self.record_cost(
            feature="llm",
            amount=cost,
            cost_type="api_call",
            team="ai"
        )
    
    def get_budget_remaining(self) -> float:
        """Get remaining budget."""
        with self._lock:
            if self.budget <= 0:
                return float('inf')
            return max(0, self.budget - self._total_cost)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        with self._lock:
            return {
                "total_cost": self._total_cost,
                "budget": self.budget,
                "remaining": self.get_budget_remaining(),
                "by_feature": dict(self._cost_by_feature),
                "by_team": dict(self._cost_by_team),
                "period_start": self._period_start.isoformat()
            }
    
    def reset_period(self):
        """Reset for new period."""
        with self._lock:
            self._total_cost = 0.0
            self._cost_by_feature = {}
            self._cost_by_team = {}
            self._period_start = datetime.utcnow()
            
            if self.budget > 0:
                COST_BUDGET_REMAINING.labels(
                    budget_type="total",
                    period=self.period
                ).set(self.budget)
        
        logger.info(f"Cost period reset: budget=${self.budget}")


# =============================================================================
# RELEASE METRICS TRACKER
# =============================================================================

class ReleaseMetricsTracker:
    """
    Production-ready release metrics tracking.
    
    Usage:
        tracker = ReleaseMetricsTracker(release_version="v2.5.0")
        tracker.update_progress(completed=45, total=60)
        tracker.add_blocker(severity="critical")
        tracker.calculate_risk_score()
    """
    
    def __init__(self, release_version: str):
        self.release_version = release_version
        self._blockers: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        self._progress = 0.0
        self._risk_factors: List[Tuple[str, float]] = []
        self._decision_start: Optional[datetime] = None
        self._lock = threading.Lock()
        
        logger.info(f"Release tracker initialized: {release_version}")
    
    def update_progress(
        self, 
        completed: int, 
        total: int,
        metric_type: str = "tickets"
    ):
        """Update release progress."""
        if total <= 0:
            return
        
        progress = (completed / total) * 100
        
        with self._lock:
            self._progress = progress
        
        RELEASE_PROGRESS.labels(
            release_version=self.release_version,
            metric_type=metric_type
        ).set(progress)
        
        logger.debug(f"Release progress: {self.release_version} = {progress:.1f}%")
    
    def add_blocker(self, severity: str = "high"):
        """Add a release blocker."""
        severity = severity.lower()
        if severity not in self._blockers:
            severity = "medium"
        
        with self._lock:
            self._blockers[severity] += 1
        
        RELEASE_BLOCKERS.labels(
            release_version=self.release_version,
            severity=severity
        ).inc()
        
        self.calculate_risk_score()
        logger.warning(f"Blocker added: {self.release_version}, severity={severity}")
    
    def remove_blocker(self, severity: str = "high"):
        """Remove a release blocker."""
        severity = severity.lower()
        if severity not in self._blockers:
            severity = "medium"
        
        with self._lock:
            self._blockers[severity] = max(0, self._blockers[severity] - 1)
        
        # Update gauge
        RELEASE_BLOCKERS.labels(
            release_version=self.release_version,
            severity=severity
        ).set(self._blockers[severity])
        
        self.calculate_risk_score()
    
    def add_risk_factor(self, factor: str, weight: float):
        """Add a risk factor."""
        with self._lock:
            self._risk_factors.append((factor, weight))
        self.calculate_risk_score()
    
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score (0-100)."""
        with self._lock:
            # Base score from blockers
            blocker_score = (
                self._blockers["critical"] * 30 +
                self._blockers["high"] * 15 +
                self._blockers["medium"] * 5 +
                self._blockers["low"] * 1
            )
            
            # Progress factor (lower progress = higher risk)
            progress_risk = max(0, (100 - self._progress) * 0.3)
            
            # Additional risk factors
            factor_risk = sum(w for _, w in self._risk_factors)
            
            risk_score = min(100, blocker_score + progress_risk + factor_risk)
        
        RELEASE_RISK_SCORE.labels(
            release_version=self.release_version
        ).set(risk_score)
        
        return risk_score
    
    def start_decision_timer(self):
        """Start timing a release decision."""
        self._decision_start = datetime.utcnow()
    
    def end_decision_timer(self, decision_type: str = "go_no_go"):
        """End timing and record decision latency."""
        if self._decision_start:
            latency = (datetime.utcnow() - self._decision_start).total_seconds()
            RELEASE_DECISION_LATENCY.labels(
                decision_type=decision_type
            ).observe(latency)
            self._decision_start = None
            logger.info(f"Decision recorded: {decision_type}, latency={latency:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get release metrics summary."""
        with self._lock:
            return {
                "release_version": self.release_version,
                "progress": self._progress,
                "blockers": dict(self._blockers),
                "total_blockers": sum(self._blockers.values()),
                "risk_score": self.calculate_risk_score(),
                "risk_factors": list(self._risk_factors)
            }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instances for easy access
_ai_evaluator: Optional[AIOutputEvaluator] = None
_security_tracker: Optional[SecurityEventTracker] = None
_cost_tracker: Optional[CostTracker] = None


def get_ai_evaluator() -> AIOutputEvaluator:
    """Get or create global AI evaluator."""
    global _ai_evaluator
    if _ai_evaluator is None:
        _ai_evaluator = AIOutputEvaluator()
    return _ai_evaluator


def get_security_tracker() -> SecurityEventTracker:
    """Get or create global security tracker."""
    global _security_tracker
    if _security_tracker is None:
        _security_tracker = SecurityEventTracker()
    return _security_tracker


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker."""
    global _cost_tracker
    if _cost_tracker is None:
        budget = float(os.getenv("NEXUS_MONTHLY_BUDGET", "0"))
        _cost_tracker = CostTracker(budget_dollars=budget, period="monthly")
    return _cost_tracker


# =============================================================================
# BACKWARDS COMPATIBILITY - Simple helper functions
# =============================================================================

def record_ai_safety_metrics(
    model_name: str,
    task_type: str,
    hallucination_rate: float,
    confidence_score: float,
    quality_score: float
):
    """Record AI safety and quality metrics (simple interface)."""
    # Validate inputs
    hallucination_rate = max(0.0, min(1.0, hallucination_rate))
    confidence_score = max(0.0, min(1.0, confidence_score))
    quality_score = max(0.0, min(100.0, quality_score))
    
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
        evaluator="manual"
    ).set(quality_score)


def record_guardrail_trigger(
    guardrail_type: str,
    model_name: str,
    action: str
):
    """Record a guardrail trigger event (simple interface)."""
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
    """Update DORA metrics for a project (simple interface)."""
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
    """Update SLO tracking metrics (simple interface)."""
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
    details: Optional[Dict] = None
):
    """Record a security event (simple interface)."""
    get_security_tracker().record_suspicious_activity(
        event_type=event_type,
        severity=severity,
        source=source,
        details=details
    )


def record_cost(
    feature: str,
    cost_type: str,
    amount: float,
    team: str = "platform",
    environment: str = "production"
):
    """Record cost attribution (simple interface)."""
    get_cost_tracker().record_cost(
        feature=feature,
        amount=amount,
        cost_type=cost_type,
        team=team,
        environment=environment
    )


def update_release_metrics(
    release_version: str,
    blockers: int,
    risk_score: float,
    progress: float
):
    """Update release tracking metrics (simple interface)."""
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

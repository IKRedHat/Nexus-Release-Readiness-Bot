"""
Nexus Observability & Instrumentation
OpenTelemetry tracing, Prometheus metrics, and LLM usage tracking
"""
import os
import functools
import time
import logging
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager
from dataclasses import dataclass

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Prometheus imports
from prometheus_client import Counter, Histogram, Gauge, Summary, REGISTRY, generate_latest

logger = logging.getLogger("nexus.instrumentation")


# ============================================================================
# PROMETHEUS METRICS - GenAI / LLM
# ============================================================================

LLM_TOKENS_TOTAL = Counter(
    'nexus_llm_tokens_total',
    'Total tokens used by LLM',
    ['model_name', 'type']  # type = input or output
)

LLM_REQUESTS_TOTAL = Counter(
    'nexus_llm_requests_total',
    'Total LLM API requests',
    ['model_name', 'status']
)

LLM_LATENCY = Histogram(
    'nexus_llm_latency_seconds',
    'Time taken for LLM generation',
    ['model_name'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0)
)

LLM_COST_TOTAL = Counter(
    'nexus_llm_cost_dollars_total',
    'Estimated cost of LLM usage in dollars',
    ['model_name']
)

LLM_TOKEN_GENERATION_SPEED = Summary(
    'nexus_llm_tokens_per_second',
    'Token generation speed',
    ['model_name']
)


# ============================================================================
# PROMETHEUS METRICS - Agent & Tool Usage
# ============================================================================

TOOL_USAGE_TOTAL = Counter(
    'nexus_tool_usage_total',
    'Count of tool executions',
    ['tool_name', 'status', 'agent_type']
)

TOOL_LATENCY = Histogram(
    'nexus_tool_latency_seconds',
    'Time taken for tool execution',
    ['tool_name'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

AGENT_TASKS_TOTAL = Counter(
    'nexus_agent_tasks_total',
    'Total agent tasks processed',
    ['agent_type', 'action', 'status']
)


# ============================================================================
# PROMETHEUS METRICS - ReAct Loop
# ============================================================================

REACT_ITERATIONS = Histogram(
    'nexus_react_iterations_count',
    'Number of iterations in ReAct loop',
    ['task_type', 'status'],
    buckets=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20)
)

REACT_LOOP_DURATION = Histogram(
    'nexus_react_loop_duration_seconds',
    'Total duration of ReAct loop execution',
    ['task_type'],
    buckets=(1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

REACT_STEP_DURATION = Histogram(
    'nexus_react_step_duration_seconds',
    'Duration of each ReAct step',
    ['step_type'],  # think, act, observe
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)


# ============================================================================
# PROMETHEUS METRICS - Business Metrics
# ============================================================================

RELEASE_DECISIONS = Counter(
    'nexus_release_decisions_total',
    'Release Go/No-Go decisions',
    ['decision', 'release_version']
)

JIRA_TICKETS_PROCESSED = Counter(
    'nexus_jira_tickets_processed_total',
    'Jira tickets processed',
    ['action', 'project_key']
)

REPORTS_GENERATED = Counter(
    'nexus_reports_generated_total',
    'Reports generated',
    ['report_type', 'destination']
)


# ============================================================================
# LLM PRICING (for cost estimation)
# ============================================================================

LLM_PRICING = {
    # Google models (per 1K tokens)
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    # OpenAI models (per 1K tokens)
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    # Anthropic models (per 1K tokens)
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    # Default fallback
    "default": {"input": 0.001, "output": 0.002}
}


def estimate_llm_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost based on token usage"""
    pricing = LLM_PRICING.get(model_name, LLM_PRICING["default"])
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    return input_cost + output_cost


# ============================================================================
# OPENTELEMETRY TRACING SETUP
# ============================================================================

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    otlp_endpoint: str = None,
    enable_console_export: bool = False
) -> TracerProvider:
    """
    Configure OpenTelemetry tracing with OTLP export
    
    Args:
        service_name: Name of the service for tracing
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (default from env)
        enable_console_export: Enable console output for debugging
    
    Returns:
        Configured TracerProvider
    """
    global _tracer_provider
    
    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.environ.get("NEXUS_ENV", "development"),
        "service.namespace": "nexus"
    })
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter if endpoint configured
    otlp_endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=os.environ.get("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"
            )
            _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP tracing configured for {service_name} -> {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP exporter: {e}")
    
    # Add console exporter for debugging
    if enable_console_export or os.environ.get("OTEL_CONSOLE_EXPORT", "").lower() == "true":
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console span export enabled")
    
    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Set B3 propagator for compatibility
    set_global_textmap(B3MultiFormat())
    
    logger.info(f"Tracing setup complete for {service_name}")
    return _tracer_provider


def get_tracer(name: str = "nexus") -> trace.Tracer:
    """Get a tracer instance"""
    return trace.get_tracer(name)


def instrument_fastapi(app):
    """Instrument a FastAPI application with OpenTelemetry"""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")


def instrument_httpx():
    """Instrument HTTPX client with OpenTelemetry"""
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")


# ============================================================================
# LLM USAGE TRACKING DECORATOR
# ============================================================================

@dataclass
class LLMUsage:
    """Container for LLM usage statistics"""
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_seconds: float
    estimated_cost: float
    tokens_per_second: float


def track_llm_usage(model_name: str = "gemini-2.5-flash"):
    """
    Decorator to track LLM API usage including tokens, latency, and cost
    
    The decorated function should return a dict with optional keys:
    - input_tokens: int
    - output_tokens: int
    - usage: dict with {prompt_tokens, completion_tokens}
    
    Args:
        model_name: Name of the LLM model being used
    
    Usage:
        @track_llm_usage(model_name="gemini-2.5-flash")
        async def call_llm(prompt: str) -> dict:
            response = await llm.generate(prompt)
            return {
                "content": response.text,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer("llm")
            
            with tracer.start_as_current_span(
                f"llm.{func.__name__}",
                kind=SpanKind.CLIENT,
                attributes={"llm.model": model_name}
            ) as span:
                start_time = time.perf_counter()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Extract token counts from result
                    input_tokens = 0
                    output_tokens = 0
                    
                    if isinstance(result, dict):
                        # Direct token counts
                        input_tokens = result.get("input_tokens", 0)
                        output_tokens = result.get("output_tokens", 0)
                        
                        # OpenAI/Google style usage object
                        usage = result.get("usage", {})
                        if usage:
                            input_tokens = input_tokens or usage.get("prompt_tokens", 0)
                            output_tokens = output_tokens or usage.get("completion_tokens", 0)
                    
                    # Calculate metrics
                    duration = time.perf_counter() - start_time
                    estimated_cost = estimate_llm_cost(model_name, input_tokens, output_tokens)
                    tokens_per_second = output_tokens / duration if duration > 0 else 0
                    
                    # Record Prometheus metrics
                    LLM_TOKENS_TOTAL.labels(model_name=model_name, type="input").inc(input_tokens)
                    LLM_TOKENS_TOTAL.labels(model_name=model_name, type="output").inc(output_tokens)
                    LLM_LATENCY.labels(model_name=model_name).observe(duration)
                    LLM_COST_TOTAL.labels(model_name=model_name).inc(estimated_cost)
                    LLM_REQUESTS_TOTAL.labels(model_name=model_name, status="success").inc()
                    LLM_TOKEN_GENERATION_SPEED.labels(model_name=model_name).observe(tokens_per_second)
                    
                    # Add span attributes
                    span.set_attribute("llm.input_tokens", input_tokens)
                    span.set_attribute("llm.output_tokens", output_tokens)
                    span.set_attribute("llm.total_tokens", input_tokens + output_tokens)
                    span.set_attribute("llm.latency_seconds", duration)
                    span.set_attribute("llm.estimated_cost_usd", estimated_cost)
                    span.set_attribute("llm.tokens_per_second", tokens_per_second)
                    
                    # Attach usage info to result if dict
                    if isinstance(result, dict):
                        result["_llm_usage"] = LLMUsage(
                            model_name=model_name,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=input_tokens + output_tokens,
                            latency_seconds=duration,
                            estimated_cost=estimated_cost,
                            tokens_per_second=tokens_per_second
                        )
                    
                    logger.debug(
                        f"LLM call: model={model_name}, tokens={input_tokens}+{output_tokens}, "
                        f"latency={duration:.2f}s, cost=${estimated_cost:.6f}"
                    )
                    
                    return result
                    
                except Exception as e:
                    status = "error"
                    LLM_REQUESTS_TOTAL.labels(model_name=model_name, status="error").inc()
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                    
                finally:
                    span.set_attribute("llm.status", status)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Sync version - simpler tracking
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                LLM_LATENCY.labels(model_name=model_name).observe(duration)
                LLM_REQUESTS_TOTAL.labels(model_name=model_name, status="success").inc()
                return result
            except Exception:
                LLM_REQUESTS_TOTAL.labels(model_name=model_name, status="error").inc()
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is async"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# ============================================================================
# TOOL USAGE TRACKING DECORATOR
# ============================================================================

def track_tool_usage(tool_name: str, agent_type: str = "orchestrator"):
    """
    Decorator to track tool/action execution
    
    Args:
        tool_name: Name of the tool being executed
        agent_type: Type of agent executing the tool
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer("tool")
            
            with tracer.start_as_current_span(
                f"tool.{tool_name}",
                kind=SpanKind.INTERNAL,
                attributes={"tool.name": tool_name, "agent.type": agent_type}
            ) as span:
                start_time = time.perf_counter()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    TOOL_USAGE_TOTAL.labels(
                        tool_name=tool_name,
                        status=status,
                        agent_type=agent_type
                    ).inc()
                    TOOL_LATENCY.labels(tool_name=tool_name).observe(duration)
                    span.set_attribute("tool.duration_seconds", duration)
                    span.set_attribute("tool.status", status)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.perf_counter() - start_time
                TOOL_USAGE_TOTAL.labels(
                    tool_name=tool_name,
                    status=status,
                    agent_type=agent_type
                ).inc()
                TOOL_LATENCY.labels(tool_name=tool_name).observe(duration)
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# REACT LOOP TRACKING
# ============================================================================

@contextmanager
def track_react_loop(task_type: str = "general"):
    """
    Context manager to track ReAct loop execution
    
    Usage:
        with track_react_loop("release_check") as tracker:
            for step in range(max_steps):
                tracker.record_step("think")
                # ... thinking ...
                tracker.record_step("act")
                # ... acting ...
            tracker.complete(success=True)
    """
    tracker = ReActTracker(task_type)
    try:
        yield tracker
    finally:
        tracker.finalize()


class ReActTracker:
    """Helper class for tracking ReAct loop metrics"""
    
    def __init__(self, task_type: str):
        self.task_type = task_type
        self.start_time = time.perf_counter()
        self.step_count = 0
        self.step_start_time = None
        self.success = False
        self.tracer = get_tracer("react")
        self.span = self.tracer.start_span(
            f"react.loop.{task_type}",
            kind=SpanKind.INTERNAL
        )
    
    def record_step(self, step_type: str = "think"):
        """Record a step in the ReAct loop"""
        if self.step_start_time:
            step_duration = time.perf_counter() - self.step_start_time
            REACT_STEP_DURATION.labels(step_type=step_type).observe(step_duration)
        
        self.step_count += 1
        self.step_start_time = time.perf_counter()
    
    def complete(self, success: bool = True):
        """Mark the loop as complete"""
        self.success = success
    
    def finalize(self):
        """Record final metrics"""
        total_duration = time.perf_counter() - self.start_time
        status = "success" if self.success else "failure"
        
        REACT_ITERATIONS.labels(task_type=self.task_type, status=status).observe(self.step_count)
        REACT_LOOP_DURATION.labels(task_type=self.task_type).observe(total_duration)
        
        self.span.set_attribute("react.iterations", self.step_count)
        self.span.set_attribute("react.duration_seconds", total_duration)
        self.span.set_attribute("react.status", status)
        
        if self.success:
            self.span.set_status(Status(StatusCode.OK))
        else:
            self.span.set_status(Status(StatusCode.ERROR, "ReAct loop failed"))
        
        self.span.end()


# ============================================================================
# METRICS ENDPOINT HELPER
# ============================================================================

def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(REGISTRY)


def create_metrics_endpoint(app):
    """Add /metrics endpoint to FastAPI app"""
    from fastapi import Response
    
    @app.get("/metrics")
    async def metrics():
        return Response(content=get_metrics(), media_type="text/plain")

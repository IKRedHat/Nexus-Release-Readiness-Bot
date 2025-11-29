import functools
import time
import logging
from typing import Any, Callable
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Histogram, REGISTRY

logger = logging.getLogger("nexus.instrumentation")

# --- Prometheus Metrics ---

# GenAI Metrics
LLM_TOKENS_TOTAL = Counter(
    'nexus_llm_tokens_total', 
    'Total tokens used by LLM', 
    ['model', 'type'] # type = input or output
)
LLM_LATENCY = Histogram(
    'nexus_llm_latency_seconds', 
    'Time taken for LLM generation',
    ['model']
)

# Agent Metrics
TOOL_USAGE_TOTAL = Counter(
    'nexus_tool_usage_total', 
    'Count of tool executions', 
    ['tool_name', 'status']
)

REACT_ITERATIONS = Histogram(
    'nexus_react_iterations_count',
    'Number of iterations in ReAct loop',
    ['task_type']
)

# --- Tracing Setup ---

def setup_tracing(service_name: str):
    """Configures OpenTelemetry to export traces via OTLP"""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    # In production, endpoint should come from env var
    # otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
    # processor = BatchSpanProcessor(otlp_exporter)
    # provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    logger.info(f"Tracing setup complete for {service_name}")

# --- Decorators ---

def track_llm_usage(model_name: str = "gemini-2.5-flash"):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                LLM_LATENCY.labels(model=model_name).observe(duration)
                
                # Mock token counting for MVP demo
                LLM_TOKENS_TOTAL.labels(model=model_name, type="input").inc(100)
                LLM_TOKENS_TOTAL.labels(model=model_name, type="output").inc(50)
                
                return result
            except Exception as e:
                raise e
        return wrapper
    return decorator

def track_tool_usage(tool_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            status = "success"
            try:
                return await func(*args, **kwargs)
            except Exception:
                status = "error"
                raise
            finally:
                TOOL_USAGE_TOTAL.labels(tool_name=tool_name, status=status).inc()
        return wrapper
    return decorator

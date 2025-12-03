"""
Unit Tests for Instrumentation & Metrics
=========================================

Tests for Prometheus metrics, OpenTelemetry tracing,
and LLM usage tracking decorators.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""  # Disable actual tracing


class TestPrometheusMetrics:
    """Tests for Prometheus metrics."""
    
    def test_llm_token_counter_exists(self):
        """Test LLM token counter metric exists."""
        from nexus_lib.instrumentation import LLM_TOKENS_TOTAL
        
        assert LLM_TOKENS_TOTAL is not None
        assert hasattr(LLM_TOKENS_TOTAL, 'labels')
    
    def test_llm_latency_histogram_exists(self):
        """Test LLM latency histogram metric exists."""
        from nexus_lib.instrumentation import LLM_LATENCY
        
        assert LLM_LATENCY is not None
        assert hasattr(LLM_LATENCY, 'labels')
    
    def test_tool_usage_counter_exists(self):
        """Test tool usage counter metric exists."""
        from nexus_lib.instrumentation import TOOL_USAGE_TOTAL
        
        assert TOOL_USAGE_TOTAL is not None
        assert hasattr(TOOL_USAGE_TOTAL, 'labels')
    
    def test_react_iterations_histogram_exists(self):
        """Test ReAct iterations histogram exists."""
        from nexus_lib.instrumentation import REACT_ITERATIONS
        
        assert REACT_ITERATIONS is not None
        assert hasattr(REACT_ITERATIONS, 'labels')
    
    def test_llm_requests_counter_exists(self):
        """Test LLM requests counter exists."""
        from nexus_lib.instrumentation import LLM_REQUESTS_TOTAL
        
        assert LLM_REQUESTS_TOTAL is not None
        assert hasattr(LLM_REQUESTS_TOTAL, 'labels')
    
    def test_llm_cost_counter_exists(self):
        """Test LLM cost counter exists."""
        from nexus_lib.instrumentation import LLM_COST_TOTAL
        
        assert LLM_COST_TOTAL is not None
        assert hasattr(LLM_COST_TOTAL, 'labels')


class TestLLMPricing:
    """Tests for LLM pricing estimation."""
    
    def test_estimate_llm_cost_gemini(self):
        """Test cost estimation for Gemini models."""
        from nexus_lib.instrumentation import estimate_llm_cost
        
        cost = estimate_llm_cost("gemini-1.5-pro", 1000, 500)
        
        # Input: 1000 tokens * $0.00125/1K = $0.00125
        # Output: 500 tokens * $0.005/1K = $0.0025
        # Total: $0.00375
        assert cost > 0
        assert cost == pytest.approx(0.00375, rel=0.01)
    
    def test_estimate_llm_cost_openai(self):
        """Test cost estimation for OpenAI models."""
        from nexus_lib.instrumentation import estimate_llm_cost
        
        cost = estimate_llm_cost("gpt-4o", 1000, 500)
        
        # Input: 1000 tokens * $0.005/1K = $0.005
        # Output: 500 tokens * $0.015/1K = $0.0075
        # Total: $0.0125
        assert cost > 0
        assert cost == pytest.approx(0.0125, rel=0.01)
    
    def test_estimate_llm_cost_unknown_model(self):
        """Test cost estimation falls back for unknown models."""
        from nexus_lib.instrumentation import estimate_llm_cost
        
        cost = estimate_llm_cost("unknown-model", 1000, 500)
        
        # Uses default pricing
        assert cost > 0


class TestTrackLLMUsageDecorator:
    """Tests for @track_llm_usage decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_tokens(self):
        """Test decorator tracks input/output tokens."""
        from nexus_lib.instrumentation import track_llm_usage
        
        @track_llm_usage(model_name="test-model")
        async def mock_llm_call():
            return {
                "content": "Test response",
                "input_tokens": 100,
                "output_tokens": 50
            }
        
        result = await mock_llm_call()
        
        assert result["content"] == "Test response"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_latency(self):
        """Test decorator tracks execution latency."""
        from nexus_lib.instrumentation import track_llm_usage
        
        @track_llm_usage(model_name="test-model")
        async def slow_llm_call():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"content": "Done", "input_tokens": 10, "output_tokens": 5}
        
        start = time.time()
        result = await slow_llm_call()
        duration = time.time() - start
        
        assert duration >= 0.1
        assert result["content"] == "Done"
    
    @pytest.mark.asyncio
    async def test_decorator_handles_errors(self):
        """Test decorator handles exceptions gracefully."""
        from nexus_lib.instrumentation import track_llm_usage
        
        @track_llm_usage(model_name="test-model")
        async def failing_llm_call():
            raise ValueError("LLM Error")
        
        with pytest.raises(ValueError):
            await failing_llm_call()
    
    @pytest.mark.asyncio
    async def test_decorator_adds_usage_info(self):
        """Test decorator adds _llm_usage to result."""
        from nexus_lib.instrumentation import track_llm_usage, LLMUsage
        
        @track_llm_usage(model_name="gemini-1.5-pro")
        async def tracked_call():
            return {"content": "response", "input_tokens": 50, "output_tokens": 25}
        
        result = await tracked_call()
        
        assert "_llm_usage" in result
        usage = result["_llm_usage"]
        assert isinstance(usage, LLMUsage)
        assert usage.input_tokens == 50
        assert usage.output_tokens == 25
        assert usage.total_tokens == 75


class TestTrackToolUsageDecorator:
    """Tests for @track_tool_usage decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_tool_calls(self):
        """Test decorator tracks tool invocations."""
        from nexus_lib.instrumentation import track_tool_usage
        
        @track_tool_usage(tool_name="get_jira_ticket")
        async def mock_tool_call(ticket_key: str):
            return {"key": ticket_key, "status": "In Progress"}
        
        result = await mock_tool_call("PROJ-123")
        
        assert result["key"] == "PROJ-123"
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_success_status(self):
        """Test decorator tracks successful tool calls."""
        from nexus_lib.instrumentation import track_tool_usage
        
        @track_tool_usage(tool_name="test_tool")
        async def successful_tool():
            return {"status": "success"}
        
        result = await successful_tool()
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_failure_status(self):
        """Test decorator tracks failed tool calls."""
        from nexus_lib.instrumentation import track_tool_usage
        
        @track_tool_usage(tool_name="failing_tool")
        async def failing_tool():
            raise Exception("Tool failed")
        
        with pytest.raises(Exception):
            await failing_tool()
    
    @pytest.mark.asyncio
    async def test_decorator_with_agent_type(self):
        """Test decorator with custom agent type."""
        from nexus_lib.instrumentation import track_tool_usage
        
        @track_tool_usage(tool_name="jira_search", agent_type="jira_agent")
        async def jira_tool():
            return {"results": []}
        
        result = await jira_tool()
        assert "results" in result


class TestOpenTelemetrySetup:
    """Tests for OpenTelemetry tracing setup."""
    
    def test_setup_tracing_returns_provider(self):
        """Test setup_tracing returns a tracer provider."""
        from nexus_lib.instrumentation import setup_tracing
        
        provider = setup_tracing("test-service")
        
        assert provider is not None
    
    def test_setup_tracing_with_version(self):
        """Test setup_tracing with version parameter."""
        from nexus_lib.instrumentation import setup_tracing
        
        provider = setup_tracing("test-service", service_version="2.0.0")
        
        assert provider is not None
    
    def test_get_tracer_returns_tracer(self):
        """Test get_tracer returns a tracer instance."""
        from nexus_lib.instrumentation import setup_tracing, get_tracer
        
        setup_tracing("test-service")
        tracer = get_tracer("test")
        
        assert tracer is not None
        assert hasattr(tracer, 'start_span')


class TestReActTracker:
    """Tests for ReAct loop tracking."""
    
    def test_react_tracker_context_manager(self):
        """Test ReAct tracker as context manager."""
        from nexus_lib.instrumentation import track_react_loop
        
        with track_react_loop("test_task") as tracker:
            tracker.record_step("think")
            tracker.record_step("act")
            tracker.complete(success=True)
        
        # Should complete without error
    
    def test_react_tracker_counts_steps(self):
        """Test ReAct tracker counts steps."""
        from nexus_lib.instrumentation import track_react_loop
        
        with track_react_loop("test_task") as tracker:
            tracker.record_step("think")
            tracker.record_step("act")
            tracker.record_step("observe")
            
            assert tracker.step_count == 3
    
    def test_react_tracker_failure(self):
        """Test ReAct tracker handles failures."""
        from nexus_lib.instrumentation import track_react_loop
        
        with track_react_loop("failing_task") as tracker:
            tracker.record_step("think")
            tracker.complete(success=False)
            
            assert not tracker.success


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware."""
    
    def test_middleware_tracks_requests(self):
        """Test middleware tracks HTTP requests."""
        from nexus_lib.middleware import MetricsMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
    
    def test_middleware_tracks_latency(self):
        """Test middleware tracks request latency."""
        from nexus_lib.middleware import MetricsMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
        
        @app.get("/slow")
        def slow_endpoint():
            time.sleep(0.1)
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/slow")
        
        assert response.status_code == 200
    
    def test_middleware_tracks_errors(self):
        """Test middleware tracks error responses."""
        from nexus_lib.middleware import MetricsMiddleware
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
        
        @app.get("/error")
        def error_endpoint():
            raise HTTPException(status_code=500, detail="Internal error")
        
        client = TestClient(app)
        response = client.get("/error")
        
        assert response.status_code == 500


class TestMetricsGeneration:
    """Tests for generating Prometheus metrics."""
    
    def test_generate_metrics_format(self):
        """Test metrics are in Prometheus format."""
        from prometheus_client import generate_latest, REGISTRY
        
        metrics = generate_latest(REGISTRY).decode('utf-8')
        
        # Should contain TYPE and HELP comments
        assert "# HELP" in metrics or "# TYPE" in metrics
    
    def test_metrics_contain_nexus_prefix(self):
        """Test custom metrics have nexus_ prefix."""
        from nexus_lib.instrumentation import get_metrics
        
        metrics = get_metrics().decode('utf-8')
        
        # Should contain nexus_ prefixed metrics
        assert "nexus_" in metrics or len(metrics) > 100
    
    def test_get_metrics_returns_bytes(self):
        """Test get_metrics returns bytes."""
        from nexus_lib.instrumentation import get_metrics
        
        metrics = get_metrics()
        
        assert isinstance(metrics, bytes)


class TestMetricLabels:
    """Tests for metric labels."""
    
    def test_llm_metrics_have_model_label(self):
        """Test LLM metrics include model label."""
        from nexus_lib.instrumentation import LLM_TOKENS_TOTAL
        
        # Access the metric with labels
        metric = LLM_TOKENS_TOTAL.labels(
            model_name="gemini-1.5-pro",
            type="input"
        )
        
        assert metric is not None
    
    def test_tool_metrics_have_status_label(self):
        """Test tool metrics include status label."""
        from nexus_lib.instrumentation import TOOL_USAGE_TOTAL
        
        metric = TOOL_USAGE_TOTAL.labels(
            tool_name="get_jira_ticket",
            status="success",
            agent_type="orchestrator"
        )
        
        assert metric is not None
    
    def test_react_metrics_have_task_label(self):
        """Test ReAct metrics include task_type label."""
        from nexus_lib.instrumentation import REACT_ITERATIONS
        
        metric = REACT_ITERATIONS.labels(
            task_type="release_check",
            status="success"
        )
        
        assert metric is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

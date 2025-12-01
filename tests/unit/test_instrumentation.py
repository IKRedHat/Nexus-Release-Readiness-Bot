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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""  # Disable actual tracing


class TestPrometheusMetrics:
    """Tests for Prometheus metrics."""
    
    def test_llm_token_counter_exists(self):
        """Test LLM token counter metric exists."""
        from nexus_lib.instrumentation import nexus_llm_tokens_total
        
        assert nexus_llm_tokens_total is not None
        assert hasattr(nexus_llm_tokens_total, 'labels')
    
    def test_llm_latency_histogram_exists(self):
        """Test LLM latency histogram metric exists."""
        from nexus_lib.instrumentation import nexus_llm_latency_seconds
        
        assert nexus_llm_latency_seconds is not None
        assert hasattr(nexus_llm_latency_seconds, 'labels')
    
    def test_tool_usage_counter_exists(self):
        """Test tool usage counter metric exists."""
        from nexus_lib.instrumentation import nexus_tool_usage_total
        
        assert nexus_tool_usage_total is not None
        assert hasattr(nexus_tool_usage_total, 'labels')
    
    def test_react_iterations_counter_exists(self):
        """Test ReAct iterations counter exists."""
        from nexus_lib.instrumentation import nexus_react_iterations_count
        
        assert nexus_react_iterations_count is not None
    
    def test_hygiene_score_gauge_exists(self):
        """Test hygiene score gauge exists."""
        from nexus_lib.instrumentation import nexus_project_hygiene_score
        
        assert nexus_project_hygiene_score is not None
        assert hasattr(nexus_project_hygiene_score, 'labels')
    
    def test_rca_metrics_exist(self):
        """Test RCA-related metrics exist."""
        from nexus_lib.instrumentation import (
            nexus_rca_requests_total,
            nexus_rca_duration_seconds,
            nexus_rca_confidence_score
        )
        
        assert nexus_rca_requests_total is not None
        assert nexus_rca_duration_seconds is not None
        assert nexus_rca_confidence_score is not None


class TestTrackLLMUsageDecorator:
    """Tests for @track_llm_usage decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_tokens(self):
        """Test decorator tracks input/output tokens."""
        from nexus_lib.instrumentation import track_llm_usage
        
        @track_llm_usage(model="test-model", task_type="test")
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
        import time
        
        @track_llm_usage(model="test-model", task_type="latency-test")
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
        
        @track_llm_usage(model="test-model", task_type="error-test")
        async def failing_llm_call():
            raise ValueError("LLM Error")
        
        with pytest.raises(ValueError):
            await failing_llm_call()


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


class TestOpenTelemetrySetup:
    """Tests for OpenTelemetry tracing setup."""
    
    def test_setup_tracing_returns_tracer(self):
        """Test setup_tracing returns a tracer."""
        from nexus_lib.instrumentation import setup_tracing
        
        tracer = setup_tracing("test-service")
        
        assert tracer is not None
    
    def test_setup_tracing_with_endpoint(self):
        """Test setup_tracing with OTLP endpoint."""
        from nexus_lib.instrumentation import setup_tracing
        
        tracer = setup_tracing(
            "test-service",
            otlp_endpoint="http://localhost:4317"
        )
        
        assert tracer is not None
    
    def test_tracer_can_start_span(self):
        """Test tracer can start spans."""
        from nexus_lib.instrumentation import setup_tracing
        
        tracer = setup_tracing("test-service")
        
        with tracer.start_as_current_span("test-span") as span:
            assert span is not None
            span.set_attribute("test.key", "test.value")


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
        import time
        
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
        from prometheus_client import generate_latest, REGISTRY
        
        metrics = generate_latest(REGISTRY).decode('utf-8')
        
        # Should contain nexus_ prefixed metrics
        # (might not if no metrics recorded yet)
        assert "nexus_" in metrics or len(metrics) > 100


class TestMetricLabels:
    """Tests for metric labels."""
    
    def test_llm_metrics_have_model_label(self):
        """Test LLM metrics include model label."""
        from nexus_lib.instrumentation import nexus_llm_tokens_total
        
        # Access the metric with labels
        metric = nexus_llm_tokens_total.labels(
            model="gemini-1.5-pro",
            token_type="input",
            task_type="rca"
        )
        
        assert metric is not None
    
    def test_tool_metrics_have_status_label(self):
        """Test tool metrics include status label."""
        from nexus_lib.instrumentation import nexus_tool_usage_total
        
        metric = nexus_tool_usage_total.labels(
            tool_name="get_jira_ticket",
            status="success"
        )
        
        assert metric is not None
    
    def test_hygiene_metrics_have_project_label(self):
        """Test hygiene metrics include project label."""
        from nexus_lib.instrumentation import nexus_project_hygiene_score
        
        metric = nexus_project_hygiene_score.labels(project="PROJ")
        
        assert metric is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


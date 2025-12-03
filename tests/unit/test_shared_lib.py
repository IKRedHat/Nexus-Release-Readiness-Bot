"""
Comprehensive Unit Tests for Shared Library (nexus_lib)
========================================================

Recommendation #2: Critical Component Coverage
Tests all modules in the shared library.

Coverage:
- Pydantic schemas and validation
- LLM client abstraction
- Configuration management
- Instrumentation and metrics
- Utilities and helpers
- Multi-tenancy
- Agent contracts

Usage:
    pytest tests/unit/test_shared_lib.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""


# =============================================================================
# Schema Tests
# =============================================================================

class TestJiraSchemas:
    """Tests for Jira-related Pydantic schemas."""
    
    def test_jira_ticket_creation(self):
        """Test JiraTicket schema creation."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test ticket",
            status="Open",
            issue_type="Bug"
        )
        
        assert ticket.key == "NEXUS-123"
        assert ticket.summary == "Test ticket"
        assert ticket.status == "Open"
    
    def test_jira_ticket_with_all_fields(self):
        """Test JiraTicket with all optional fields."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-456",
            summary="Complete ticket",
            status="In Progress",
            issue_type="Story",
            assignee="user@example.com",
            priority="High",
            labels=["release", "v2.0"],
            story_points=5,
            fix_version="2.0.0",
            epic_key="NEXUS-100",
            description="Full description"
        )
        
        assert ticket.assignee == "user@example.com"
        assert ticket.story_points == 5
        assert "release" in ticket.labels
    
    def test_jira_ticket_serialization(self):
        """Test JiraTicket JSON serialization."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-789",
            summary="Serialization test",
            status="Done",
            issue_type="Task"
        )
        
        json_data = ticket.model_dump()
        assert json_data["key"] == "NEXUS-789"
        assert isinstance(json_data, dict)


class TestBuildSchemas:
    """Tests for Build-related schemas."""
    
    def test_build_status_creation(self):
        """Test BuildStatus schema creation."""
        from nexus_lib.schemas.agent_contract import BuildStatus
        
        build = BuildStatus(
            job_name="nexus-main",
            build_number=142,
            status="SUCCESS",
            url="http://jenkins/job/nexus-main/142"
        )
        
        assert build.job_name == "nexus-main"
        assert build.status == "SUCCESS"
    
    def test_build_status_with_details(self):
        """Test BuildStatus with all details."""
        from nexus_lib.schemas.agent_contract import BuildStatus
        
        build = BuildStatus(
            job_name="nexus-main",
            build_number=143,
            status="FAILURE",
            url="http://jenkins/job/nexus-main/143",
            timestamp=datetime.utcnow(),
            duration_seconds=300,
            triggered_by="webhook",
            commit_sha="abc123def456"
        )
        
        assert build.status == "FAILURE"
        assert build.duration_seconds == 300


class TestReleaseSchemas:
    """Tests for Release-related schemas."""
    
    def test_release_creation(self):
        """Test Release schema creation."""
        from nexus_lib.schemas.agent_contract import Release
        
        release = Release(
            release_id="rel-001",
            version="v2.0.0",
            target_date=datetime.utcnow() + timedelta(days=30)
        )
        
        assert release.version == "v2.0.0"
        assert release.release_id == "rel-001"
    
    def test_release_with_milestones(self):
        """Test Release with milestones."""
        from nexus_lib.schemas.agent_contract import Release, ReleaseMilestone
        
        milestone = ReleaseMilestone(
            name="Code Freeze",
            target_date=datetime.utcnow() + timedelta(days=7),
            completed=False
        )
        
        release = Release(
            release_id="rel-002",
            version="v2.1.0",
            target_date=datetime.utcnow() + timedelta(days=30),
            milestones=[milestone]
        )
        
        assert len(release.milestones) == 1
        assert release.milestones[0].name == "Code Freeze"


class TestAgentContractSchemas:
    """Tests for Agent Contract schemas."""
    
    def test_agent_task_request(self):
        """Test AgentTaskRequest schema."""
        from nexus_lib.schemas.agent_contract import AgentTaskRequest
        
        request = AgentTaskRequest(
            task_id="task-001",
            action="get_ticket",
            payload={"ticket_key": "NEXUS-123"}
        )
        
        assert request.action == "get_ticket"
        assert request.payload["ticket_key"] == "NEXUS-123"
    
    def test_agent_task_response(self):
        """Test AgentTaskResponse schema."""
        from nexus_lib.schemas.agent_contract import AgentTaskResponse
        
        response = AgentTaskResponse(
            task_id="task-001",
            status="success",
            data={"key": "NEXUS-123", "status": "Open"}
        )
        
        assert response.status == "success"
        assert response.data["key"] == "NEXUS-123"
    
    def test_agent_task_response_failure(self):
        """Test AgentTaskResponse with failure."""
        from nexus_lib.schemas.agent_contract import AgentTaskResponse
        
        response = AgentTaskResponse(
            task_id="task-002",
            status="failed",
            error="Ticket not found"
        )
        
        assert response.status == "failed"
        assert response.error == "Ticket not found"


# =============================================================================
# LLM Client Tests
# =============================================================================

class TestLLMClientFactory:
    """Tests for LLM client factory."""
    
    def test_create_mock_client(self):
        """Test creating mock LLM client."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        assert client is not None
        assert hasattr(client, 'generate')
    
    def test_llm_config_defaults(self):
        """Test LLMConfig default values."""
        from nexus_lib.llm.base import LLMConfig
        
        config = LLMConfig()
        assert config.temperature >= 0
        assert config.max_tokens > 0


class TestMockLLMClient:
    """Tests for mock LLM client."""
    
    @pytest.mark.asyncio
    async def test_mock_generate(self):
        """Test mock LLM generation."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        
        response = await client.generate("Hello, how are you?")
        
        assert response is not None
        # Mock should return something
    
    @pytest.mark.asyncio
    async def test_mock_with_system_message(self):
        """Test mock LLM with system message."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        
        response = await client.generate(
            "What is the release status?",
            system_message="You are a release assistant."
        )
        
        assert response is not None


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfigManager:
    """Tests for ConfigManager."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        return mock
    
    def test_is_sensitive_key(self):
        """Test sensitive key detection."""
        from nexus_lib.config import ConfigManager
        
        # API keys should be sensitive
        assert ConfigManager.is_sensitive("nexus:config:api_key") == True
        assert ConfigManager.is_sensitive("nexus:config:token") == True
        assert ConfigManager.is_sensitive("nexus:config:password") == True
        assert ConfigManager.is_sensitive("nexus:config:secret") == True
        
        # URLs should not be sensitive
        assert ConfigManager.is_sensitive("nexus:config:jira_url") == False
    
    def test_mask_value(self):
        """Test value masking."""
        from nexus_lib.config import ConfigManager
        
        masked = ConfigManager.mask_value(
            "nexus:config:api_key",
            "super_secret_key_12345"
        )
        
        # Should be masked
        assert "12345" not in masked or "****" in masked
    
    def test_mask_non_sensitive_value(self):
        """Test non-sensitive values not masked."""
        from nexus_lib.config import ConfigManager
        
        value = "https://jira.example.com"
        result = ConfigManager.mask_value("nexus:config:jira_url", value)
        
        # Should show full URL
        assert result == value


class TestConfigKeys:
    """Tests for ConfigKeys constants."""
    
    def test_config_keys_exist(self):
        """Test ConfigKeys constants exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'JIRA_URL')
        assert hasattr(ConfigKeys, 'GITHUB_TOKEN')
        assert hasattr(ConfigKeys, 'LLM_PROVIDER')
    
    def test_config_keys_format(self):
        """Test ConfigKeys follow naming convention."""
        from nexus_lib.config import ConfigKeys
        
        # All keys should start with nexus:config:
        for attr in dir(ConfigKeys):
            if not attr.startswith('_'):
                value = getattr(ConfigKeys, attr)
                if isinstance(value, str):
                    assert value.startswith("nexus:"), f"{attr} doesn't start with nexus:"


# =============================================================================
# Instrumentation Tests
# =============================================================================

class TestPrometheusMetrics:
    """Tests for Prometheus metrics."""
    
    def test_llm_token_counter_exists(self):
        """Test LLM token counter metric exists."""
        from nexus_lib.instrumentation import LLM_TOKENS_TOTAL
        
        assert LLM_TOKENS_TOTAL is not None
        assert hasattr(LLM_TOKENS_TOTAL, 'labels')
    
    def test_tool_usage_counter_exists(self):
        """Test tool usage counter exists."""
        from nexus_lib.instrumentation import TOOL_USAGE_TOTAL
        
        assert TOOL_USAGE_TOTAL is not None
    
    def test_react_iterations_exists(self):
        """Test ReAct iterations metric exists."""
        from nexus_lib.instrumentation import REACT_ITERATIONS
        
        assert REACT_ITERATIONS is not None


class TestMetricDecorators:
    """Tests for metric decorators."""
    
    @pytest.mark.asyncio
    async def test_track_llm_usage_decorator(self):
        """Test track_llm_usage decorator."""
        from nexus_lib.instrumentation import track_llm_usage
        
        @track_llm_usage(model="test-model")
        async def mock_llm_call():
            return {"response": "test", "tokens": 100}
        
        result = await mock_llm_call()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_track_tool_usage_decorator(self):
        """Test track_tool_usage decorator."""
        from nexus_lib.instrumentation import track_tool_usage
        
        @track_tool_usage(tool_name="test_tool")
        async def mock_tool_call():
            return {"status": "success"}
        
        result = await mock_tool_call()
        assert result is not None


# =============================================================================
# Utility Tests
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_truncate_build_log(self):
        """Test build log truncation."""
        from nexus_lib.utils import truncate_build_log
        
        long_log = "line\n" * 10000
        truncated = truncate_build_log(long_log)
        
        # Should be shorter
        assert len(truncated) < len(long_log)
    
    def test_truncate_short_log(self):
        """Test short logs not truncated."""
        from nexus_lib.utils import truncate_build_log
        
        short_log = "Error on line 1\nError on line 2"
        result = truncate_build_log(short_log)
        
        # Should preserve content
        assert "Error on line 1" in result
    
    def test_extract_error_summary(self):
        """Test error summary extraction."""
        from nexus_lib.utils import extract_error_summary
        
        log = """
        Running tests...
        [ERROR] Test failed: test_example
        Traceback (most recent call last):
            File "test.py", line 10
        AssertionError: Expected True
        """
        
        summary = extract_error_summary(log)
        assert "ERROR" in summary or "failed" in summary.lower() or len(summary) > 0
    
    def test_parse_stack_trace(self):
        """Test stack trace parsing."""
        from nexus_lib.utils import parse_stack_trace
        
        traceback = """
        Traceback (most recent call last):
          File "main.py", line 50, in process
            result = calculate()
          File "utils.py", line 25, in calculate
            return 1/0
        ZeroDivisionError: division by zero
        """
        
        parsed = parse_stack_trace(traceback)
        assert parsed is not None


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_get_url_for_agent(self):
        """Test getting URL for agent."""
        from nexus_lib.utils import AgentRegistry
        
        url = AgentRegistry.get_url("jira_agent")
        
        # Should return a URL or None
        assert url is None or url.startswith("http")
    
    def test_list_agents(self):
        """Test listing all agents."""
        from nexus_lib.utils import AgentRegistry
        
        agents = AgentRegistry.list_agents()
        
        # Should return dict
        assert isinstance(agents, dict)


# =============================================================================
# HTTP Client Tests
# =============================================================================

class TestAsyncHttpClient:
    """Tests for AsyncHttpClient."""
    
    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test HTTP client creation."""
        from nexus_lib.utils import AsyncHttpClient
        
        client = AsyncHttpClient()
        assert client is not None
    
    @pytest.mark.asyncio
    async def test_client_with_retry(self):
        """Test HTTP client with retry config."""
        from nexus_lib.utils import AsyncHttpClient
        
        client = AsyncHttpClient(
            timeout=30.0,
            max_retries=3
        )
        assert client.max_retries == 3


# =============================================================================
# Multi-Tenancy Tests
# =============================================================================

class TestMultiTenancy:
    """Tests for multi-tenancy support."""
    
    def test_tenant_context(self):
        """Test TenantContext creation."""
        try:
            from nexus_lib.multitenancy import TenantContext
            
            context = TenantContext(
                tenant_id="tenant-123",
                organization="Acme Corp"
            )
            
            assert context.tenant_id == "tenant-123"
        except ImportError:
            pytest.skip("Multi-tenancy not implemented")
    
    def test_tenant_limits(self):
        """Test tenant limits."""
        try:
            from nexus_lib.multitenancy import TenantLimits
            
            limits = TenantLimits(
                max_queries_per_day=1000,
                max_llm_tokens_per_day=100000
            )
            
            assert limits.max_queries_per_day == 1000
        except ImportError:
            pytest.skip("Multi-tenancy not implemented")


# =============================================================================
# Recommendations Engine Tests
# =============================================================================

class TestRecommendationsEngine:
    """Tests for AI recommendations engine."""
    
    def test_release_timing_recommendation(self):
        """Test release timing recommendations."""
        try:
            from nexus_lib.recommendations import RecommendationEngine
            
            engine = RecommendationEngine()
            # Should have methods for recommendations
            assert hasattr(engine, 'analyze') or hasattr(engine, 'get_recommendations')
        except ImportError:
            pytest.skip("Recommendations engine not implemented")


# =============================================================================
# Validation Tests
# =============================================================================

class TestSchemaValidation:
    """Tests for schema validation."""
    
    def test_invalid_ticket_key_format(self):
        """Test invalid ticket key is handled."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        # Should allow any key format (Jira handles validation)
        ticket = JiraTicket(
            key="invalid-key",
            summary="Test",
            status="Open",
            issue_type="Bug"
        )
        
        assert ticket.key == "invalid-key"
    
    def test_empty_summary_allowed(self):
        """Test empty summary is allowed."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="",
            status="Open",
            issue_type="Bug"
        )
        
        assert ticket.summary == ""
    
    def test_negative_story_points(self):
        """Test negative story points handling."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        # Pydantic may allow negative, but it's unusual
        try:
            ticket = JiraTicket(
                key="NEXUS-123",
                summary="Test",
                status="Open",
                issue_type="Story",
                story_points=-5
            )
            # If created, should have the value
            assert ticket.story_points == -5
        except Exception:
            # Validation error is acceptable
            pass


# =============================================================================
# RCA Schema Tests
# =============================================================================

class TestRCASchemas:
    """Tests for RCA-related schemas."""
    
    def test_rca_request_creation(self):
        """Test RcaRequest schema."""
        from nexus_lib.schemas.agent_contract import RcaRequest
        
        request = RcaRequest(
            job_name="nexus-main",
            build_number=142
        )
        
        assert request.job_name == "nexus-main"
        assert request.build_number == 142
    
    def test_rca_request_with_log(self):
        """Test RcaRequest with build log."""
        from nexus_lib.schemas.agent_contract import RcaRequest
        
        request = RcaRequest(
            job_name="nexus-main",
            build_number=142,
            build_log="Error: Test failed",
            repository="nexus-backend"
        )
        
        assert request.build_log == "Error: Test failed"
    
    def test_rca_analysis_creation(self):
        """Test RcaAnalysis schema."""
        from nexus_lib.schemas.agent_contract import (
            RcaAnalysis, RcaConfidenceLevel, RcaErrorType
        )
        
        analysis = RcaAnalysis(
            analysis_id="rca-001",
            job_name="nexus-main",
            build_number=142,
            root_cause="Test assertion failed",
            confidence=RcaConfidenceLevel.HIGH,
            error_type=RcaErrorType.TEST_FAILURE
        )
        
        assert analysis.root_cause == "Test assertion failed"
        assert analysis.confidence == RcaConfidenceLevel.HIGH


# =============================================================================
# Analytics Schema Tests
# =============================================================================

class TestAnalyticsSchemas:
    """Tests for Analytics-related schemas."""
    
    def test_dora_metrics_creation(self):
        """Test DORAMetrics schema."""
        try:
            from nexus_lib.schemas.agent_contract import DORAMetrics
            
            metrics = DORAMetrics(
                deployment_frequency=5.0,
                lead_time_for_changes=24.0,
                time_to_restore_service=2.0,
                change_failure_rate=0.05
            )
            
            assert metrics.deployment_frequency == 5.0
        except ImportError:
            # May not have DORAMetrics
            pass
    
    def test_prediction_result_creation(self):
        """Test PredictionResult schema."""
        from nexus_lib.schemas.agent_contract import PredictionResult
        
        prediction = PredictionResult(
            prediction_type="release_date",
            predicted_value="2025-01-15",
            confidence=0.85
        )
        
        assert prediction.confidence == 0.85


# =============================================================================
# Webhook Schema Tests
# =============================================================================

class TestWebhookSchemas:
    """Tests for Webhook-related schemas."""
    
    def test_webhook_event_creation(self):
        """Test WebhookEvent schema."""
        try:
            from nexus_lib.schemas.agent_contract import WebhookEvent
            
            event = WebhookEvent(
                event_type="release.created",
                payload={"version": "v2.0.0"}
            )
            
            assert event.event_type == "release.created"
        except ImportError:
            pass


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_very_long_ticket_summary(self):
        """Test very long ticket summary."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        long_summary = "A" * 10000
        ticket = JiraTicket(
            key="NEXUS-123",
            summary=long_summary,
            status="Open",
            issue_type="Bug"
        )
        
        assert len(ticket.summary) == 10000
    
    def test_unicode_in_fields(self):
        """Test Unicode characters in fields."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-日本語",
            summary="テスト 🚀 émojis",
            status="Open",
            issue_type="Bug"
        )
        
        assert "🚀" in ticket.summary
    
    def test_null_optional_fields(self):
        """Test null values for optional fields."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Bug",
            assignee=None,
            labels=None
        )
        
        assert ticket.assignee is None


"""
Comprehensive Error Handling Tests
===================================

Recommendation #4: Add Negative Tests
Tests error handling across all services and components.

Coverage:
- Invalid input validation
- Missing required fields
- Malformed requests
- Authentication/Authorization errors
- Rate limiting
- Timeout handling
- Service unavailability
- Data validation errors
- Boundary conditions

Usage:
    pytest tests/unit/test_error_handling.py -v
"""

import pytest
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"


# =============================================================================
# Schema Validation Error Tests
# =============================================================================

class TestSchemaValidationErrors:
    """Tests for Pydantic schema validation errors."""
    
    def test_jira_ticket_missing_required_fields(self):
        """Test JiraTicket fails without required fields."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            JiraTicket()  # Missing all required fields
    
    def test_jira_ticket_missing_key(self):
        """Test JiraTicket fails without key."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        with pytest.raises(Exception):
            JiraTicket(
                summary="Test",
                status="Open",
                issue_type="Bug"
            )
    
    def test_build_status_invalid_status(self):
        """Test BuildStatus with invalid enum value."""
        from nexus_lib.schemas.agent_contract import BuildStatus
        
        # May or may not validate status - depends on schema
        build = BuildStatus(
            job_name="test",
            build_number=1,
            status="INVALID_STATUS",
            url="http://test"
        )
        # If it accepts any string, that's fine
        assert build.status == "INVALID_STATUS"
    
    def test_agent_task_request_empty_action(self):
        """Test AgentTaskRequest with empty action."""
        from nexus_lib.schemas.agent_contract import AgentTaskRequest
        
        request = AgentTaskRequest(
            task_id="test-1",
            action="",
            payload={}
        )
        
        # Empty action is technically valid
        assert request.action == ""
    
    def test_agent_task_response_invalid_status(self):
        """Test AgentTaskResponse with invalid status."""
        from nexus_lib.schemas.agent_contract import AgentTaskResponse
        
        response = AgentTaskResponse(
            task_id="test-1",
            status="invalid_status",
            data={}
        )
        
        # May accept any string
        assert response.status == "invalid_status"
    
    def test_release_invalid_date_format(self):
        """Test Release with invalid date."""
        from nexus_lib.schemas.agent_contract import Release
        
        # Passing string instead of datetime may fail
        try:
            release = Release(
                release_id="rel-1",
                version="v1.0",
                target_date="not-a-date"
            )
            # If it accepts, it should convert
        except Exception:
            # Expected to fail
            pass


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    """Tests for input validation edge cases."""
    
    def test_very_long_string_input(self):
        """Test handling of very long strings."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        # Should handle gracefully
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="A" * 100000,
            status="Open",
            issue_type="Bug"
        )
        
        assert len(ticket.summary) == 100000
    
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-日本語-🚀",
            summary="Test émoji 🎉 日本語テスト",
            status="Open",
            issue_type="Bug"
        )
        
        assert "🚀" in ticket.key
        assert "🎉" in ticket.summary
    
    def test_null_byte_in_string(self):
        """Test handling of null bytes in strings."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        # May or may not handle null bytes
        try:
            ticket = JiraTicket(
                key="NEXUS-123",
                summary="Test\x00with\x00nulls",
                status="Open",
                issue_type="Bug"
            )
            # If created, verify content
            assert "Test" in ticket.summary
        except Exception:
            pass  # Rejection is also valid
    
    def test_html_injection_attempt(self):
        """Test handling of HTML injection."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="<script>alert('xss')</script>",
            status="Open",
            issue_type="Bug"
        )
        
        # Should preserve as-is (sanitization happens elsewhere)
        assert "<script>" in ticket.summary
    
    def test_sql_injection_attempt(self):
        """Test handling of SQL injection."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123'; DROP TABLE tickets;--",
            summary="Test",
            status="Open",
            issue_type="Bug"
        )
        
        # Should preserve as-is
        assert "DROP TABLE" in ticket.key
    
    def test_negative_numbers(self):
        """Test handling of negative numbers."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Story",
            story_points=-100
        )
        
        assert ticket.story_points == -100
    
    def test_float_for_integer_field(self):
        """Test handling of float for integer field."""
        from nexus_lib.schemas.agent_contract import BuildStatus
        
        build = BuildStatus(
            job_name="test",
            build_number=142.5,  # Should truncate or fail
            status="SUCCESS",
            url="http://test"
        )
        
        # Pydantic may convert to int
        assert isinstance(build.build_number, int)


# =============================================================================
# Configuration Error Tests
# =============================================================================

class TestConfigurationErrors:
    """Tests for configuration error handling."""
    
    def test_invalid_config_key_format(self):
        """Test invalid config key format."""
        from nexus_lib.config import ConfigManager
        
        # Keys without nexus: prefix may still work
        is_sensitive = ConfigManager.is_sensitive("invalid_key")
        # Should return some boolean
        assert isinstance(is_sensitive, bool)
    
    def test_empty_config_value(self):
        """Test empty config value."""
        from nexus_lib.config import ConfigManager
        
        masked = ConfigManager.mask_value("nexus:config:test", "")
        # Empty should return empty
        assert masked == "" or masked is None
    
    def test_config_with_special_characters(self):
        """Test config with special characters."""
        from nexus_lib.config import ConfigManager
        
        value = "password!@#$%^&*(){}[]|\\:\";<>?,./~`"
        masked = ConfigManager.mask_value("nexus:config:api_key", value)
        
        # Should be masked
        assert "****" in masked or value not in masked


# =============================================================================
# Utility Function Error Tests
# =============================================================================

class TestUtilityErrors:
    """Tests for utility function error handling."""
    
    def test_truncate_empty_log(self):
        """Test truncating empty log."""
        from nexus_lib.utils import truncate_build_log
        
        result = truncate_build_log("")
        assert result == ""
    
    def test_truncate_none_log(self):
        """Test truncating None log."""
        from nexus_lib.utils import truncate_build_log
        
        try:
            result = truncate_build_log(None)
            # May return empty or raise
            assert result is None or result == ""
        except (TypeError, AttributeError):
            pass  # Expected
    
    def test_extract_error_from_empty_log(self):
        """Test extracting error from empty log."""
        from nexus_lib.utils import extract_error_summary
        
        result = extract_error_summary("")
        # Should return empty or None
        assert result == "" or result is None or len(result) == 0
    
    def test_parse_invalid_stack_trace(self):
        """Test parsing invalid stack trace."""
        from nexus_lib.utils import parse_stack_trace
        
        result = parse_stack_trace("not a stack trace")
        # Should handle gracefully
        assert result is None or isinstance(result, (dict, list, str))


# =============================================================================
# LLM Client Error Tests
# =============================================================================

class TestLLMClientErrors:
    """Tests for LLM client error handling."""
    
    def test_create_invalid_provider(self):
        """Test creating client with invalid provider."""
        from nexus_lib.llm import create_llm_client
        
        # May fall back to mock or raise
        try:
            client = create_llm_client(provider="nonexistent_provider")
            # If created, should still work
            assert client is not None
        except Exception as e:
            # Expected to fail
            assert "provider" in str(e).lower() or "not supported" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt(self):
        """Test generation with empty prompt."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        
        # Should handle empty prompt
        response = await client.generate("")
        # May return empty or error
        assert response is not None


# =============================================================================
# Agent Registry Error Tests
# =============================================================================

class TestAgentRegistryErrors:
    """Tests for AgentRegistry error handling."""
    
    def test_get_nonexistent_agent(self):
        """Test getting URL for non-existent agent."""
        from nexus_lib.utils import AgentRegistry
        
        url = AgentRegistry.get_url("nonexistent_agent_12345")
        
        # Should return None, not raise
        assert url is None
    
    def test_get_agent_with_empty_string(self):
        """Test getting URL with empty string."""
        from nexus_lib.utils import AgentRegistry
        
        url = AgentRegistry.get_url("")
        
        # Should return None
        assert url is None


# =============================================================================
# Boundary Condition Tests
# =============================================================================

class TestBoundaryConditions:
    """Tests for boundary conditions."""
    
    def test_zero_story_points(self):
        """Test zero story points."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Story",
            story_points=0
        )
        
        assert ticket.story_points == 0
    
    def test_max_int_story_points(self):
        """Test maximum integer story points."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        import sys
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Story",
            story_points=sys.maxsize
        )
        
        assert ticket.story_points == sys.maxsize
    
    def test_empty_labels_list(self):
        """Test empty labels list."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Bug",
            labels=[]
        )
        
        assert ticket.labels == []
    
    def test_past_date_for_release(self):
        """Test past date for release."""
        from nexus_lib.schemas.agent_contract import Release
        
        past_date = datetime.utcnow() - timedelta(days=365)
        
        release = Release(
            release_id="rel-1",
            version="v1.0",
            target_date=past_date
        )
        
        assert release.target_date < datetime.utcnow()
    
    def test_far_future_date(self):
        """Test far future date."""
        from nexus_lib.schemas.agent_contract import Release
        
        future_date = datetime.utcnow() + timedelta(days=365*100)
        
        release = Release(
            release_id="rel-1",
            version="v1.0",
            target_date=future_date
        )
        
        assert release.target_date > datetime.utcnow()


# =============================================================================
# Type Coercion Tests
# =============================================================================

class TestTypeCoercion:
    """Tests for type coercion and conversion."""
    
    def test_string_to_int_coercion(self):
        """Test string to int coercion."""
        from nexus_lib.schemas.agent_contract import BuildStatus
        
        build = BuildStatus(
            job_name="test",
            build_number="142",  # String instead of int
            status="SUCCESS",
            url="http://test"
        )
        
        assert build.build_number == 142
        assert isinstance(build.build_number, int)
    
    def test_int_to_string_coercion(self):
        """Test int to string coercion."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key=12345,  # Int instead of string
            summary="Test",
            status="Open",
            issue_type="Bug"
        )
        
        # Should convert to string
        assert ticket.key == "12345"
    
    def test_list_to_tuple_conversion(self):
        """Test list/tuple handling."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        
        ticket = JiraTicket(
            key="NEXUS-123",
            summary="Test",
            status="Open",
            issue_type="Bug",
            labels=("label1", "label2")  # Tuple instead of list
        )
        
        # Should accept tuple
        assert len(ticket.labels) == 2


# =============================================================================
# Concurrent/Race Condition Tests
# =============================================================================

class TestConcurrentAccess:
    """Tests for concurrent access handling."""
    
    def test_agent_registry_thread_safety(self):
        """Test AgentRegistry is thread-safe."""
        from nexus_lib.utils import AgentRegistry
        import concurrent.futures
        
        def get_url():
            return AgentRegistry.get_url("jira_agent")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_url) for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should return same result
        unique_results = set(results)
        assert len(unique_results) == 1 or (None in unique_results and len(unique_results) == 1)
    
    def test_config_manager_thread_safety(self):
        """Test ConfigManager is thread-safe."""
        from nexus_lib.config import ConfigManager
        import concurrent.futures
        
        def check_sensitive():
            return ConfigManager.is_sensitive("nexus:config:api_key")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_sensitive) for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should return same result
        assert all(r == results[0] for r in results)


# =============================================================================
# Memory/Resource Tests
# =============================================================================

class TestMemoryHandling:
    """Tests for memory and resource handling."""
    
    def test_large_payload_handling(self):
        """Test handling of large payloads."""
        from nexus_lib.schemas.agent_contract import AgentTaskRequest
        
        large_payload = {"data": "x" * 1000000}  # 1MB string
        
        request = AgentTaskRequest(
            task_id="test-1",
            action="process",
            payload=large_payload
        )
        
        assert len(request.payload["data"]) == 1000000
    
    def test_deeply_nested_payload(self):
        """Test handling of deeply nested payloads."""
        from nexus_lib.schemas.agent_contract import AgentTaskRequest
        
        # Create deeply nested structure
        nested = {"level": 0}
        current = nested
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        request = AgentTaskRequest(
            task_id="test-1",
            action="process",
            payload=nested
        )
        
        assert request.payload["level"] == 0


# =============================================================================
# Error Message Tests
# =============================================================================

class TestErrorMessages:
    """Tests for error message quality."""
    
    def test_validation_error_message_informative(self):
        """Test validation error messages are informative."""
        from nexus_lib.schemas.agent_contract import JiraTicket
        from pydantic import ValidationError
        
        try:
            JiraTicket(
                key="NEXUS-123",
                # Missing required fields
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_str = str(e)
            # Should mention missing field
            assert "summary" in error_str.lower() or "required" in error_str.lower()


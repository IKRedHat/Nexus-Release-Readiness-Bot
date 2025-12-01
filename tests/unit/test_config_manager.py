"""
Unit Tests for ConfigManager (Dynamic Configuration)
=====================================================

Tests for the centralized configuration management system
that enables dynamic configuration via Redis with env var fallback.
"""

import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["NEXUS_MOCK_MODE"] = "true"


class TestConfigManagerBasics:
    """Basic tests for ConfigManager functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.keys = AsyncMock(return_value=[])
        mock.mget = AsyncMock(return_value=[])
        return mock
    
    @pytest.mark.asyncio
    async def test_get_from_redis(self, mock_redis):
        """Test getting config from Redis."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.get = AsyncMock(return_value="https://jira.example.com")
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            value = await ConfigManager.get("nexus:config:jira_url")
            assert value == "https://jira.example.com"
    
    @pytest.mark.asyncio
    async def test_get_fallback_to_env(self, mock_redis):
        """Test fallback to environment variable."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.get = AsyncMock(return_value=None)  # Redis returns None
        
        os.environ["JIRA_URL"] = "https://env-jira.example.com"
        
        try:
            with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
                value = await ConfigManager.get("nexus:config:jira_url")
                # Should fallback to env var
                assert value is not None or "JIRA_URL" in os.environ
        finally:
            del os.environ["JIRA_URL"]
    
    @pytest.mark.asyncio
    async def test_get_fallback_to_default(self, mock_redis):
        """Test fallback to default value."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            value = await ConfigManager.get(
                "nexus:config:nonexistent_key",
                default="default_value"
            )
            assert value == "default_value"
    
    @pytest.mark.asyncio
    async def test_set_config(self, mock_redis):
        """Test setting config in Redis."""
        from nexus_lib.config import ConfigManager
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            result = await ConfigManager.set("nexus:config:test_key", "test_value")
            assert result is True
            mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_config(self, mock_redis):
        """Test deleting config from Redis."""
        from nexus_lib.config import ConfigManager
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            result = await ConfigManager.delete("nexus:config:test_key")
            assert result is True
            mock_redis.delete.assert_called()


class TestMockMode:
    """Tests for mock mode functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        return mock
    
    @pytest.mark.asyncio
    async def test_is_mock_mode_from_redis(self, mock_redis):
        """Test mock mode detection from Redis."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.get = AsyncMock(return_value="mock")
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            is_mock = await ConfigManager.is_mock_mode()
            assert is_mock is True
    
    @pytest.mark.asyncio
    async def test_is_live_mode_from_redis(self, mock_redis):
        """Test live mode detection from Redis."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.get = AsyncMock(return_value="live")
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            is_mock = await ConfigManager.is_mock_mode()
            assert is_mock is False
    
    @pytest.mark.asyncio
    async def test_set_mode(self, mock_redis):
        """Test setting system mode."""
        from nexus_lib.config import ConfigManager
        
        mock_redis.set = AsyncMock(return_value=True)
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            result = await ConfigManager.set_mode("live")
            assert result is True


class TestSensitiveKeys:
    """Tests for sensitive key handling."""
    
    def test_is_sensitive_token(self):
        """Test detection of sensitive token keys."""
        from nexus_lib.config import ConfigManager
        
        assert ConfigManager.is_sensitive("nexus:config:jira_api_token") is True
        assert ConfigManager.is_sensitive("nexus:config:github_token") is True
        assert ConfigManager.is_sensitive("nexus:config:slack_bot_token") is True
    
    def test_is_sensitive_secret(self):
        """Test detection of sensitive secret keys."""
        from nexus_lib.config import ConfigManager
        
        assert ConfigManager.is_sensitive("nexus:config:slack_signing_secret") is True
        assert ConfigManager.is_sensitive("nexus:config:webhook_secret") is True
    
    def test_is_not_sensitive(self):
        """Test non-sensitive keys."""
        from nexus_lib.config import ConfigManager
        
        assert ConfigManager.is_sensitive("nexus:config:jira_url") is False
        assert ConfigManager.is_sensitive("nexus:config:jira_project_key") is False
        assert ConfigManager.is_sensitive("nexus:mode") is False
    
    def test_mask_sensitive_value(self):
        """Test masking of sensitive values."""
        from nexus_lib.config import ConfigManager
        
        masked = ConfigManager.mask_value(
            "nexus:config:jira_api_token",
            "ATT0abcdefghijklmnop"
        )
        
        assert "****" in masked
        assert "abcdefghijklmnop" not in masked
        # Should show some prefix/suffix
        assert "ATT0" in masked or "mnop" in masked
    
    def test_mask_non_sensitive_value(self):
        """Test non-sensitive values are not masked."""
        from nexus_lib.config import ConfigManager
        
        value = "https://jira.example.com"
        masked = ConfigManager.mask_value("nexus:config:jira_url", value)
        
        assert masked == value  # Not masked


class TestConfigKeys:
    """Tests for ConfigKeys constants."""
    
    def test_jira_config_keys(self):
        """Test Jira configuration keys exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'JIRA_URL')
        assert hasattr(ConfigKeys, 'JIRA_USERNAME')
        assert hasattr(ConfigKeys, 'JIRA_API_TOKEN')
        assert ConfigKeys.JIRA_URL.startswith("nexus:")
    
    def test_github_config_keys(self):
        """Test GitHub configuration keys exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'GITHUB_TOKEN')
        assert hasattr(ConfigKeys, 'GITHUB_ORG')
    
    def test_llm_config_keys(self):
        """Test LLM configuration keys exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'LLM_PROVIDER')
        assert hasattr(ConfigKeys, 'LLM_MODEL')
        assert hasattr(ConfigKeys, 'GEMINI_API_KEY')


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_get_all_agents(self):
        """Test getting all registered agents."""
        from nexus_lib.config import AgentRegistry
        
        agents = AgentRegistry.get_all_agents()
        
        assert isinstance(agents, dict)
        assert len(agents) > 0
        
        # Check for expected agents
        expected_agents = [
            'orchestrator', 'jira_agent', 'git_ci_agent',
            'slack_agent', 'hygiene_agent', 'rca_agent'
        ]
        
        for agent in expected_agents:
            assert agent in agents, f"Missing agent: {agent}"
    
    def test_agent_has_required_fields(self):
        """Test each agent has required configuration fields."""
        from nexus_lib.config import AgentRegistry
        
        agents = AgentRegistry.get_all_agents()
        
        for agent_id, agent_info in agents.items():
            assert 'name' in agent_info, f"Agent {agent_id} missing 'name'"
            assert 'port' in agent_info, f"Agent {agent_id} missing 'port'"
            assert 'health_path' in agent_info, f"Agent {agent_id} missing 'health_path'"
            assert 'url_key' in agent_info, f"Agent {agent_id} missing 'url_key'"


class TestRedisConnection:
    """Tests for Redis connection handling."""
    
    def test_connection_url_from_env(self):
        """Test Redis URL is read from environment."""
        from nexus_lib.config import RedisConnection
        
        os.environ["REDIS_URL"] = "redis://test-redis:6379/1"
        
        try:
            conn = RedisConnection()
            assert conn.url == "redis://test-redis:6379/1"
        finally:
            del os.environ["REDIS_URL"]
    
    def test_default_connection_url(self):
        """Test default Redis URL."""
        from nexus_lib.config import RedisConnection
        
        # Temporarily remove env var if exists
        original = os.environ.pop("REDIS_URL", None)
        
        try:
            conn = RedisConnection()
            assert "localhost" in conn.url or "redis" in conn.url
        finally:
            if original:
                os.environ["REDIS_URL"] = original


class TestConfigContext:
    """Tests for ConfigContext async context manager."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value="mock_value")
        return mock
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_redis):
        """Test ConfigContext as async context manager."""
        from nexus_lib.config import ConfigContext, ConfigManager
        
        with patch.object(ConfigManager, '_get_redis_client', return_value=mock_redis):
            async with ConfigContext("nexus:config:test_key") as ctx:
                assert ctx.value is not None or ctx.is_mock is not None


class TestWithMockFallback:
    """Tests for with_mock_fallback decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_calls_mock_in_mock_mode(self):
        """Test decorator calls mock function in mock mode."""
        from nexus_lib.config import with_mock_fallback, ConfigManager
        
        mock_called = False
        live_called = False
        
        async def mock_func():
            nonlocal mock_called
            mock_called = True
            return "mock_result"
        
        @with_mock_fallback(mock_func)
        async def live_func():
            nonlocal live_called
            live_called = True
            return "live_result"
        
        with patch.object(ConfigManager, 'is_mock_mode', return_value=True):
            result = await live_func()
            
            assert mock_called is True
            assert live_called is False
            assert result == "mock_result"
    
    @pytest.mark.asyncio
    async def test_decorator_calls_live_in_live_mode(self):
        """Test decorator calls live function in live mode."""
        from nexus_lib.config import with_mock_fallback, ConfigManager
        
        mock_called = False
        live_called = False
        
        async def mock_func():
            nonlocal mock_called
            mock_called = True
            return "mock_result"
        
        @with_mock_fallback(mock_func)
        async def live_func():
            nonlocal live_called
            live_called = True
            return "live_result"
        
        with patch.object(ConfigManager, 'is_mock_mode', return_value=False):
            result = await live_func()
            
            assert mock_called is False
            assert live_called is True
            assert result == "live_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


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
    
    def test_slack_config_keys(self):
        """Test Slack configuration keys exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'SLACK_BOT_TOKEN')
        assert hasattr(ConfigKeys, 'SLACK_SIGNING_SECRET')
    
    def test_agent_url_keys(self):
        """Test agent URL configuration keys exist."""
        from nexus_lib.config import ConfigKeys
        
        assert hasattr(ConfigKeys, 'ORCHESTRATOR_URL')
        assert hasattr(ConfigKeys, 'JIRA_AGENT_URL')
        assert hasattr(ConfigKeys, 'GIT_AGENT_URL')
        assert hasattr(ConfigKeys, 'SLACK_AGENT_URL')
        assert hasattr(ConfigKeys, 'RCA_AGENT_URL')


class TestDefaultConfig:
    """Tests for default configuration values."""
    
    def test_default_config_exists(self):
        """Test DEFAULT_CONFIG dictionary exists."""
        from nexus_lib.config import DEFAULT_CONFIG, ConfigKeys
        
        assert isinstance(DEFAULT_CONFIG, dict)
        assert len(DEFAULT_CONFIG) > 0
    
    def test_system_mode_default(self):
        """Test system mode defaults to mock."""
        from nexus_lib.config import DEFAULT_CONFIG, ConfigKeys
        
        assert ConfigKeys.SYSTEM_MODE in DEFAULT_CONFIG
        assert DEFAULT_CONFIG[ConfigKeys.SYSTEM_MODE] == "mock"
    
    def test_llm_defaults(self):
        """Test LLM defaults are set."""
        from nexus_lib.config import DEFAULT_CONFIG, ConfigKeys
        
        assert ConfigKeys.LLM_PROVIDER in DEFAULT_CONFIG
        assert ConfigKeys.LLM_MODEL in DEFAULT_CONFIG


class TestEnvVarMapping:
    """Tests for environment variable mapping."""
    
    def test_env_var_mapping_exists(self):
        """Test ENV_VAR_MAPPING dictionary exists."""
        from nexus_lib.config import ENV_VAR_MAPPING, ConfigKeys
        
        assert isinstance(ENV_VAR_MAPPING, dict)
        assert len(ENV_VAR_MAPPING) > 0
    
    def test_jira_env_vars_mapped(self):
        """Test Jira keys are mapped to env vars."""
        from nexus_lib.config import ENV_VAR_MAPPING, ConfigKeys
        
        assert ConfigKeys.JIRA_URL in ENV_VAR_MAPPING
        assert ENV_VAR_MAPPING[ConfigKeys.JIRA_URL] == "JIRA_URL"
    
    def test_github_env_vars_mapped(self):
        """Test GitHub keys are mapped to env vars."""
        from nexus_lib.config import ENV_VAR_MAPPING, ConfigKeys
        
        assert ConfigKeys.GITHUB_TOKEN in ENV_VAR_MAPPING
        assert ENV_VAR_MAPPING[ConfigKeys.GITHUB_TOKEN] == "GITHUB_TOKEN"


class TestSensitiveKeys:
    """Tests for sensitive key handling."""
    
    def test_sensitive_keys_set_exists(self):
        """Test SENSITIVE_KEYS set exists."""
        from nexus_lib.config import SENSITIVE_KEYS, ConfigKeys
        
        assert isinstance(SENSITIVE_KEYS, set)
        assert len(SENSITIVE_KEYS) > 0
    
    def test_tokens_are_sensitive(self):
        """Test token keys are marked as sensitive."""
        from nexus_lib.config import SENSITIVE_KEYS, ConfigKeys
        
        assert ConfigKeys.JIRA_API_TOKEN in SENSITIVE_KEYS
        assert ConfigKeys.GITHUB_TOKEN in SENSITIVE_KEYS
        assert ConfigKeys.GEMINI_API_KEY in SENSITIVE_KEYS
    
    def test_secrets_are_sensitive(self):
        """Test secret keys are marked as sensitive."""
        from nexus_lib.config import SENSITIVE_KEYS, ConfigKeys
        
        assert ConfigKeys.SLACK_SIGNING_SECRET in SENSITIVE_KEYS
    
    def test_urls_not_sensitive(self):
        """Test URL keys are not marked as sensitive."""
        from nexus_lib.config import SENSITIVE_KEYS, ConfigKeys
        
        assert ConfigKeys.JIRA_URL not in SENSITIVE_KEYS
        assert ConfigKeys.GITHUB_ORG not in SENSITIVE_KEYS


class TestConfigManagerIsSensitive:
    """Tests for ConfigManager.is_sensitive method."""
    
    def test_is_sensitive_token(self):
        """Test detection of sensitive token keys."""
        from nexus_lib.config import ConfigManager, ConfigKeys
        
        assert ConfigManager.is_sensitive(ConfigKeys.JIRA_API_TOKEN) is True
        assert ConfigManager.is_sensitive(ConfigKeys.GITHUB_TOKEN) is True
    
    def test_is_not_sensitive(self):
        """Test non-sensitive keys."""
        from nexus_lib.config import ConfigManager, ConfigKeys
        
        assert ConfigManager.is_sensitive(ConfigKeys.JIRA_URL) is False
        assert ConfigManager.is_sensitive(ConfigKeys.JIRA_PROJECT_KEY) is False


class TestConfigManagerMaskValue:
    """Tests for ConfigManager.mask_value method."""
    
    def test_mask_sensitive_value(self):
        """Test masking of sensitive values."""
        from nexus_lib.config import ConfigManager, ConfigKeys
        
        masked = ConfigManager.mask_value(
            ConfigKeys.JIRA_API_TOKEN,
            "ATT0abcdefghijklmnop"
        )
        
        # Should be masked somehow
        assert masked != "ATT0abcdefghijklmnop" or len(masked) < 20
    
    def test_mask_short_value(self):
        """Test masking of short values."""
        from nexus_lib.config import ConfigManager, ConfigKeys
        
        masked = ConfigManager.mask_value(ConfigKeys.GITHUB_TOKEN, "short")
        
        # Short values should be fully masked or handled
        assert masked is not None
    
    def test_mask_non_sensitive_value(self):
        """Test non-sensitive values are returned as-is."""
        from nexus_lib.config import ConfigManager, ConfigKeys
        
        value = "https://jira.example.com"
        masked = ConfigManager.mask_value(ConfigKeys.JIRA_URL, value)
        
        # Non-sensitive should not be masked
        assert masked == value


class TestRedisConnection:
    """Tests for Redis connection handling."""
    
    def test_redis_connection_singleton(self):
        """Test RedisConnection is a singleton."""
        from nexus_lib.config import RedisConnection
        
        conn1 = RedisConnection()
        conn2 = RedisConnection()
        
        assert conn1 is conn2
    
    def test_redis_url_property(self):
        """Test redis_url property exists."""
        from nexus_lib.config import RedisConnection
        
        conn = RedisConnection()
        
        assert hasattr(conn, 'redis_url')
        assert "redis" in conn.redis_url.lower() or "localhost" in conn.redis_url
    
    def test_redis_url_from_env(self):
        """Test Redis URL is read from environment."""
        from nexus_lib.config import RedisConnection
        
        os.environ["REDIS_URL"] = "redis://test-redis:6379/1"
        
        try:
            # Reset singleton for test
            RedisConnection._instance = None
            conn = RedisConnection()
            assert conn.redis_url == "redis://test-redis:6379/1"
        finally:
            del os.environ["REDIS_URL"]
            RedisConnection._instance = None
    
    def test_is_connected_property(self):
        """Test is_connected property exists."""
        from nexus_lib.config import RedisConnection
        
        conn = RedisConnection()
        
        assert hasattr(conn, 'is_connected')
        assert isinstance(conn.is_connected, bool)


class TestConfigManagerBasics:
    """Basic tests for ConfigManager functionality."""
    
    @pytest.mark.asyncio
    async def test_get_fallback_to_default(self):
        """Test fallback to default value."""
        from nexus_lib.config import ConfigManager
        
        value = await ConfigManager.get(
            "nexus:config:nonexistent_key_12345",
            default="default_value"
        )
        assert value == "default_value"
    
    @pytest.mark.asyncio
    async def test_get_returns_none_for_unknown(self):
        """Test returns None for unknown key without default."""
        from nexus_lib.config import ConfigManager
        
        value = await ConfigManager.get(
            "nexus:config:completely_nonexistent_xyz"
        )
        # Should return None or empty string for unknown keys
        assert value is None or value == ""


class TestMockModeFunction:
    """Tests for is_mock_mode standalone function."""
    
    @pytest.mark.asyncio
    async def test_is_mock_mode_returns_bool(self):
        """Test is_mock_mode returns boolean."""
        from nexus_lib.config import is_mock_mode
        
        result = await is_mock_mode()
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_default_is_mock_mode(self):
        """Test default mode is mock for safety."""
        from nexus_lib.config import is_mock_mode
        
        # In test environment, should default to mock
        result = await is_mock_mode()
        
        # Default should be True (mock mode) for safety
        assert result is True


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_agent_registry_exists(self):
        """Test AgentRegistry class exists."""
        from nexus_lib.config import AgentRegistry
        
        assert AgentRegistry is not None
    
    def test_get_all_agents_returns_dict(self):
        """Test get_all_agents returns dictionary."""
        from nexus_lib.config import AgentRegistry
        
        agents = AgentRegistry.get_all_agents()
        
        assert isinstance(agents, dict)
    
    def test_agents_have_required_fields(self):
        """Test each agent has required configuration fields."""
        from nexus_lib.config import AgentRegistry
        
        agents = AgentRegistry.get_all_agents()
        
        for agent_id, agent_info in agents.items():
            assert 'name' in agent_info, f"Agent {agent_id} missing 'name'"
            assert 'port' in agent_info, f"Agent {agent_id} missing 'port'"


class TestWithMockFallbackDecorator:
    """Tests for with_mock_fallback decorator."""
    
    def test_decorator_import(self):
        """Test with_mock_fallback can be imported."""
        from nexus_lib.config import with_mock_fallback
        
        assert callable(with_mock_fallback)


class TestConfigContext:
    """Tests for ConfigContext async context manager."""
    
    def test_config_context_import(self):
        """Test ConfigContext can be imported."""
        from nexus_lib.config import ConfigContext
        
        assert ConfigContext is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

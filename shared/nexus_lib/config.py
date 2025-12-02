"""
Nexus Dynamic Configuration Manager
===================================

Centralized configuration management with Redis-backed dynamic config
and environment variable fallback for resilience.

Features:
- Redis-first dynamic configuration
- Environment variable fallback
- Mock mode toggle
- Secure credential management
- Connection pooling and caching

Author: Nexus Team
Version: 2.3.0
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration Keys and Defaults
# =============================================================================

class ConfigKeys:
    """Standard configuration keys used across the system."""
    
    # System Mode
    SYSTEM_MODE = "nexus:mode"  # "mock" or "live"
    
    # Jira Configuration
    JIRA_URL = "nexus:config:jira_url"
    JIRA_USERNAME = "nexus:config:jira_username"
    JIRA_API_TOKEN = "nexus:config:jira_api_token"
    JIRA_PROJECT_KEY = "nexus:config:jira_project_key"
    
    # GitHub Configuration
    GITHUB_TOKEN = "nexus:config:github_token"
    GITHUB_ORG = "nexus:config:github_org"
    GITHUB_REPO = "nexus:config:github_repo"
    
    # Jenkins Configuration
    JENKINS_URL = "nexus:config:jenkins_url"
    JENKINS_USERNAME = "nexus:config:jenkins_username"
    JENKINS_API_TOKEN = "nexus:config:jenkins_api_token"
    
    # LLM Configuration
    LLM_PROVIDER = "nexus:config:llm_provider"
    LLM_MODEL = "nexus:config:llm_model"
    LLM_API_KEY = "nexus:config:llm_api_key"
    LLM_BASE_URL = "nexus:config:llm_base_url"
    LLM_TEMPERATURE = "nexus:config:llm_temperature"
    LLM_MAX_TOKENS = "nexus:config:llm_max_tokens"
    
    # Provider-specific API Keys
    OPENAI_API_KEY = "nexus:config:openai_api_key"
    OPENAI_ORG = "nexus:config:openai_org"
    GEMINI_API_KEY = "nexus:config:gemini_api_key"
    ANTHROPIC_API_KEY = "nexus:config:anthropic_api_key"
    GROQ_API_KEY = "nexus:config:groq_api_key"
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = "nexus:config:azure_openai_endpoint"
    AZURE_OPENAI_API_VERSION = "nexus:config:azure_openai_api_version"
    AZURE_OPENAI_DEPLOYMENT = "nexus:config:azure_openai_deployment"
    
    # Local/Self-hosted LLMs
    OLLAMA_BASE_URL = "nexus:config:ollama_base_url"
    VLLM_BASE_URL = "nexus:config:vllm_base_url"
    
    # Slack Configuration
    SLACK_BOT_TOKEN = "nexus:config:slack_bot_token"
    SLACK_SIGNING_SECRET = "nexus:config:slack_signing_secret"
    SLACK_APP_TOKEN = "nexus:config:slack_app_token"
    
    # Confluence Configuration
    CONFLUENCE_URL = "nexus:config:confluence_url"
    CONFLUENCE_USERNAME = "nexus:config:confluence_username"
    CONFLUENCE_API_TOKEN = "nexus:config:confluence_api_token"
    CONFLUENCE_SPACE_KEY = "nexus:config:confluence_space_key"
    
    # Agent URLs (for inter-service communication)
    ORCHESTRATOR_URL = "nexus:config:orchestrator_url"
    JIRA_AGENT_URL = "nexus:config:jira_agent_url"
    GIT_AGENT_URL = "nexus:config:git_agent_url"
    REPORTING_AGENT_URL = "nexus:config:reporting_agent_url"
    SLACK_AGENT_URL = "nexus:config:slack_agent_url"
    HYGIENE_AGENT_URL = "nexus:config:hygiene_agent_url"
    RCA_AGENT_URL = "nexus:config:rca_agent_url"
    ANALYTICS_URL = "nexus:config:analytics_url"
    WEBHOOKS_URL = "nexus:config:webhooks_url"


# Default values for configuration
DEFAULT_CONFIG = {
    ConfigKeys.SYSTEM_MODE: "mock",
    ConfigKeys.JIRA_URL: "https://your-org.atlassian.net",
    ConfigKeys.JIRA_PROJECT_KEY: "PROJ",
    ConfigKeys.GITHUB_ORG: "your-org",
    ConfigKeys.GITHUB_REPO: "your-repo",
    ConfigKeys.JENKINS_URL: "http://jenkins:8080",
    ConfigKeys.LLM_PROVIDER: "google",
    ConfigKeys.LLM_MODEL: "gemini-1.5-pro",
    ConfigKeys.ORCHESTRATOR_URL: "http://orchestrator:8080",
    ConfigKeys.JIRA_AGENT_URL: "http://jira-agent:8081",
    ConfigKeys.GIT_AGENT_URL: "http://git-agent:8082",
    ConfigKeys.REPORTING_AGENT_URL: "http://reporting-agent:8083",
    ConfigKeys.SLACK_AGENT_URL: "http://slack-agent:8084",
    ConfigKeys.HYGIENE_AGENT_URL: "http://hygiene-agent:8005",
    ConfigKeys.RCA_AGENT_URL: "http://rca-agent:8006",
    ConfigKeys.ANALYTICS_URL: "http://analytics:8086",
    ConfigKeys.WEBHOOKS_URL: "http://webhooks:8087",
}

# Map Redis keys to environment variable names
ENV_VAR_MAPPING = {
    ConfigKeys.SYSTEM_MODE: "NEXUS_MODE",
    ConfigKeys.JIRA_URL: "JIRA_URL",
    ConfigKeys.JIRA_USERNAME: "JIRA_USERNAME",
    ConfigKeys.JIRA_API_TOKEN: "JIRA_API_TOKEN",
    ConfigKeys.JIRA_PROJECT_KEY: "JIRA_PROJECT_KEY",
    ConfigKeys.GITHUB_TOKEN: "GITHUB_TOKEN",
    ConfigKeys.GITHUB_ORG: "GITHUB_ORG",
    ConfigKeys.GITHUB_REPO: "GITHUB_REPO",
    ConfigKeys.JENKINS_URL: "JENKINS_URL",
    ConfigKeys.JENKINS_USERNAME: "JENKINS_USERNAME",
    ConfigKeys.JENKINS_API_TOKEN: "JENKINS_API_TOKEN",
    ConfigKeys.LLM_PROVIDER: "LLM_PROVIDER",
    ConfigKeys.LLM_MODEL: "LLM_MODEL",
    ConfigKeys.LLM_API_KEY: "LLM_API_KEY",
    ConfigKeys.LLM_BASE_URL: "LLM_BASE_URL",
    ConfigKeys.LLM_TEMPERATURE: "LLM_TEMPERATURE",
    ConfigKeys.LLM_MAX_TOKENS: "LLM_MAX_TOKENS",
    ConfigKeys.OPENAI_API_KEY: "OPENAI_API_KEY",
    ConfigKeys.OPENAI_ORG: "OPENAI_ORG",
    ConfigKeys.GEMINI_API_KEY: "GEMINI_API_KEY",
    ConfigKeys.ANTHROPIC_API_KEY: "ANTHROPIC_API_KEY",
    ConfigKeys.GROQ_API_KEY: "GROQ_API_KEY",
    ConfigKeys.AZURE_OPENAI_ENDPOINT: "AZURE_OPENAI_ENDPOINT",
    ConfigKeys.AZURE_OPENAI_API_VERSION: "AZURE_OPENAI_API_VERSION",
    ConfigKeys.AZURE_OPENAI_DEPLOYMENT: "AZURE_OPENAI_DEPLOYMENT",
    ConfigKeys.OLLAMA_BASE_URL: "OLLAMA_BASE_URL",
    ConfigKeys.VLLM_BASE_URL: "VLLM_BASE_URL",
    ConfigKeys.SLACK_BOT_TOKEN: "SLACK_BOT_TOKEN",
    ConfigKeys.SLACK_SIGNING_SECRET: "SLACK_SIGNING_SECRET",
    ConfigKeys.SLACK_APP_TOKEN: "SLACK_APP_TOKEN",
    ConfigKeys.CONFLUENCE_URL: "CONFLUENCE_URL",
    ConfigKeys.CONFLUENCE_USERNAME: "CONFLUENCE_USERNAME",
    ConfigKeys.CONFLUENCE_API_TOKEN: "CONFLUENCE_API_TOKEN",
    ConfigKeys.CONFLUENCE_SPACE_KEY: "CONFLUENCE_SPACE_KEY",
    ConfigKeys.ORCHESTRATOR_URL: "ORCHESTRATOR_URL",
    ConfigKeys.JIRA_AGENT_URL: "JIRA_AGENT_URL",
    ConfigKeys.GIT_AGENT_URL: "GIT_AGENT_URL",
    ConfigKeys.REPORTING_AGENT_URL: "REPORTING_AGENT_URL",
    ConfigKeys.SLACK_AGENT_URL: "SLACK_AGENT_URL",
    ConfigKeys.HYGIENE_AGENT_URL: "HYGIENE_AGENT_URL",
    ConfigKeys.RCA_AGENT_URL: "RCA_AGENT_URL",
    ConfigKeys.ANALYTICS_URL: "ANALYTICS_URL",
    ConfigKeys.WEBHOOKS_URL: "WEBHOOKS_URL",
}

# Keys that contain sensitive data (should be masked in UI)
SENSITIVE_KEYS = {
    ConfigKeys.JIRA_API_TOKEN,
    ConfigKeys.GITHUB_TOKEN,
    ConfigKeys.JENKINS_API_TOKEN,
    ConfigKeys.LLM_API_KEY,
    ConfigKeys.OPENAI_API_KEY,
    ConfigKeys.GEMINI_API_KEY,
    ConfigKeys.ANTHROPIC_API_KEY,
    ConfigKeys.GROQ_API_KEY,
    ConfigKeys.SLACK_BOT_TOKEN,
    ConfigKeys.SLACK_SIGNING_SECRET,
    ConfigKeys.SLACK_APP_TOKEN,
    ConfigKeys.CONFLUENCE_API_TOKEN,
}


# =============================================================================
# Redis Connection Manager
# =============================================================================

class RedisConnection:
    """Manages Redis connection with automatic reconnection."""
    
    _instance: Optional["RedisConnection"] = None
    _redis: Any = None
    _connected: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def redis_url(self) -> str:
        return os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    async def get_client(self):
        """Get or create Redis client."""
        if self._redis is None or not self._connected:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
                # Test connection
                await self._redis.ping()
                self._connected = True
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self._connected = False
                self._redis = None
        return self._redis
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# Configuration Manager
# =============================================================================

class ConfigManager:
    """
    Dynamic configuration manager with Redis-backed storage.
    
    Priority order:
    1. Redis (dynamic configuration)
    2. Environment variables (static configuration)
    3. Default values
    
    Usage:
        # Get a configuration value
        jira_url = await ConfigManager.get("nexus:config:jira_url")
        
        # Check if system is in mock mode
        if await ConfigManager.is_mock_mode():
            return mock_response()
        
        # Set a configuration value
        await ConfigManager.set("nexus:config:jira_url", "https://new-jira.atlassian.net")
    """
    
    _cache: Dict[str, Any] = {}
    _cache_ttl: Dict[str, datetime] = {}
    _cache_duration = timedelta(seconds=30)
    
    @classmethod
    async def get(
        cls,
        key: str,
        default: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (e.g., "nexus:config:jira_url")
            default: Default value if not found
            use_cache: Whether to use cached values
            
        Returns:
            Configuration value or default
        """
        # Check cache first
        if use_cache and key in cls._cache:
            if datetime.now() < cls._cache_ttl.get(key, datetime.min):
                return cls._cache[key]
        
        # Try Redis first
        value = await cls._get_from_redis(key)
        
        if value is None:
            # Fall back to environment variable
            env_var = ENV_VAR_MAPPING.get(key)
            if env_var:
                value = os.environ.get(env_var)
        
        if value is None:
            # Fall back to default
            value = DEFAULT_CONFIG.get(key, default)
        
        # Update cache
        if value is not None:
            cls._cache[key] = value
            cls._cache_ttl[key] = datetime.now() + cls._cache_duration
        
        return value
    
    @classmethod
    async def get_env(cls, env_var: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get config by environment variable name.
        
        Args:
            env_var: Environment variable name (e.g., "JIRA_URL")
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        # Find the Redis key for this env var
        redis_key = None
        for rkey, evar in ENV_VAR_MAPPING.items():
            if evar == env_var:
                redis_key = rkey
                break
        
        if redis_key:
            return await cls.get(redis_key, default)
        
        # No mapping, just get from env
        return os.environ.get(env_var, default)
    
    @classmethod
    async def set(cls, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set a configuration value in Redis.
        
        Args:
            key: Configuration key
            value: Value to set
            ttl: Optional TTL in seconds
            
        Returns:
            True if successful
        """
        try:
            redis = await RedisConnection().get_client()
            if redis:
                if ttl:
                    await redis.setex(key, ttl, value)
                else:
                    await redis.set(key, value)
                
                # Update cache
                cls._cache[key] = value
                cls._cache_ttl[key] = datetime.now() + cls._cache_duration
                
                logger.info(f"Config updated: {cls._mask_key(key)}")
                return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
        return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """Delete a configuration key from Redis."""
        try:
            redis = await RedisConnection().get_client()
            if redis:
                await redis.delete(key)
                cls._cache.pop(key, None)
                cls._cache_ttl.pop(key, None)
                return True
        except Exception as e:
            logger.error(f"Failed to delete config {key}: {e}")
        return False
    
    @classmethod
    async def get_all(cls, pattern: str = "nexus:config:*") -> Dict[str, str]:
        """
        Get all configuration values matching a pattern.
        
        Args:
            pattern: Redis key pattern
            
        Returns:
            Dictionary of key-value pairs
        """
        config = {}
        
        try:
            redis = await RedisConnection().get_client()
            if redis:
                keys = await redis.keys(pattern)
                if keys:
                    values = await redis.mget(keys)
                    for key, value in zip(keys, values):
                        if value is not None:
                            config[key] = value
        except Exception as e:
            logger.warning(f"Failed to get config from Redis: {e}")
        
        # Fill in missing values from env vars and defaults
        for redis_key, env_var in ENV_VAR_MAPPING.items():
            if redis_key not in config:
                env_value = os.environ.get(env_var)
                if env_value:
                    config[redis_key] = env_value
                elif redis_key in DEFAULT_CONFIG:
                    config[redis_key] = DEFAULT_CONFIG[redis_key]
        
        return config
    
    @classmethod
    async def set_bulk(cls, config: Dict[str, str]) -> bool:
        """Set multiple configuration values at once."""
        try:
            redis = await RedisConnection().get_client()
            if redis:
                pipe = redis.pipeline()
                for key, value in config.items():
                    pipe.set(key, value)
                await pipe.execute()
                
                # Update cache
                for key, value in config.items():
                    cls._cache[key] = value
                    cls._cache_ttl[key] = datetime.now() + cls._cache_duration
                
                return True
        except Exception as e:
            logger.error(f"Failed to set bulk config: {e}")
        return False
    
    @classmethod
    async def is_mock_mode(cls) -> bool:
        """
        Check if the system is in mock mode.
        
        Returns:
            True if in mock mode, False for live mode
        """
        mode = await cls.get(ConfigKeys.SYSTEM_MODE)
        return mode != "live"
    
    @classmethod
    async def set_mode(cls, mode: str) -> bool:
        """
        Set the system mode.
        
        Args:
            mode: "mock" or "live"
            
        Returns:
            True if successful
        """
        if mode not in ("mock", "live"):
            raise ValueError("Mode must be 'mock' or 'live'")
        return await cls.set(ConfigKeys.SYSTEM_MODE, mode)
    
    @classmethod
    async def get_mode(cls) -> str:
        """Get current system mode."""
        return await cls.get(ConfigKeys.SYSTEM_MODE, "mock")
    
    @classmethod
    def clear_cache(cls):
        """Clear the configuration cache."""
        cls._cache.clear()
        cls._cache_ttl.clear()
    
    @classmethod
    async def _get_from_redis(cls, key: str) -> Optional[str]:
        """Get value from Redis with error handling."""
        try:
            redis = await RedisConnection().get_client()
            if redis:
                return await redis.get(key)
        except Exception as e:
            logger.debug(f"Redis get failed for {key}: {e}")
        return None
    
    @classmethod
    def _mask_key(cls, key: str) -> str:
        """Mask sensitive key names in logs."""
        if key in SENSITIVE_KEYS:
            return f"{key}=****"
        return key
    
    @classmethod
    def is_sensitive(cls, key: str) -> bool:
        """Check if a key contains sensitive data."""
        return key in SENSITIVE_KEYS
    
    @classmethod
    def mask_value(cls, key: str, value: str) -> str:
        """Mask a value if it's sensitive."""
        if cls.is_sensitive(key) and value:
            if len(value) <= 8:
                return "****"
            return value[:4] + "****" + value[-4:]
        return value


# =============================================================================
# Helper Functions for Agent Integration
# =============================================================================

async def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Shorthand for ConfigManager.get()."""
    return await ConfigManager.get(key, default)


async def is_mock_mode() -> bool:
    """Shorthand for ConfigManager.is_mock_mode()."""
    return await ConfigManager.is_mock_mode()


async def with_mock_fallback(
    live_func,
    mock_func,
    *args,
    **kwargs
):
    """
    Execute live or mock function based on system mode.
    
    Usage:
        result = await with_mock_fallback(
            live_func=real_jira_call,
            mock_func=mock_jira_response,
            ticket_key="PROJ-123"
        )
    """
    if await is_mock_mode():
        if asyncio.iscoroutinefunction(mock_func):
            return await mock_func(*args, **kwargs)
        return mock_func(*args, **kwargs)
    else:
        if asyncio.iscoroutinefunction(live_func):
            return await live_func(*args, **kwargs)
        return live_func(*args, **kwargs)


class ConfigContext:
    """
    Context manager for configuration-aware operations.
    
    Usage:
        async with ConfigContext() as config:
            jira_url = config.jira_url
            if config.is_mock:
                return mock_response()
    """
    
    def __init__(self):
        self._config: Dict[str, str] = {}
        self._is_mock: bool = True
    
    async def __aenter__(self):
        self._config = await ConfigManager.get_all()
        self._is_mock = await ConfigManager.is_mock_mode()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @property
    def is_mock(self) -> bool:
        return self._is_mock
    
    @property
    def jira_url(self) -> Optional[str]:
        return self._config.get(ConfigKeys.JIRA_URL)
    
    @property
    def jira_username(self) -> Optional[str]:
        return self._config.get(ConfigKeys.JIRA_USERNAME)
    
    @property
    def jira_token(self) -> Optional[str]:
        return self._config.get(ConfigKeys.JIRA_API_TOKEN)
    
    @property
    def github_token(self) -> Optional[str]:
        return self._config.get(ConfigKeys.GITHUB_TOKEN)
    
    @property
    def github_org(self) -> Optional[str]:
        return self._config.get(ConfigKeys.GITHUB_ORG)
    
    @property
    def jenkins_url(self) -> Optional[str]:
        return self._config.get(ConfigKeys.JENKINS_URL)
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        return self._config.get(ConfigKeys.GEMINI_API_KEY)
    
    @property
    def llm_provider(self) -> Optional[str]:
        return self._config.get(ConfigKeys.LLM_PROVIDER)
    
    @property
    def llm_model(self) -> Optional[str]:
        return self._config.get(ConfigKeys.LLM_MODEL)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._config.get(key, default)


# =============================================================================
# Agent Health Registry
# =============================================================================

class AgentRegistry:
    """Registry for tracking agent health and endpoints."""
    
    AGENTS = {
        "orchestrator": {
            "name": "Central Orchestrator",
            "url_key": ConfigKeys.ORCHESTRATOR_URL,
            "port": 8080,
            "health_path": "/health"
        },
        "jira_agent": {
            "name": "Jira Agent",
            "url_key": ConfigKeys.JIRA_AGENT_URL,
            "port": 8081,
            "health_path": "/health"
        },
        "git_agent": {
            "name": "Git/CI Agent",
            "url_key": ConfigKeys.GIT_AGENT_URL,
            "port": 8082,
            "health_path": "/health"
        },
        "reporting_agent": {
            "name": "Reporting Agent",
            "url_key": ConfigKeys.REPORTING_AGENT_URL,
            "port": 8083,
            "health_path": "/health"
        },
        "slack_agent": {
            "name": "Slack Agent",
            "url_key": ConfigKeys.SLACK_AGENT_URL,
            "port": 8084,
            "health_path": "/health"
        },
        "hygiene_agent": {
            "name": "Jira Hygiene Agent",
            "url_key": ConfigKeys.HYGIENE_AGENT_URL,
            "port": 8005,
            "health_path": "/health"
        },
        "rca_agent": {
            "name": "RCA Agent",
            "url_key": ConfigKeys.RCA_AGENT_URL,
            "port": 8006,
            "health_path": "/health"
        },
        "analytics": {
            "name": "Analytics Service",
            "url_key": ConfigKeys.ANALYTICS_URL,
            "port": 8086,
            "health_path": "/health"
        },
        "webhooks": {
            "name": "Webhooks Service",
            "url_key": ConfigKeys.WEBHOOKS_URL,
            "port": 8087,
            "health_path": "/health"
        },
    }
    
    @classmethod
    async def get_agent_url(cls, agent_id: str) -> Optional[str]:
        """Get the URL for an agent."""
        agent = cls.AGENTS.get(agent_id)
        if agent:
            return await ConfigManager.get(agent["url_key"])
        return None
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, dict]:
        """Get all registered agents."""
        return cls.AGENTS.copy()


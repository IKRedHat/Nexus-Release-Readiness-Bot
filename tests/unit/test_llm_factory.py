"""
Unit Tests for New LLM Factory (LangGraph Integration)
======================================================

Tests for the new LLM Factory that supports multiple providers
via LangChain and dynamic Redis configuration.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add orchestrator path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/orchestrator")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "mock"


class TestLLMProviderEnum:
    """Tests for LLMProvider enum."""
    
    def test_provider_values(self):
        """Test all provider values are defined."""
        from app.core.llm_factory import LLMProvider
        
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.AZURE_OPENAI.value == "azure_openai"
        assert LLMProvider.GEMINI.value == "gemini"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.GROQ.value == "groq"
        assert LLMProvider.VLLM.value == "vllm"
        assert LLMProvider.MOCK.value == "mock"
    
    def test_provider_count(self):
        """Test we have 8 providers."""
        from app.core.llm_factory import LLMProvider
        
        assert len(LLMProvider) == 8


class TestProviderConfigs:
    """Tests for provider configuration registry."""
    
    def test_all_providers_have_config(self):
        """Test all providers have configuration."""
        from app.core.llm_factory import LLMProvider, PROVIDER_CONFIGS
        
        for provider in LLMProvider:
            assert provider in PROVIDER_CONFIGS, f"Missing config for {provider}"
    
    def test_config_structure(self):
        """Test config has required fields."""
        from app.core.llm_factory import PROVIDER_CONFIGS, LLMProvider
        
        for provider, config in PROVIDER_CONFIGS.items():
            assert hasattr(config, 'display_name'), f"{provider} missing display_name"
            assert hasattr(config, 'required_fields'), f"{provider} missing required_fields"
            assert hasattr(config, 'optional_fields'), f"{provider} missing optional_fields"
            assert hasattr(config, 'default_model'), f"{provider} missing default_model"
            assert hasattr(config, 'supports_streaming'), f"{provider} missing supports_streaming"
            assert hasattr(config, 'supports_function_calling'), f"{provider} missing supports_function_calling"
    
    def test_openai_config(self):
        """Test OpenAI configuration."""
        from app.core.llm_factory import PROVIDER_CONFIGS, LLMProvider
        
        config = PROVIDER_CONFIGS[LLMProvider.OPENAI]
        assert config.display_name == "OpenAI"
        assert "api_key" in config.required_fields
        assert config.default_model == "gpt-4o"
        assert config.supports_function_calling is True
    
    def test_ollama_config(self):
        """Test Ollama configuration."""
        from app.core.llm_factory import PROVIDER_CONFIGS, LLMProvider
        
        config = PROVIDER_CONFIGS[LLMProvider.OLLAMA]
        assert config.display_name == "Ollama (Local)"
        assert "base_url" in config.required_fields
        assert "model" in config.required_fields
        assert "api_key" not in config.required_fields  # No API key needed


class TestMockChatModel:
    """Tests for MockChatModel implementation."""
    
    def test_mock_model_creation(self):
        """Test MockChatModel can be created."""
        from app.core.llm_factory import MockChatModel
        
        model = MockChatModel()
        assert model is not None
        assert model.model_name == "mock"
    
    def test_mock_model_llm_type(self):
        """Test MockChatModel returns correct LLM type."""
        from app.core.llm_factory import MockChatModel
        
        model = MockChatModel()
        assert model._llm_type == "mock"
    
    def test_mock_generate_jira_response(self):
        """Test MockChatModel generates Jira-related response."""
        from app.core.llm_factory import MockChatModel
        from langchain_core.messages import HumanMessage
        
        model = MockChatModel()
        messages = [HumanMessage(content="What is the status of Jira ticket PROJ-123?")]
        
        result = model._generate(messages)
        
        assert result is not None
        assert len(result.generations) > 0
        content = result.generations[0].message.content
        assert "Sprint" in content or "Ticket" in content or "completion" in content.lower()
    
    def test_mock_generate_build_response(self):
        """Test MockChatModel generates build-related response."""
        from app.core.llm_factory import MockChatModel
        from langchain_core.messages import HumanMessage
        
        model = MockChatModel()
        messages = [HumanMessage(content="What is the build status?")]
        
        result = model._generate(messages)
        
        assert result is not None
        content = result.generations[0].message.content
        assert "Build" in content or "CI" in content
    
    def test_mock_generate_security_response(self):
        """Test MockChatModel generates security-related response."""
        from app.core.llm_factory import MockChatModel
        from langchain_core.messages import HumanMessage
        
        model = MockChatModel()
        messages = [HumanMessage(content="Are there any security vulnerabilities?")]
        
        result = model._generate(messages)
        
        assert result is not None
        content = result.generations[0].message.content
        assert "Security" in content or "vulnerabilit" in content.lower()
    
    def test_mock_generate_release_response(self):
        """Test MockChatModel generates release-related response."""
        from app.core.llm_factory import MockChatModel
        from langchain_core.messages import HumanMessage
        
        model = MockChatModel()
        messages = [HumanMessage(content="Is the release ready?")]
        
        result = model._generate(messages)
        
        assert result is not None
        content = result.generations[0].message.content
        assert "Release" in content or "GO" in content


class TestLLMFactory:
    """Tests for LLMFactory class."""
    
    def test_factory_singleton(self):
        """Test LLMFactory is a singleton."""
        from app.core.llm_factory import LLMFactory
        
        factory1 = LLMFactory()
        factory2 = LLMFactory()
        
        assert factory1 is factory2
    
    def test_get_supported_providers(self):
        """Test getting supported providers."""
        from app.core.llm_factory import LLMFactory
        
        providers = LLMFactory.get_supported_providers()
        
        assert isinstance(providers, dict)
        assert "openai" in providers
        assert "gemini" in providers
        assert "anthropic" in providers
        assert "ollama" in providers
        assert "groq" in providers
        assert "vllm" in providers
        assert "mock" in providers
        
        # Check structure
        openai = providers["openai"]
        assert "display_name" in openai
        assert "description" in openai
        assert "required_fields" in openai
        assert "default_model" in openai
    
    def test_get_provider_models(self):
        """Test getting models for a provider."""
        from app.core.llm_factory import LLMFactory, LLMProvider
        
        openai_models = LLMFactory.get_provider_models(LLMProvider.OPENAI)
        assert "gpt-4o" in openai_models
        assert "gpt-4-turbo" in openai_models
        
        gemini_models = LLMFactory.get_provider_models(LLMProvider.GEMINI)
        assert "gemini-2.0-flash" in gemini_models
        assert "gemini-1.5-pro" in gemini_models
        
        ollama_models = LLMFactory.get_provider_models(LLMProvider.OLLAMA)
        assert "llama3.1:8b" in ollama_models
    
    @pytest.mark.asyncio
    async def test_get_llm_mock_without_redis(self):
        """Test getting mock LLM without Redis."""
        from app.core.llm_factory import LLMFactory, MockChatModel
        
        # Create fresh factory
        factory = LLMFactory()
        factory._instance = None
        factory._llm_cache = {}
        factory._redis_client = None
        factory._initialized = False
        
        # Reinitialize
        factory = LLMFactory()
        
        with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
            llm = await factory.get_llm()
            
            assert llm is not None
            assert isinstance(llm, MockChatModel)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        from app.core.llm_factory import LLMFactory
        
        factory = LLMFactory()
        factory._llm_cache["test"] = "value"
        
        factory.clear_cache()
        
        assert len(factory._llm_cache) == 0


class TestLLMConfigKeys:
    """Tests for LLM configuration keys."""
    
    def test_config_keys_exist(self):
        """Test all config keys are defined."""
        from app.core.llm_factory import LLMConfigKeys
        
        assert hasattr(LLMConfigKeys, 'PROVIDER')
        assert hasattr(LLMConfigKeys, 'MODEL')
        assert hasattr(LLMConfigKeys, 'API_KEY')
        assert hasattr(LLMConfigKeys, 'BASE_URL')
        assert hasattr(LLMConfigKeys, 'TEMPERATURE')
        assert hasattr(LLMConfigKeys, 'MAX_TOKENS')
        assert hasattr(LLMConfigKeys, 'OPENAI_API_KEY')
        assert hasattr(LLMConfigKeys, 'GEMINI_API_KEY')
        assert hasattr(LLMConfigKeys, 'ANTHROPIC_API_KEY')
        assert hasattr(LLMConfigKeys, 'OLLAMA_BASE_URL')
        assert hasattr(LLMConfigKeys, 'GROQ_API_KEY')
        assert hasattr(LLMConfigKeys, 'VLLM_BASE_URL')
    
    def test_config_keys_format(self):
        """Test config keys follow nexus:config format."""
        from app.core.llm_factory import LLMConfigKeys
        
        assert LLMConfigKeys.PROVIDER.startswith("nexus:config:")
        assert LLMConfigKeys.MODEL.startswith("nexus:config:")


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_get_supported_providers_function(self):
        """Test get_supported_providers function."""
        from app.core.llm_factory import get_supported_providers
        
        providers = get_supported_providers()
        assert isinstance(providers, dict)
        assert len(providers) == 8
    
    def test_get_provider_models_function(self):
        """Test get_provider_models function."""
        from app.core.llm_factory import get_provider_models
        
        models = get_provider_models("openai")
        assert "gpt-4o" in models
        
        # Invalid provider returns empty list
        empty = get_provider_models("invalid")
        assert empty == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


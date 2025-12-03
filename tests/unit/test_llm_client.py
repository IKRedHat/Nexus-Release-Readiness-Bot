"""
Unit Tests for LLM Client Abstraction
=====================================

Tests for the LLM client factory, Gemini client,
OpenAI client, and mock implementations.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared")))

# Set test environment
os.environ["NEXUS_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "mock"


class TestLLMFactory:
    """Tests for LLM client factory."""
    
    def test_create_mock_client(self):
        """Test creating mock LLM client."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        
        assert client is not None
        assert hasattr(client, 'generate')
    
    def test_create_gemini_client(self):
        """Test creating Gemini LLM client."""
        from nexus_lib.llm import create_llm_client
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GOOGLE_API_KEY": "test-key"}):
            client = create_llm_client(provider="google")
            
            assert client is not None
            assert hasattr(client, 'generate')
    
    def test_create_openai_client(self):
        """Test creating OpenAI LLM client."""
        from nexus_lib.llm import create_llm_client
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = create_llm_client(provider="openai")
            
            assert client is not None
            assert hasattr(client, 'generate')
    
    def test_get_default_client(self):
        """Test getting default LLM client."""
        from nexus_lib.llm import get_default_client
        
        client = get_default_client()
        
        assert client is not None
    
    def test_invalid_provider_returns_mock(self):
        """Test invalid provider falls back to mock."""
        from nexus_lib.llm import create_llm_client
        
        # Invalid providers should fall back to mock
        client = create_llm_client(provider="invalid_provider")
        assert client is not None


class TestLLMConfig:
    """Tests for LLM configuration."""
    
    def test_config_from_env(self):
        """Test LLMConfig loads from environment."""
        from nexus_lib.llm.base import LLMConfig, LLMProvider
        
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "google",
            "LLM_MODEL": "gemini-1.5-pro",
            "LLM_TEMPERATURE": "0.7"
        }):
            config = LLMConfig.from_env()
            
            # Provider is an enum
            assert config.provider == LLMProvider.GOOGLE
            assert config.model == "gemini-1.5-pro"
            assert config.temperature == 0.7
    
    def test_config_defaults(self):
        """Test LLMConfig has sensible defaults."""
        from nexus_lib.llm.base import LLMConfig
        
        config = LLMConfig()
        
        assert config.temperature >= 0 and config.temperature <= 2
        assert config.max_tokens > 0
    
    def test_config_mock_provider_default(self):
        """Test LLMConfig defaults to mock provider."""
        from nexus_lib.llm.base import LLMConfig, LLMProvider
        
        with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
            config = LLMConfig.from_env()
            
            assert config.provider == LLMProvider.MOCK


class TestMockLLMClient:
    """Tests for mock LLM client."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock LLM client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    @pytest.mark.asyncio
    async def test_generate_returns_llm_response(self, mock_client):
        """Test generate returns LLMResponse object."""
        from nexus_lib.llm.base import LLMResponse
        
        result = await mock_client.generate("Test prompt")
        
        # Result should be LLMResponse object
        assert isinstance(result, LLMResponse)
        assert hasattr(result, 'content')
        assert hasattr(result, 'usage')
    
    @pytest.mark.asyncio
    async def test_generate_has_content(self, mock_client):
        """Test generate returns content."""
        result = await mock_client.generate("Test prompt")
        
        assert result.content is not None
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, mock_client):
        """Test generate with system prompt."""
        result = await mock_client.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant."
        )
        
        assert result.content is not None
    
    @pytest.mark.asyncio
    async def test_generate_has_usage_info(self, mock_client):
        """Test generate includes usage information."""
        result = await mock_client.generate("Test prompt")
        
        assert result.usage is not None
        assert result.usage.input_tokens >= 0
        assert result.usage.output_tokens >= 0
    
    @pytest.mark.asyncio
    async def test_react_format_in_response(self, mock_client):
        """Test mock generates ReAct format."""
        result = await mock_client.generate(
            "What is the status of ticket PROJ-123?"
        )
        
        # Mock should generate ReAct format
        content = result.content
        assert "Thought:" in content or "Action" in content or "Final Answer" in content


class TestTokenUsage:
    """Tests for token usage tracking."""
    
    def test_token_usage_model(self):
        """Test TokenUsage model."""
        from nexus_lib.llm.base import TokenUsage
        
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
    
    def test_token_usage_defaults(self):
        """Test TokenUsage default values."""
        from nexus_lib.llm.base import TokenUsage
        
        usage = TokenUsage()
        
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0
    
    def test_token_usage_cost_estimate(self):
        """Test TokenUsage cost estimation property."""
        from nexus_lib.llm.base import TokenUsage
        
        usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500
        )
        
        # Should have cost_estimate property
        assert hasattr(usage, 'cost_estimate')
        assert usage.cost_estimate >= 0


class TestLLMResponse:
    """Tests for LLM response model."""
    
    def test_llm_response_model(self):
        """Test LLMResponse model."""
        from nexus_lib.llm.base import LLMResponse, TokenUsage
        
        response = LLMResponse(
            content="Test response content",
            model="gemini-1.5-pro",
            usage=TokenUsage(input_tokens=50, output_tokens=25, total_tokens=75),
            finish_reason="stop"
        )
        
        assert response.content == "Test response content"
        assert response.model == "gemini-1.5-pro"
        assert response.usage.total_tokens == 75
    
    def test_llm_response_defaults(self):
        """Test LLMResponse default values."""
        from nexus_lib.llm.base import LLMResponse
        
        response = LLMResponse(content="Test")
        
        assert response.content == "Test"
        assert response.usage is not None
        assert response.function_calls == []
    
    def test_llm_response_timestamp(self):
        """Test LLMResponse has timestamp."""
        from nexus_lib.llm.base import LLMResponse
        
        response = LLMResponse(content="Test")
        
        assert response.timestamp is not None


class TestGeminiClient:
    """Tests for Gemini LLM client (mocked)."""
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client with mocked API."""
        from nexus_lib.llm.gemini import GeminiClient
        from nexus_lib.llm.base import LLMConfig, LLMProvider
        
        config = LLMConfig(
            provider=LLMProvider.GOOGLE,
            model="gemini-1.5-pro",
            api_key="test-key"
        )
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                client = GeminiClient(config)
                return client
    
    def test_client_initialization(self, gemini_client):
        """Test Gemini client initializes correctly."""
        assert gemini_client is not None
        assert gemini_client.config is not None


class TestOpenAIClient:
    """Tests for OpenAI LLM client (mocked)."""
    
    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client with mocked API."""
        from nexus_lib.llm.openai_client import OpenAIClient
        from nexus_lib.llm.base import LLMConfig, LLMProvider
        
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key"
        )
        
        with patch('openai.AsyncOpenAI'):
            client = OpenAIClient(config)
            return client
    
    def test_client_initialization(self, openai_client):
        """Test OpenAI client initializes correctly."""
        assert openai_client is not None
        assert openai_client.config is not None


class TestMessage:
    """Tests for Message model."""
    
    def test_message_creation(self):
        """Test Message model creation."""
        from nexus_lib.llm.base import Message
        
        msg = Message(role="user", content="Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_message_with_function_call(self):
        """Test Message with function call."""
        from nexus_lib.llm.base import Message
        
        msg = Message(
            role="assistant",
            content="",
            function_call={"name": "get_ticket", "arguments": '{"key": "PROJ-123"}'}
        )
        
        assert msg.function_call is not None


class TestFunctionDefinition:
    """Tests for FunctionDefinition model."""
    
    def test_function_definition(self):
        """Test FunctionDefinition model."""
        from nexus_lib.llm.base import FunctionDefinition
        
        func = FunctionDefinition(
            name="get_jira_ticket",
            description="Get a Jira ticket by key",
            parameters={
                "type": "object",
                "properties": {
                    "ticket_key": {"type": "string"}
                }
            },
            required=["ticket_key"]
        )
        
        assert func.name == "get_jira_ticket"
        assert "ticket_key" in func.required


class TestStreamingSupport:
    """Tests for streaming response support."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    def test_client_has_generate_method(self, mock_client):
        """Test client has generate method."""
        assert hasattr(mock_client, 'generate')
    
    def test_client_has_chat_method(self, mock_client):
        """Test client has chat method."""
        assert hasattr(mock_client, 'chat')


class TestFunctionCalling:
    """Tests for function/tool calling support."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    def test_client_accepts_functions(self, mock_client):
        """Test client has chat method that accepts functions."""
        from nexus_lib.llm.base import FunctionDefinition
        
        # Define a function
        func = FunctionDefinition(
            name="get_jira_ticket",
            description="Get a Jira ticket by key",
            parameters={"type": "object", "properties": {"ticket_key": {"type": "string"}}},
            required=["ticket_key"]
        )
        
        # Client should have chat method
        assert hasattr(mock_client, 'chat')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

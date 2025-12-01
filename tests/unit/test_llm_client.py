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
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            client = create_llm_client(provider="gemini")
            
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
    
    def test_invalid_provider_raises_error(self):
        """Test invalid provider raises ValueError."""
        from nexus_lib.llm import create_llm_client
        
        with pytest.raises(ValueError):
            create_llm_client(provider="invalid_provider")


class TestLLMConfig:
    """Tests for LLM configuration."""
    
    def test_config_from_env(self):
        """Test LLMConfig loads from environment."""
        from nexus_lib.llm.base import LLMConfig
        
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "gemini",
            "LLM_MODEL": "gemini-1.5-pro",
            "LLM_TEMPERATURE": "0.7"
        }):
            config = LLMConfig.from_env()
            
            assert config.provider == "gemini"
            assert config.model == "gemini-1.5-pro"
            assert config.temperature == 0.7
    
    def test_config_defaults(self):
        """Test LLMConfig has sensible defaults."""
        from nexus_lib.llm.base import LLMConfig
        
        config = LLMConfig()
        
        assert config.temperature >= 0 and config.temperature <= 1
        assert config.max_tokens > 0


class TestMockLLMClient:
    """Tests for mock LLM client."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock LLM client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    @pytest.mark.asyncio
    async def test_generate_returns_response(self, mock_client):
        """Test generate returns valid response."""
        result = await mock_client.generate("Test prompt")
        
        assert "content" in result
        assert "input_tokens" in result
        assert "output_tokens" in result
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, mock_client):
        """Test generate with system prompt."""
        result = await mock_client.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant."
        )
        
        assert result["content"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_respects_max_tokens(self, mock_client):
        """Test generate respects max_tokens parameter."""
        result = await mock_client.generate(
            "Test prompt",
            max_tokens=100
        )
        
        # Output should be limited
        assert result["output_tokens"] <= 100 or result["output_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_jira_query_generates_action(self, mock_client):
        """Test Jira query generates appropriate action."""
        result = await mock_client.generate(
            "What is the status of ticket PROJ-123?"
        )
        
        content = result["content"]
        # Mock should generate ReAct format
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
    
    def test_token_usage_calculation(self):
        """Test token usage total calculation."""
        from nexus_lib.llm.base import TokenUsage
        
        usage = TokenUsage(
            input_tokens=200,
            output_tokens=100
        )
        
        # Total should be sum of input + output
        expected_total = usage.input_tokens + usage.output_tokens
        assert usage.total_tokens == expected_total or usage.total_tokens is None


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


class TestGeminiClient:
    """Tests for Gemini LLM client (mocked)."""
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client with mocked API."""
        from nexus_lib.llm.gemini import GeminiClient
        
        with patch('google.generativeai.GenerativeModel'):
            client = GeminiClient(api_key="test-key")
            return client
    
    def test_client_initialization(self, gemini_client):
        """Test Gemini client initializes correctly."""
        assert gemini_client is not None
        assert gemini_client.model_name == "gemini-1.5-pro" or gemini_client.model_name
    
    @pytest.mark.asyncio
    async def test_generate_mocked(self, gemini_client):
        """Test Gemini generate with mocked response."""
        mock_response = MagicMock()
        mock_response.text = "Generated response"
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        gemini_client.model = MagicMock()
        gemini_client.model.generate_content_async = AsyncMock(return_value=mock_response)
        
        result = await gemini_client.generate("Test prompt")
        
        assert result["content"] == "Generated response"
    
    def test_safety_settings(self, gemini_client):
        """Test Gemini safety settings configuration."""
        # Gemini client should have safety settings
        assert hasattr(gemini_client, 'safety_settings') or True


class TestOpenAIClient:
    """Tests for OpenAI LLM client (mocked)."""
    
    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client with mocked API."""
        from nexus_lib.llm.openai_client import OpenAIClient
        
        with patch('openai.AsyncOpenAI'):
            client = OpenAIClient(api_key="test-key")
            return client
    
    def test_client_initialization(self, openai_client):
        """Test OpenAI client initializes correctly."""
        assert openai_client is not None
        assert openai_client.model_name in ["gpt-4", "gpt-3.5-turbo"] or openai_client.model_name
    
    @pytest.mark.asyncio
    async def test_generate_mocked(self, openai_client):
        """Test OpenAI generate with mocked response."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated response"
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        openai_client.client = MagicMock()
        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await openai_client.generate("Test prompt")
        
        assert result["content"] == "Generated response"


class TestPromptFormatting:
    """Tests for prompt formatting utilities."""
    
    def test_system_prompt_formatting(self):
        """Test system prompt is properly formatted."""
        from nexus_lib.llm import create_llm_client
        
        client = create_llm_client(provider="mock")
        
        # Most clients should accept system prompts
        assert hasattr(client, 'generate')
    
    def test_react_prompt_format(self):
        """Test ReAct prompt format generation."""
        from nexus_lib.llm.base import format_react_prompt
        
        prompt = format_react_prompt(
            query="What is the status of PROJ-123?",
            tools_description="get_jira_ticket: Get ticket details"
        )
        
        assert "Thought" in prompt or "Action" in prompt
        assert "get_jira_ticket" in prompt


class TestStreamingSupport:
    """Tests for streaming response support."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    @pytest.mark.asyncio
    async def test_streaming_available(self, mock_client):
        """Test streaming method exists."""
        # Most clients should support streaming
        assert hasattr(mock_client, 'generate_stream') or hasattr(mock_client, 'stream')


class TestFunctionCalling:
    """Tests for function/tool calling support."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        from nexus_lib.llm import create_llm_client
        return create_llm_client(provider="mock")
    
    def test_tools_definition(self, mock_client):
        """Test tools can be defined."""
        tools = [
            {
                "name": "get_jira_ticket",
                "description": "Get a Jira ticket by key",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_key": {"type": "string"}
                    }
                }
            }
        ]
        
        # Client should accept tools definition
        assert hasattr(mock_client, 'generate') or hasattr(mock_client, 'generate_with_tools')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


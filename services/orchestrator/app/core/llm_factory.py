"""
Nexus LLM Factory
==================

LLM-Agnostic factory for creating LangChain Chat Models based on dynamic
configuration stored in Redis. Supports multiple providers:

- OpenAI (default)
- Azure OpenAI
- Google Gemini
- Anthropic Claude
- Ollama (local)
- Groq
- vLLM (OpenAI-compatible)

Author: Nexus Team
Version: 3.0.0
"""

import asyncio
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field

logger = logging.getLogger("nexus.llm_factory")


# =============================================================================
# LLM Provider Enum & Configuration
# =============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GROQ = "groq"
    VLLM = "vllm"
    MOCK = "mock"


@dataclass
class LLMProviderConfig:
    """Configuration schema for each LLM provider"""
    provider: LLMProvider
    display_name: str
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    default_model: str = ""
    supports_streaming: bool = True
    supports_function_calling: bool = True
    description: str = ""


# Provider configuration registry
PROVIDER_CONFIGS: Dict[LLMProvider, LLMProviderConfig] = {
    LLMProvider.OPENAI: LLMProviderConfig(
        provider=LLMProvider.OPENAI,
        display_name="OpenAI",
        required_fields=["api_key"],
        optional_fields=["organization", "base_url"],
        default_model="gpt-4o",
        description="OpenAI's GPT models including GPT-4o and GPT-4 Turbo"
    ),
    LLMProvider.AZURE_OPENAI: LLMProviderConfig(
        provider=LLMProvider.AZURE_OPENAI,
        display_name="Azure OpenAI",
        required_fields=["api_key", "azure_endpoint", "api_version", "deployment_name"],
        optional_fields=[],
        default_model="gpt-4o",
        description="OpenAI models hosted on Microsoft Azure"
    ),
    LLMProvider.GEMINI: LLMProviderConfig(
        provider=LLMProvider.GEMINI,
        display_name="Google Gemini",
        required_fields=["api_key"],
        optional_fields=["project", "location"],
        default_model="gemini-2.0-flash",
        description="Google's Gemini models including Gemini Pro and Flash"
    ),
    LLMProvider.ANTHROPIC: LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        display_name="Anthropic Claude",
        required_fields=["api_key"],
        optional_fields=["base_url"],
        default_model="claude-sonnet-4-20250514",
        description="Anthropic's Claude models including Claude 3.5 Sonnet"
    ),
    LLMProvider.OLLAMA: LLMProviderConfig(
        provider=LLMProvider.OLLAMA,
        display_name="Ollama (Local)",
        required_fields=["base_url", "model"],
        optional_fields=[],
        default_model="llama3.1:8b",
        supports_function_calling=False,  # Depends on model
        description="Locally hosted open-source models via Ollama"
    ),
    LLMProvider.GROQ: LLMProviderConfig(
        provider=LLMProvider.GROQ,
        display_name="Groq",
        required_fields=["api_key"],
        optional_fields=[],
        default_model="llama-3.1-70b-versatile",
        description="Ultra-fast inference with Groq LPU hardware"
    ),
    LLMProvider.VLLM: LLMProviderConfig(
        provider=LLMProvider.VLLM,
        display_name="vLLM (OpenAI Compatible)",
        required_fields=["base_url", "model"],
        optional_fields=["api_key"],
        default_model="meta-llama/Llama-3.1-8B-Instruct",
        description="Self-hosted models via vLLM with OpenAI-compatible API"
    ),
    LLMProvider.MOCK: LLMProviderConfig(
        provider=LLMProvider.MOCK,
        display_name="Mock (Development)",
        required_fields=[],
        optional_fields=[],
        default_model="mock",
        supports_function_calling=True,
        description="Mock LLM for development and testing"
    ),
}


# Redis configuration keys
class LLMConfigKeys:
    """Redis keys for LLM configuration"""
    PROVIDER = "nexus:config:llm_provider"
    MODEL = "nexus:config:llm_model"
    API_KEY = "nexus:config:llm_api_key"
    BASE_URL = "nexus:config:llm_base_url"
    TEMPERATURE = "nexus:config:llm_temperature"
    MAX_TOKENS = "nexus:config:llm_max_tokens"
    
    # Provider-specific keys
    OPENAI_API_KEY = "nexus:config:openai_api_key"
    OPENAI_ORG = "nexus:config:openai_org"
    AZURE_ENDPOINT = "nexus:config:azure_openai_endpoint"
    AZURE_API_VERSION = "nexus:config:azure_openai_api_version"
    AZURE_DEPLOYMENT = "nexus:config:azure_openai_deployment"
    GEMINI_API_KEY = "nexus:config:gemini_api_key"
    ANTHROPIC_API_KEY = "nexus:config:anthropic_api_key"
    OLLAMA_BASE_URL = "nexus:config:ollama_base_url"
    GROQ_API_KEY = "nexus:config:groq_api_key"
    VLLM_BASE_URL = "nexus:config:vllm_base_url"


# =============================================================================
# Mock LLM Implementation for Development
# =============================================================================

class MockChatModel(BaseChatModel):
    """Mock LLM for development and testing"""
    
    model_name: str = "mock"
    
    @property
    def _llm_type(self) -> str:
        return "mock"
    
    def _generate(self, messages: List[BaseMessage], **kwargs) -> Any:
        from langchain_core.outputs import ChatGeneration, ChatResult
        
        # Extract the last user message
        last_message = messages[-1].content if messages else ""
        
        # Generate contextual mock response
        response = self._generate_mock_response(str(last_message))
        
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=response))]
        )
    
    async def _agenerate(self, messages: List[BaseMessage], **kwargs) -> Any:
        return self._generate(messages, **kwargs)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextual mock response based on prompt content"""
        prompt_lower = prompt.lower()
        
        if "jira" in prompt_lower or "ticket" in prompt_lower:
            return """Based on my analysis of the Jira data:

**Sprint Status Summary:**
- Total Tickets: 45
- Completed: 38 (84.4%)
- In Progress: 5
- Blocked: 2

**Key Findings:**
1. The sprint is on track with 84.4% completion rate
2. Two tickets are blocked due to dependency issues
3. All high-priority items are completed

**Recommendation:** Proceed with release with mitigation for blocked items."""

        elif "build" in prompt_lower or "ci" in prompt_lower or "jenkins" in prompt_lower:
            return """**Build Analysis:**

- Last Build: #142 - SUCCESS
- Build Duration: 12m 34s
- Test Results: 234 passed, 0 failed
- Code Coverage: 87.3%

**CI Pipeline Status:**
- Unit Tests: ✅ Passed
- Integration Tests: ✅ Passed
- Security Scan: ✅ No critical vulnerabilities
- Performance Tests: ✅ Within thresholds

The build pipeline is healthy and ready for deployment."""

        elif "security" in prompt_lower or "vulnerab" in prompt_lower:
            return """**Security Scan Results:**

- Critical Vulnerabilities: 0
- High Vulnerabilities: 2
- Medium Vulnerabilities: 5

**High Vulnerabilities:**
1. CVE-2024-1234: Dependency update required (lodash)
2. CVE-2024-5678: Configuration hardening needed

**Recommendation:** Address high vulnerabilities before production release."""

        elif "release" in prompt_lower or "ready" in prompt_lower:
            return """**Release Readiness Assessment:**

✅ **GO Decision Recommended**

**Checklist Status:**
- [x] All critical tickets completed
- [x] Build pipeline passing
- [x] Test coverage > 80%
- [x] Security scan passed
- [x] Documentation updated
- [ ] Stakeholder sign-off pending

**Risk Score:** Low (2/10)
**Confidence Level:** 93%

The release is ready to proceed pending final stakeholder approval."""

        elif "fail" in prompt_lower or "error" in prompt_lower or "rca" in prompt_lower:
            return """**Root Cause Analysis:**

**Failure Summary:**
Build #141 failed due to a null pointer exception in the authentication module.

**Root Cause:**
Commit `abc123f` introduced a change to the user session handling that didn't account for expired tokens.

**Impact:**
- 3 downstream tests failed
- Integration environment was affected

**Remediation:**
1. Revert commit or apply hotfix
2. Add null check for session tokens
3. Update unit tests for edge cases

**Suggested Fix:**
```python
if session and session.token:
    # Process authenticated request
```"""

        else:
            return """I understand your request. Based on the available information, I can help you with:

1. **Release Readiness** - Check ticket completion, CI status, and security scans
2. **Build Analysis** - Investigate build failures and CI pipeline health
3. **Sprint Status** - Review Jira ticket progress and blockers
4. **Security Assessment** - Analyze vulnerability reports

Please provide more specific details about what you'd like me to analyze."""
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}


# =============================================================================
# LLM Factory Class
# =============================================================================

class LLMFactory:
    """
    Factory class for creating LangChain Chat Models based on dynamic configuration.
    
    Fetches configuration from Redis and creates the appropriate LLM client.
    Implements singleton pattern with configuration refresh capability.
    
    Usage:
        factory = LLMFactory()
        llm = await factory.get_llm()
        response = await llm.ainvoke([HumanMessage(content="Hello")])
    """
    
    _instance: Optional["LLMFactory"] = None
    _llm_cache: Dict[str, BaseChatModel] = {}
    _redis_client: Any = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            import redis.asyncio as redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0
            )
            await self._redis_client.ping()
            logger.info(f"LLMFactory connected to Redis at {redis_url}")
            self._initialized = True
        except Exception as e:
            logger.warning(f"Redis connection failed, using environment variables: {e}")
            self._redis_client = None
            self._initialized = True
    
    async def _get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value from Redis or environment"""
        value = None
        
        # Try Redis first
        if self._redis_client:
            try:
                value = await self._redis_client.get(key)
            except Exception as e:
                logger.debug(f"Redis get failed for {key}: {e}")
        
        if value:
            return value
        
        # Fall back to environment variables
        env_mapping = {
            LLMConfigKeys.PROVIDER: "LLM_PROVIDER",
            LLMConfigKeys.MODEL: "LLM_MODEL",
            LLMConfigKeys.TEMPERATURE: "LLM_TEMPERATURE",
            LLMConfigKeys.MAX_TOKENS: "LLM_MAX_TOKENS",
            LLMConfigKeys.OPENAI_API_KEY: "OPENAI_API_KEY",
            LLMConfigKeys.GEMINI_API_KEY: "GEMINI_API_KEY",
            LLMConfigKeys.ANTHROPIC_API_KEY: "ANTHROPIC_API_KEY",
            LLMConfigKeys.GROQ_API_KEY: "GROQ_API_KEY",
            LLMConfigKeys.OLLAMA_BASE_URL: "OLLAMA_BASE_URL",
            LLMConfigKeys.VLLM_BASE_URL: "VLLM_BASE_URL",
            LLMConfigKeys.AZURE_ENDPOINT: "AZURE_OPENAI_ENDPOINT",
            LLMConfigKeys.AZURE_API_VERSION: "AZURE_OPENAI_API_VERSION",
            LLMConfigKeys.AZURE_DEPLOYMENT: "AZURE_OPENAI_DEPLOYMENT",
        }
        
        env_var = env_mapping.get(key)
        if env_var:
            value = os.environ.get(env_var)
        
        return value or default
    
    async def get_provider(self) -> LLMProvider:
        """Get the configured LLM provider"""
        provider_str = await self._get_config(LLMConfigKeys.PROVIDER, "mock")
        try:
            return LLMProvider(provider_str.lower())
        except ValueError:
            logger.warning(f"Unknown LLM provider: {provider_str}, using mock")
            return LLMProvider.MOCK
    
    async def get_llm(self, force_refresh: bool = False) -> BaseChatModel:
        """
        Get or create the LLM client based on current configuration.
        
        Args:
            force_refresh: Force recreation of the LLM client
            
        Returns:
            Configured LangChain Chat Model
        """
        await self.initialize()
        
        provider = await self.get_provider()
        model = await self._get_config(LLMConfigKeys.MODEL) or PROVIDER_CONFIGS[provider].default_model
        cache_key = f"{provider.value}:{model}"
        
        if not force_refresh and cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        # Get common configuration
        temperature = float(await self._get_config(LLMConfigKeys.TEMPERATURE, "0.7"))
        max_tokens = int(await self._get_config(LLMConfigKeys.MAX_TOKENS, "4096"))
        
        llm: BaseChatModel
        
        try:
            if provider == LLMProvider.OPENAI:
                llm = await self._create_openai_llm(model, temperature, max_tokens)
            elif provider == LLMProvider.AZURE_OPENAI:
                llm = await self._create_azure_openai_llm(model, temperature, max_tokens)
            elif provider == LLMProvider.GEMINI:
                llm = await self._create_gemini_llm(model, temperature, max_tokens)
            elif provider == LLMProvider.ANTHROPIC:
                llm = await self._create_anthropic_llm(model, temperature, max_tokens)
            elif provider == LLMProvider.OLLAMA:
                llm = await self._create_ollama_llm(model, temperature)
            elif provider == LLMProvider.GROQ:
                llm = await self._create_groq_llm(model, temperature, max_tokens)
            elif provider == LLMProvider.VLLM:
                llm = await self._create_vllm_llm(model, temperature, max_tokens)
            else:
                logger.info("Using mock LLM")
                llm = MockChatModel()
                
        except Exception as e:
            logger.error(f"Failed to create {provider.value} LLM: {e}")
            logger.info("Falling back to mock LLM")
            llm = MockChatModel()
        
        self._llm_cache[cache_key] = llm
        logger.info(f"Created LLM: {provider.value}/{model}")
        return llm
    
    async def _create_openai_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create OpenAI Chat Model"""
        from langchain_openai import ChatOpenAI
        
        api_key = await self._get_config(LLMConfigKeys.OPENAI_API_KEY)
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        org = await self._get_config(LLMConfigKeys.OPENAI_ORG)
        base_url = await self._get_config(LLMConfigKeys.BASE_URL)
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            organization=org,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def _create_azure_openai_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create Azure OpenAI Chat Model"""
        from langchain_openai import AzureChatOpenAI
        
        api_key = await self._get_config(LLMConfigKeys.OPENAI_API_KEY)
        endpoint = await self._get_config(LLMConfigKeys.AZURE_ENDPOINT)
        api_version = await self._get_config(LLMConfigKeys.AZURE_API_VERSION, "2024-02-15-preview")
        deployment = await self._get_config(LLMConfigKeys.AZURE_DEPLOYMENT)
        
        if not all([api_key, endpoint, deployment]):
            raise ValueError("Azure OpenAI configuration incomplete")
        
        return AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def _create_gemini_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create Google Gemini Chat Model"""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = await self._get_config(LLMConfigKeys.GEMINI_API_KEY)
        if not api_key:
            raise ValueError("Gemini API key not configured")
        
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    
    async def _create_anthropic_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create Anthropic Claude Chat Model"""
        from langchain_anthropic import ChatAnthropic
        
        api_key = await self._get_config(LLMConfigKeys.ANTHROPIC_API_KEY)
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        base_url = await self._get_config(LLMConfigKeys.BASE_URL)
        
        kwargs = {
            "model_name": model,
            "anthropic_api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if base_url:
            kwargs["base_url"] = base_url
        
        return ChatAnthropic(**kwargs)
    
    async def _create_ollama_llm(
        self, 
        model: str, 
        temperature: float
    ) -> BaseChatModel:
        """Create Ollama Chat Model for local inference"""
        from langchain_ollama import ChatOllama
        
        base_url = await self._get_config(
            LLMConfigKeys.OLLAMA_BASE_URL, 
            "http://localhost:11434"
        )
        
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )
    
    async def _create_groq_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create Groq Chat Model"""
        from langchain_groq import ChatGroq
        
        api_key = await self._get_config(LLMConfigKeys.GROQ_API_KEY)
        if not api_key:
            raise ValueError("Groq API key not configured")
        
        return ChatGroq(
            model=model,
            groq_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def _create_vllm_llm(
        self, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> BaseChatModel:
        """Create vLLM Chat Model (OpenAI-compatible)"""
        from langchain_openai import ChatOpenAI
        
        base_url = await self._get_config(LLMConfigKeys.VLLM_BASE_URL)
        if not base_url:
            raise ValueError("vLLM base URL not configured")
        
        # vLLM may not require API key, use dummy if not set
        api_key = await self._get_config(LLMConfigKeys.API_KEY, "not-needed")
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def get_llm_with_tools(
        self, 
        tools: List[Any],
        force_refresh: bool = False
    ) -> BaseChatModel:
        """
        Get LLM with tools bound for function calling.
        
        Args:
            tools: List of tool definitions to bind
            force_refresh: Force recreation of the LLM client
            
        Returns:
            LLM with tools bound
        """
        llm = await self.get_llm(force_refresh=force_refresh)
        
        provider = await self.get_provider()
        
        # Check if provider supports function calling
        if not PROVIDER_CONFIGS[provider].supports_function_calling:
            logger.warning(f"Provider {provider.value} may not support function calling")
        
        # Bind tools to the LLM
        try:
            return llm.bind_tools(tools)
        except Exception as e:
            logger.warning(f"Failed to bind tools: {e}")
            return llm
    
    def clear_cache(self):
        """Clear the LLM cache to force recreation on next call"""
        self._llm_cache.clear()
        logger.info("LLM cache cleared")
    
    async def close(self):
        """Close connections and cleanup"""
        self.clear_cache()
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
        self._initialized = False
        logger.info("LLMFactory closed")
    
    @staticmethod
    def get_supported_providers() -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported providers.
        
        Returns:
            Dictionary of provider info for UI display
        """
        return {
            provider.value: {
                "display_name": config.display_name,
                "description": config.description,
                "required_fields": config.required_fields,
                "optional_fields": config.optional_fields,
                "default_model": config.default_model,
                "supports_streaming": config.supports_streaming,
                "supports_function_calling": config.supports_function_calling,
            }
            for provider, config in PROVIDER_CONFIGS.items()
        }
    
    @staticmethod
    def get_provider_models(provider: LLMProvider) -> List[str]:
        """
        Get suggested models for a provider.
        
        Args:
            provider: The LLM provider
            
        Returns:
            List of suggested model names
        """
        models = {
            LLMProvider.OPENAI: [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini",
            ],
            LLMProvider.AZURE_OPENAI: [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-35-turbo",
            ],
            LLMProvider.GEMINI: [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
            ],
            LLMProvider.ANTHROPIC: [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ],
            LLMProvider.OLLAMA: [
                "llama3.1:8b",
                "llama3.1:70b",
                "mistral:7b",
                "codellama:13b",
                "mixtral:8x7b",
                "qwen2:7b",
            ],
            LLMProvider.GROQ: [
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ],
            LLMProvider.VLLM: [
                "meta-llama/Llama-3.1-8B-Instruct",
                "meta-llama/Llama-3.1-70B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.3",
            ],
            LLMProvider.MOCK: ["mock"],
        }
        return models.get(provider, [])


# =============================================================================
# Convenience Functions
# =============================================================================

async def get_llm() -> BaseChatModel:
    """Get the default LLM instance"""
    factory = LLMFactory()
    return await factory.get_llm()


async def get_llm_with_tools(tools: List[Any]) -> BaseChatModel:
    """Get LLM with tools bound"""
    factory = LLMFactory()
    return await factory.get_llm_with_tools(tools)


def get_supported_providers() -> Dict[str, Dict[str, Any]]:
    """Get all supported LLM providers"""
    return LLMFactory.get_supported_providers()


def get_provider_models(provider: str) -> List[str]:
    """Get models for a specific provider"""
    try:
        return LLMFactory.get_provider_models(LLMProvider(provider))
    except ValueError:
        return []


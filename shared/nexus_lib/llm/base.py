"""
Base LLM Client Interface
Abstract base class and common types for all LLM providers
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger("nexus.llm")


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class LLMConfig(BaseModel):
    """Configuration for LLM client"""
    provider: LLMProvider = Field(default=LLMProvider.MOCK)
    model: str = Field(default="gemini-2.0-flash")
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    top_p: float = Field(default=0.95, ge=0, le=1)
    top_k: int = Field(default=40, ge=1, le=100)
    
    # Safety settings
    enable_safety_filters: bool = True
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Streaming
    enable_streaming: bool = False
    
    # Cost tracking
    track_costs: bool = True
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables"""
        provider_str = os.environ.get("LLM_PROVIDER", "mock").lower()
        
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            logger.warning(f"Unknown LLM provider: {provider_str}, using mock")
            provider = LLMProvider.MOCK
        
        return cls(
            provider=provider,
            model=os.environ.get("LLM_MODEL", "gemini-2.0-flash"),
            api_key=os.environ.get("LLM_API_KEY") or os.environ.get("GOOGLE_API_KEY"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
            enable_streaming=os.environ.get("LLM_STREAMING", "false").lower() == "true",
        )


class TokenUsage(BaseModel):
    """Token usage information"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost based on typical pricing (Gemini pricing)"""
        # Gemini 2.0 Flash: $0.10 per 1M input, $0.40 per 1M output
        input_cost = (self.input_tokens / 1_000_000) * 0.10
        output_cost = (self.output_tokens / 1_000_000) * 0.40
        return input_cost + output_cost


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: Optional[str] = None
    latency_ms: float = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For function calling
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    request_id: Optional[str] = None
    cached: bool = False


class Message(BaseModel):
    """Chat message"""
    role: str  # "user", "assistant", "system"
    content: str
    name: Optional[str] = None
    
    # For function calls
    function_call: Optional[Dict[str, Any]] = None


class FunctionDefinition(BaseModel):
    """Function/Tool definition for LLM"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = Field(default_factory=list)


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the client connection"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from a prompt"""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[FunctionDefinition]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Chat with message history"""
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close client connections"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def provider_name(self) -> str:
        return self.config.provider.value


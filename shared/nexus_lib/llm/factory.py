"""
LLM Client Factory
Creates and manages LLM client instances
"""
import os
import logging
from typing import Optional, Dict

from .base import BaseLLMClient, LLMConfig, LLMProvider
from .gemini import GeminiClient
from .openai_client import OpenAIClient

logger = logging.getLogger("nexus.llm.factory")

# Global client cache
_client_cache: Dict[str, BaseLLMClient] = {}


def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """
    Create an LLM client instance
    
    Args:
        provider: LLM provider (google, openai, mock)
        model: Model name to use
        api_key: API key for the provider
        **kwargs: Additional configuration options
    
    Returns:
        Configured LLM client instance
    """
    # Build config
    config = LLMConfig.from_env()
    
    if provider:
        try:
            config.provider = LLMProvider(provider.lower())
        except ValueError:
            logger.warning(f"Unknown provider: {provider}, using default")
    
    if model:
        config.model = model
    
    if api_key:
        config.api_key = api_key
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Create appropriate client
    if config.provider == LLMProvider.GOOGLE:
        return GeminiClient(config)
    elif config.provider == LLMProvider.OPENAI:
        return OpenAIClient(config)
    else:
        # Return mock client (GeminiClient handles mock mode internally)
        config.provider = LLMProvider.MOCK
        return GeminiClient(config)


def get_default_client() -> BaseLLMClient:
    """
    Get or create the default LLM client based on environment configuration
    
    Returns:
        Default LLM client instance (cached)
    """
    global _client_cache
    
    cache_key = "default"
    
    if cache_key not in _client_cache:
        config = LLMConfig.from_env()
        client = create_llm_client(
            provider=config.provider.value,
            model=config.model,
            api_key=config.api_key,
        )
        _client_cache[cache_key] = client
        logger.info(f"Created default LLM client: {config.provider.value}/{config.model}")
    
    return _client_cache[cache_key]


async def close_all_clients():
    """Close all cached LLM clients"""
    global _client_cache
    
    for key, client in _client_cache.items():
        try:
            await client.close()
            logger.info(f"Closed LLM client: {key}")
        except Exception as e:
            logger.warning(f"Failed to close client {key}: {e}")
    
    _client_cache.clear()


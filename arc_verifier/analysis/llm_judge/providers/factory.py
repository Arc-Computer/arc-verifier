"""Factory for creating LLM providers."""

import os

from ..models import LLMProvider
from .anthropic import AnthropicProvider
from .base import BaseLLMProvider
from .openai import OpenAIProvider


def create_provider(provider_type: LLMProvider | None = None) -> BaseLLMProvider:
    """Create an LLM provider instance based on type or environment.
    
    Args:
        provider_type: Specific provider type to create, or None to use environment
        
    Returns:
        Configured LLM provider instance
        
    Raises:
        ValueError: If provider type is unsupported
    """
    # Use environment variable if no specific type provided
    if provider_type is None:
        env_provider = os.getenv("LLM_PRIMARY_PROVIDER", "anthropic")
        provider_type = LLMProvider(env_provider)

    if provider_type == LLMProvider.ANTHROPIC:
        return AnthropicProvider()
    elif provider_type == LLMProvider.OPENAI:
        return OpenAIProvider()
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")


def create_fallback_provider() -> BaseLLMProvider | None:
    """Create a fallback provider based on environment configuration.
    
    Returns:
        Fallback provider instance or None if not configured
    """
    fallback_env = os.getenv("LLM_FALLBACK_PROVIDER")
    if not fallback_env:
        return None

    try:
        fallback_type = LLMProvider(fallback_env)
        return create_provider(fallback_type)
    except ValueError:
        return None

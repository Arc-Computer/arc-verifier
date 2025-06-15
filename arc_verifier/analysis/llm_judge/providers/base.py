"""Base class for LLM providers."""

import os
from abc import ABC, abstractmethod

import httpx
from rich.console import Console

from ..models import LLMProvider


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, provider_type: LLMProvider):
        self.provider_type = provider_type
        self.console = Console()

        # Initialize HTTP client with timeout
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.client = httpx.Client(timeout=timeout)

    @abstractmethod
    def call_llm(self, prompt: str) -> str:
        """Call the LLM provider with the given prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM response as a string
            
        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name for identification."""
        pass

    @abstractmethod
    def generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response for testing/development."""
        pass

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if hasattr(self, 'client'):
            self.client.close()

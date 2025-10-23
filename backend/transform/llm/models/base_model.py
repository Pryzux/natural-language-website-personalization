"""Base class for LLM model providers"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseLLMModel(ABC):
    """Abstract base class for LLM model providers"""

    def __init__(self, api_key: str, model_version: str):
        """
        Initialize the model provider

        Args:
            api_key: API key for the provider
            model_version: Specific model version to use
        """
        self.api_key = api_key
        self.model_version = model_version

    @abstractmethod
    def generate_completion(
        self,
        system_prompt: str,
        user_message: List[Dict[str, Any]],
        temperature: float = 0.3
    ) -> str:
        """
        Generate a completion from the model

        Args:
            system_prompt: System instructions for the model
            user_message: User message content (can include text and images)
            temperature: Sampling temperature

        Returns:
            str: Raw text response from the model
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider (e.g., 'openai', 'anthropic')"""
        pass

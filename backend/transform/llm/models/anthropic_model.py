"""Anthropic model provider implementation"""

from typing import Dict, Any, List
from .base_model import BaseLLMModel


class AnthropicModel(BaseLLMModel):
    """Anthropic API implementation"""

    def __init__(self, api_key: str, model_version: str):
        super().__init__(api_key, model_version)
        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client"""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def generate_completion(
        self,
        system_prompt: str,
        user_message: List[Dict[str, Any]],
        temperature: float = 0.3
    ) -> str:
        """
        Generate completion using Anthropic API

        Args:
            system_prompt: System instructions
            user_message: User message content (text + images)
            temperature: Sampling temperature

        Returns:
            str: Raw text response
        """
        response = self.client.messages.create(
            model=self.model_version,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        return response.content[0].text

    @property
    def provider_name(self) -> str:
        return "anthropic"

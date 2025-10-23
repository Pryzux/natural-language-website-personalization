"""OpenAI model provider implementation"""

from typing import Dict, Any, List
from .base_model import BaseLLMModel


class OpenAIModel(BaseLLMModel):
    """OpenAI API implementation"""

    def __init__(self, api_key: str, model_version: str):
        super().__init__(api_key, model_version)
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_completion(
        self,
        system_prompt: str,
        user_message: List[Dict[str, Any]],
        temperature: float = 0.3
    ) -> str:
        """
        Generate completion using OpenAI API

        Args:
            system_prompt: System instructions
            user_message: User message content (text + images)
            temperature: Sampling temperature

        Returns:
            str: Raw text response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Calculate approximate message sizes for debugging
        system_chars = len(system_prompt)
        user_text_chars = sum(len(item.get("text", "")) for item in user_message if item.get("type") == "text")
        user_images = sum(1 for item in user_message if item.get("type") == "image_url")

        print(f"[OpenAI] Sending request: system={system_chars:,} chars, user_text={user_text_chars:,} chars, images={user_images}")

        response = self.client.chat.completions.create(
            model=self.model_version,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature
        )

        # Log token usage from response
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"[OpenAI] Token usage: prompt={usage.prompt_tokens:,}, completion={usage.completion_tokens:,}, total={usage.total_tokens:,}")

        return response.choices[0].message.content

    @property
    def provider_name(self) -> str:
        return "openai"

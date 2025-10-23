"""
LLM Service for generating DOM transformations.
Project-specific orchestration layer that uses model providers.
"""

import os
import time
import json
from typing import Dict, Any, List
from .models import OpenAIModel, AnthropicModel, BaseLLMModel
from .types import TransformationResponse
from api.types import TransformationRequest


class LLMService:
    """Service for generating DOM transformations using LLM providers"""

    def __init__(self, max_html: int | None = None):
        """
        Initialize LLM Service

        Args:
            max_html: Maximum HTML characters to send from extension
                     - None (default): No truncation
                     - Integer: Truncate to this length
                     - Defaults to MAX_HTML_LENGTH_FROM_EXTENSION env var if set

        Required Environment Variables:
            LLM_MODEL: "OpenAI" or "Anthropic"
            LLM_VERSION: Model version (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
            LLM_API_KEY: API key for the provider
        """
        # Get required env vars
        llm_model = os.getenv("LLM_MODEL")
        llm_version = os.getenv("LLM_VERSION")
        llm_api_key = os.getenv("LLM_API_KEY")

        if not llm_model:
            raise ValueError("LLM_MODEL environment variable must be set to 'OpenAI' or 'Anthropic'")
        if not llm_version:
            raise ValueError("LLM_VERSION environment variable must be set (e.g., 'gpt-4o', 'claude-3-5-sonnet-20241022')")
        if not llm_api_key:
            raise ValueError("LLM_API_KEY environment variable must be set")

        # Initialize the appropriate model
        self.model = self._create_model(llm_model, llm_api_key, llm_version)

        # Configure HTML truncation
        if max_html is not None:
            self.max_html = max_html
        else:
            env_val = os.getenv("MAX_HTML_LENGTH_FROM_EXTENSION")
            if env_val and env_val.lower() != "none":
                self.max_html = int(env_val)
            else:
                self.max_html = None

        max_html_display = self.max_html if self.max_html is not None else "unlimited"
        print(f"[LLM Service] Initialized with provider={self.model.provider_name}, model={self.model.model_version}, max_html_from_extension={max_html_display}")

    def _create_model(self, provider: str, api_key: str, version: str) -> BaseLLMModel:
        """
        Factory method to create the appropriate model instance

        Args:
            provider: "OpenAI" or "Anthropic"
            api_key: API key for the provider
            version: Model version string

        Returns:
            BaseLLMModel: Initialized model instance
        """
        provider_lower = provider.lower()

        if provider_lower == "openai":
            return OpenAIModel(api_key=api_key, model_version=version)
        elif provider_lower == "anthropic":
            return AnthropicModel(api_key=api_key, model_version=version)
        else:
            raise ValueError(f"LLM_MODEL must be 'OpenAI' or 'Anthropic', got: {provider}")

    def generate_transformations(self, request: TransformationRequest) -> Dict[str, Any]:
        """
        Generate DOM transformations from user prompt and page context.

        This is the main project-specific orchestration method that:
        1. Builds prompts with project context
        2. Calls the model provider
        3. Validates and parses responses
        4. Times the operation
        5. Handles errors

        Returns:
            Dict containing:
                - 'transformations': list of transformation objects with command chains
                - 'llm_messages': messages sent to LLM (for debugging)
                - 'llm_response': parsed response from LLM (for debugging)
        """
        # Load system prompt from file
        system_prompt = self._load_system_prompt()

        user_message_content = self._build_user_message(
            request.prompt,
            request.html,
            request.screenshot,
            request.url
        )

        try:
            # Time the API call
            api_start = time.time()
            print(f"[LLM Service] Calling {self.model.provider_name} API with model {self.model.model_version}...")

            # Call the model provider
            result_text = self.model.generate_completion(
                system_prompt=system_prompt,
                user_message=user_message_content,
                temperature=0.3
            )

            api_duration = time.time() - api_start
            print(f"[LLM Service] API responded in {api_duration:.2f}s")

            # Parse and validate the response
            result_dict = json.loads(result_text)
            validated = TransformationResponse(**result_dict)
            transformations_dict = validated.model_dump()

            print(f"[LLM Service] Generated {len(transformations_dict['transformations'])} transformations")

            # Build debug messages in standard format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_content}
            ]

            return {
                "transformations": transformations_dict["transformations"],
                "llm_messages": messages,
                "llm_response": transformations_dict
            }

        except json.JSONDecodeError as e:
            print(f"[LLM Service] JSON parsing error: {str(e)}")
            print(f"[LLM Service] Raw response: {result_text[:500]}...")
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")

        except Exception as e:
            print(f"[LLM Service] Error generating transformations: {str(e)}")
            print(f"[LLM Service] Error type: {type(e).__name__}")

            # Show validation errors if it's a Pydantic error
            try:
                from pydantic import ValidationError
                if isinstance(e, ValidationError):
                    print(f"[LLM Service] Validation errors: {e.errors()}")
            except ImportError:
                pass

            raise

    def _load_system_prompt(self) -> str:
        """Load system prompt from system_prompt.txt file"""
        from pathlib import Path

        # Get path to system_prompt.txt (in llm directory)
        prompt_path = Path(__file__).parent / "system_prompt.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"system_prompt.txt not found at {prompt_path}. "
                "Please create this file with your system prompt."
            )

        with open(prompt_path, 'r') as f:
            return f.read()

    def _build_user_message(
        self,
        prompt: str,
        html: str,
        screenshot_base64: str,
        url: str | None = None
    ) -> List[Dict[str, Any]]:
        
        """Build user message with HTML and screenshot"""

        # Detect Twitter and sanitize
        if url and ('twitter.com' in url or 'x.com' in url):
            from ..twitter_sanitizer import sanitize_twitter_html
            original_size = len(html)
            html = sanitize_twitter_html(html)
            sanitized_size = len(html)
            reduction = (1 - sanitized_size/original_size) * 100
            print(f"[LLM Service] Sanitized Twitter HTML: {original_size:,} → {sanitized_size:,} bytes ({reduction:.1f}% reduction)")

        content = []

        # Add text context
        context_text = f"""**User Request:**
        {prompt}

        **Page URL:**
        {url or 'Not provided'}

        **Page HTML:**
        {html if self.max_html is None else html[:self.max_html]}

       """

        content.append({"type": "text", "text": context_text})

        # Add screenshot
        if screenshot_base64.startswith("data:image"):
            screenshot_base64 = screenshot_base64.split(",", 1)[1]

        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{screenshot_base64}",
                "detail": "high"
            }
        })

        return content


# Global service instance (lazy-loaded)
_llm_service_instance = None

def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance

# For backward compatibility
llm_service = None  # Will be lazily initialized on first access

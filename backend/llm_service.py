"""
LLM Service Module

Handles communication with OpenAI API to generate DOM transformations
from natural language prompts + HTML + screenshot context.
"""

import os
import json
from typing import List, Dict, Any, Optional
import base64

from openai import OpenAI
from pydantic import BaseModel

from actions import get_action_definitions, get_action_types, validate_action_type


# OpenAI client (initialized lazily)
_client = None


def get_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        _client = OpenAI(api_key=api_key)
    return _client


class Transformation(BaseModel):
    """Single transformation to apply to the DOM"""
    selector: str
    action: str
    params: Dict[str, Any] = {}


class TransformationResponse(BaseModel):
    """Response containing all transformations"""
    transformations: List[Transformation]


class LLMService:
    """Service for generating DOM transformations using LLM"""

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize LLM service.

        Args:
            model: OpenAI model to use (default: gpt-4o for vision support)
        """
        self.model = model
        self.action_types = get_action_types()
        self.action_definitions = get_action_definitions()

    def generate_transformations(self,prompt: str,html: str,screenshot_base64: str,url: Optional[str] = None) -> Dict[str, Any]:

        """
        Generate DOM transformations from user prompt and page context.

        Args:
            prompt: User's natural language request
            html: Full HTML of the page
            screenshot_base64: Base64-encoded screenshot (required)
            url: Page URL for context (optional)

        Returns:
            Dictionary with 'transformations' key containing list of transformation objects

        Raises:
            Exception: If LLM call fails or returns invalid response
        """
        
        system_prompt = self._build_system_prompt()
        user_message_content = self._build_user_message(prompt, html, screenshot_base64, url)

        try:
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_content}
            ]

            # Call OpenAI API with JSON mode
            client = get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent output
            )

            # Extract and validate transformations
            result_text = response.choices[0].message.content
            transformations_dict = json.loads(result_text)

            # Validate action types
            for t in transformations_dict["transformations"]:
                if not validate_action_type(t["action"]):
                    raise ValueError(f"Invalid action type: {t['action']}")

            return transformations_dict

        except Exception as e:
            print(f"[LLM Service] Error generating transformations: {str(e)}")
            raise

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt that defines the LLM's role and constraints.

        Returns:
            System prompt string
        """
        actions_json = json.dumps(self.action_definitions, indent=2)

        return f"""You are a web page personalization assistant that outputs JSON.

Your task is to analyze the HTML, screenshot, and user prompt, then generate structured JSON describing CSS selector-based transformations that will modify the page according to the user's intent.

You will ALWAYS receive both the page HTML and a screenshot for visual context.

**Output Format:**
You MUST return a JSON object with this exact structure:
{{
  "transformations": [
    {{
      "selector": "body",
      "action": "color",
      "params": {{"background-color": "green"}}
    }}
  ]
}}

**Available Actions:**
{actions_json}

**Rules:**
1. Output ONLY valid JSON - no explanations, no markdown code blocks, just raw JSON
2. Each transformation must have:
   - selector: A valid CSS selector (be specific but generalizable)
   - action: One of {self.action_types}
   - params: An object with CSS property key-value pairs (follow param_examples above)

3. Use concise and specific selectors that will work across page reloads
4. Prefer class-based or attribute-based selectors over nth-child when possible
5. Do NOT include scripts, event handlers, or JavaScript execution
6. Only safe DOM/style changes are allowed

**Selector Best Practices:**
- Use `.classname` for repeated elements
- Use `#id` for unique elements
- Use `[attribute="value"]` for semantic targeting
- Use `tag.class` for specificity
- Combine with commas for multiple targets: `h1, h2, h3`
- Use descendant selectors when needed: `.container .item`

**Safety:**
- Never modify or remove authentication elements
- Never hide critical UI (close buttons, navigation out of context)
- Never inject executable code

Remember: Output must be valid JSON only, starting with {{ and ending with }}"""

    def _build_user_message(
        self,
        prompt: str,
        html: str,
        screenshot_base64: str,
        url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Build the user message with multimodal content (text + required image).

        Args:
            prompt: User's request
            html: Page HTML
            screenshot_base64: Required screenshot (base64-encoded)
            url: Optional page URL

        Returns:
            List of message content parts
        """
        # Start with text content
        content = []

        # Add text context
        context_text = f"""**User Request:**
{prompt}

**Page URL:**
{url or 'Not provided'}

**Page HTML:**
```html
{html[:50000]}
```

Generate JSON transformations to fulfill the user's request."""

        content.append({
            "type": "text",
            "text": context_text
        })

        # Add screenshot (always required)
        # Remove data URL prefix if present
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


# Singleton instance
llm_service = LLMService()

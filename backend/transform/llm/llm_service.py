
import os
from typing import List, Dict, Any
from openai import OpenAI
import time
import json
from .types import TransformationResponse
from api.types import TransformationRequest


# OpenAI client (initialized lazily)
_client = None

MAX_HTML = 70000


def get_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        _client = OpenAI(api_key=api_key)
    return _client


class LLMService:
    """Service for generating DOM transformations using LLM with Structured Outputs"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model


    def generate_transformations(self, request: TransformationRequest) -> Dict[str, Any]:
        """
        Generate DOM transformations from user prompt and page context.

        Returns:
                - 'transformations': list of transformation objects with command chains
                - 'llm_messages': messages sent to LLM (for debugging)
                - 'llm_response': parsed response from LLM (for debugging)
        """

        system_prompt = self._build_system_prompt()
        user_message_content = self._build_user_message(request.prompt, request.html, request.screenshot, request.url)

        try:
            # Build messages
            messages = [ {"role": "system", "content": system_prompt}, {"role": "user", "content": user_message_content} ]

            client = get_client()

            api_start = time.time()
            print(f"[LLM Service] Calling OpenAI API (using regular JSON mode for speed)...")

            # Use regular JSON mode instead of Structured Outputs - faster!
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3
            )

            print(f"[LLM Service] API responded in {time.time() - api_start:.2f}s")

            # Parse and validate with Pydantic
           
            result_text = response.choices[0].message.content
            result_dict = json.loads(result_text)

            # Validate using Pydantic
            validated = TransformationResponse(**result_dict)
            transformations_dict = validated.model_dump()

            print(f"[LLM Service] Generated {len(transformations_dict['transformations'])} transformations")

            # Return transformations along with debugging info
            return {
                "transformations": transformations_dict["transformations"],
                "llm_messages": messages,
                "llm_response": transformations_dict
            }

        except Exception as e:
            print(f"[LLM Service] Error generating transformations: {str(e)}")
            print(f"[LLM Service] Error type: {type(e).__name__}")

            # If it's a validation error, show more details
            if hasattr(e, 'errors'):
                print(f"[LLM Service] Validation errors: {e.errors()}")

            raise


    def _build_system_prompt(self) -> str:

        return """You are a website personalizer assistant. Analyze the HTML and screenshot, then generate commands to transform the page based on the user's request.

**Output JSON Format:**
{
  "transformations": [
    {
      "description": "what this transformation does",
      "commands": [
        {"selector": "...", "method": "css", "cssProps": {"property": "value"}},
        {"selector": "...", "method": "relocate", "target": "...", "position": "append"}
      ]
    }
  ]
}

**Available Methods:**

**relocate** - Move element to a new position in the DOM
  - selector: element to move
  - target: destination selector
  - position: "append" | "prepend" | "before" | "after"
  - Example: {"selector": ".widget", "method": "relocate", "target": "body", "position": "append"}

**css** - Apply CSS styling
  - selector: elements to style
  - cssProps: {property: value}
  - Example: {"selector": "body", "method": "css", "cssProps": {"background": "blue", "color": "white"}}

**addClass** / **removeClass** / **toggleClass** - Manage CSS classes
  - selector: elements to modify
  - content: class name
  - Example: {"selector": ".card", "method": "addClass", "content": "dark-mode"}

**text** / **html** - Change element content
  - selector: elements to modify
  - content: new content
  - Example: {"selector": "h1", "method": "text", "content": "Welcome"}

**append** / **prepend** / **before** / **after** - Insert HTML
  - selector: reference element
  - content: HTML to insert
  - Example: {"selector": "body", "method": "prepend", "content": "<div class='banner'>New!</div>"}

**remove** - Delete element from DOM
  - selector: elements to remove
  - Example: {"selector": ".ad", "method": "remove"}

**hide** / **show** - Toggle visibility
  - selector: elements to hide/show
  - Example: {"selector": ".popup", "method": "hide"}

**wrap** / **unwrap** - Wrap element in container or remove wrapper
  - selector: element to wrap/unwrap
  - content: wrapper HTML (for wrap)
  - Example: {"selector": "img", "method": "wrap", "content": "<figure class='image-wrapper'></figure>"}

**attr** / **removeAttr** - Modify attributes
  - selector: elements to modify
  - cssProps: {attribute: value} (for attr)
  - content: attribute name (for removeAttr)
  - Example: {"selector": "a", "method": "attr", "cssProps": {"target": "_blank"}}

**clone** - Duplicate element
  - selector: element to clone
  - Example: {"selector": ".widget", "method": "clone"}"""


    def _build_user_message(self, prompt: str, html: str, screenshot_base64: str, url: str | None = None) -> List[Dict[str, Any]]:
        """Build user message with text context and screenshot. """
        
        content = []

        # Add text context
        context_text = f"""**User Request:**
        {prompt}

        **Page URL:**
        {url or 'Not provided'}

        **Page HTML:**
        {html[:MAX_HTML]}

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


llm_service = LLMService()

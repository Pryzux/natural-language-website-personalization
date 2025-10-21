"""
Request Saving Module

Handles saving request data, screenshots, and HTML to disk for debugging and logging.
"""

import os
import json
import base64
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from datetime import datetime


class RequestSaver:
    """Handles saving request data to disk"""

    def __init__(self, base_path: str = "requests"):
        """ Initialize RequestSaver """
        self.base_path = os.path.join(os.path.dirname(__file__), base_path)

    def _get_next_request_dir(self, domain: str) -> tuple[str, int]:
        """Find the next available request directory for a domain."""
        
        base_dir = os.path.join(self.base_path, domain)
        os.makedirs(base_dir, exist_ok=True)

        request_num = 1
        while os.path.exists(os.path.join(base_dir, f"request_{request_num}")):
            request_num += 1

        request_dir = os.path.join(base_dir, f"request_{request_num}")
        os.makedirs(request_dir, exist_ok=True)

        return request_dir, request_num

    def _save_screenshot(self, screenshot_dir: str, screenshot_base64: str) -> str:
        """
        Save screenshot to disk.

        Args:
            screenshot_dir: Directory to save screenshot in
            screenshot_base64: Base64-encoded screenshot

        Returns:
            Path to saved screenshot
        """
        # Remove data:image/png;base64, prefix if present
        screenshot_data = screenshot_base64
        if ',' in screenshot_data:
            screenshot_data = screenshot_data.split(',', 1)[1]

        screenshot_path = os.path.join(screenshot_dir, "screenshot.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot_data))

        print(f"[RequestSaver] Saved screenshot to: {screenshot_path}")
        return screenshot_path

    def save_transformation_request(
        self,
        prompt: str,
        html: str,
        screenshot: str,
        transformations: List[Dict[str, Any]],
        url: Optional[str] = None,
        llm_messages: Optional[List[Dict[str, Any]]] = None,
        llm_response: Optional[Dict[str, Any]] = None,
        extension_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a transformation request with all its data in a structured format.

        Args:
            prompt: User's natural language prompt
            html: Page HTML
            screenshot: Base64-encoded screenshot
            transformations: Generated transformations
            url: Page URL (optional)
            llm_messages: Messages sent to LLM (optional)
            llm_response: Raw response from LLM (optional)
            extension_response: Response sent to extension (optional)

        Returns:
            Dictionary with save information
        """
        domain = urlparse(url).hostname if url else "unknown"
        request_dir, request_num = self._get_next_request_dir(domain)
        timestamp = datetime.now().isoformat()

        # Create subdirectories
        prompt_dir = os.path.join(request_dir, "prompt")
        output_dir = os.path.join(request_dir, "output")
        os.makedirs(prompt_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # ========== PROMPT DIRECTORY ==========
        # Save LLM input messages
        if llm_messages:
            message_path = os.path.join(prompt_dir, "message.json")
            with open(message_path, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "url": url,
                    "messages": llm_messages
                }, f, indent=2)
            print(f"[RequestSaver] Saved LLM messages to: {message_path}")

        # Save HTML in prompt directory
        html_path = os.path.join(prompt_dir, "page.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[RequestSaver] Saved HTML to: {html_path}")

        # Save screenshot in prompt directory
        screenshot_path = self._save_screenshot(prompt_dir, screenshot)

        # ========== OUTPUT DIRECTORY ==========
        # Save raw LLM response
        if llm_response:
            llm_response_path = os.path.join(output_dir, "llm_response.json")
            with open(llm_response_path, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "response": llm_response
                }, f, indent=2)
            print(f"[RequestSaver] Saved LLM response to: {llm_response_path}")

        # Save extension response
        if extension_response:
            extension_response_path = os.path.join(output_dir, "extension_response.json")
            with open(extension_response_path, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "response": extension_response
                }, f, indent=2)
            print(f"[RequestSaver] Saved extension response to: {extension_response_path}")

        # ========== METADATA (root of request directory) ==========
        # Save summary metadata
        selectors = [t["selector"] for t in transformations]
        metadata_path = os.path.join(request_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "request_number": request_num,
                "url": url,
                "prompt": prompt,
                "html_length": len(html),
                "screenshot_length": len(screenshot),
                "transformation_count": len(transformations),
                "selectors": selectors
            }, f, indent=2)
        print(f"[RequestSaver] Saved metadata to: {metadata_path}")

        return {
            "request_dir": request_dir,
            "request_num": request_num,
            "prompt_dir": prompt_dir,
            "output_dir": output_dir,
            "screenshot_path": screenshot_path,
            "html_path": html_path,
            "metadata_path": metadata_path
        }

# Create default RequestSaver instance
request_saver = RequestSaver()

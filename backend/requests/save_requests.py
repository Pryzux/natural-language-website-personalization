"""
Request Saving Module

Saves request data in structured format:
- raw_received/: Original data from extension
- llm/: LLM interaction data with placeholders
"""

import os
import json
import base64
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from datetime import datetime


class RequestSaver:
    """Handles saving request data to disk"""

    def __init__(self, base_path: str = None):
        """Initialize RequestSaver

        base_path defaults to the directory containing this file (backend/requests/)
        """
        if base_path is None:
            self.base_path = os.path.dirname(__file__)
        else:
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

    def save_raw_request(
        self,
        prompt: str,
        html: str,
        screenshot: str,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save raw request data immediately when received from extension.
        Call this BEFORE making LLM request for debugging.

        Args:
            prompt: User's natural language prompt
            html: Original page HTML from extension
            screenshot: Base64-encoded screenshot
            url: Page URL (optional)

        Returns:
            Dictionary with save information including request_dir for later use
        """
        domain = urlparse(url).hostname if url else "unknown"
        request_dir, request_num = self._get_next_request_dir(domain)
        timestamp = datetime.now().isoformat()

        # Create raw_received directory
        raw_dir = os.path.join(request_dir, "raw_received")
        os.makedirs(raw_dir, exist_ok=True)

        # Save user prompt
        prompt_path = os.path.join(raw_dir, "prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"[RequestSaver] Saved prompt to: {prompt_path}")

        # Save original HTML
        html_path = os.path.join(raw_dir, "page.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[RequestSaver] Saved HTML to: {html_path}")

        # Save screenshot as PNG
        screenshot_path = os.path.join(raw_dir, "screenshot.png")
        screenshot_data = screenshot
        if ',' in screenshot_data:
            screenshot_data = screenshot_data.split(',', 1)[1]
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot_data))
        print(f"[RequestSaver] Saved screenshot to: {screenshot_path}")

        # Save metadata
        metadata_path = os.path.join(request_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "request_number": request_num,
                "url": url,
                "html_length": len(html)
            }, f, indent=2)

        print(f"[RequestSaver] Saved raw request data for request #{request_num}")

        return {
            "request_dir": request_dir,
            "request_num": request_num,
            "raw_dir": raw_dir,
            "domain": domain
        }

    def save_llm_results(
        self,
        request_dir: str,
        transformations: List[Dict[str, Any]],
        llm_messages: Optional[List[Dict[str, Any]]] = None,
        llm_response: Optional[Dict[str, Any]] = None,
        extension_response: Optional[Dict[str, Any]] = None,
        was_sanitized: bool = False,
        sanitized_html: Optional[str] = None,
        original_html_length: int = 0
    ) -> Dict[str, Any]:
        """
        Save LLM interaction results after processing.
        Call this AFTER LLM request completes.

        Args:
            request_dir: Request directory from save_raw_request()
            transformations: Generated transformations
            llm_messages: Messages sent to LLM (optional)
            llm_response: Raw response from LLM (optional)
            extension_response: Response sent to extension (optional)
            was_sanitized: Whether HTML was sanitized
            sanitized_html: Sanitized HTML if was_sanitized is True
            original_html_length: Length of original HTML for comparison

        Returns:
            Dictionary with save information
        """
        timestamp = datetime.now().isoformat()

        # Create llm directory
        llm_dir = os.path.join(request_dir, "llm")
        os.makedirs(llm_dir, exist_ok=True)

        # Save LLM prompt with placeholders
        if llm_messages:
            messages_with_placeholders = self._create_messages_with_placeholders(llm_messages)

            prompt_json_path = os.path.join(llm_dir, "prompt.json")
            with open(prompt_json_path, "w") as f:
                json.dump(messages_with_placeholders, f, indent=2)
            print(f"[RequestSaver] Saved LLM prompt (with placeholders) to: {prompt_json_path}")

        # Save LLM result
        result_data = {
            "timestamp": timestamp,
            "was_sanitized": was_sanitized,
            "llm_response": llm_response,
            "extension_response": extension_response,
            "metadata": {
                "transformation_count": len(transformations),
                "html_length_original": original_html_length,
                "html_length_sent_to_llm": len(sanitized_html) if was_sanitized and sanitized_html else original_html_length
            }
        }

        result_path = os.path.join(llm_dir, "result.json")
        with open(result_path, "w") as f:
            json.dump(result_data, f, indent=2)
        print(f"[RequestSaver] Saved LLM result to: {result_path}")

        # Save sanitized HTML (only if it was sanitized)
        if was_sanitized and sanitized_html:
            sanitized_path = os.path.join(llm_dir, "sanitized_page.html")
            with open(sanitized_path, "w", encoding="utf-8") as f:
                f.write(sanitized_html)
            print(f"[RequestSaver] Saved sanitized HTML to: {sanitized_path}")

        print(f"[RequestSaver] Saved LLM results")

        return {
            "request_dir": request_dir,
            "llm_dir": llm_dir
        }

    def _create_messages_with_placeholders(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create messages with placeholders instead of full HTML/screenshot.

        Args:
            messages: Original LLM messages

        Returns:
            Messages with [HTML in page.html] and [Screenshot in screenshot.png] placeholders
        """
        result = []

        for msg in messages:
            new_msg = {"role": msg["role"]}

            if msg["role"] == "system":
                new_msg["content"] = msg["content"]
            elif msg["role"] == "user":
                content = msg.get("content", [])

                if isinstance(content, str):
                    new_msg["content"] = content
                elif isinstance(content, list):
                    new_content = []
                    for item in content:
                        if item.get("type") == "text":
                            # Replace HTML in text with placeholder
                            text = item["text"]
                            # Find and replace HTML section
                            if "**Page HTML:**" in text:
                                parts = text.split("**Page HTML:**")
                                if len(parts) == 2:
                                    before_html = parts[0]
                                    # Find end of HTML section (next ** or end)
                                    after_html_idx = parts[1].find("**")
                                    if after_html_idx > 0:
                                        after_html = parts[1][after_html_idx:]
                                        text = f"{before_html}**Page HTML:**\n[HTML in page.html]\n\n{after_html}"
                                    else:
                                        text = f"{before_html}**Page HTML:**\n[HTML in page.html]"

                            new_content.append({"type": "text", "text": text})
                        elif item.get("type") == "image_url":
                            # Replace image with placeholder
                            new_content.append({
                                "type": "image",
                                "image": "[Screenshot in screenshot.png]"
                            })
                        else:
                            new_content.append(item)

                    new_msg["content"] = new_content
            else:
                new_msg["content"] = msg.get("content", "")

            result.append(new_msg)

        return result


# Create default RequestSaver instance
request_saver = RequestSaver()

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

    def _save_screenshot(self, request_dir: str, screenshot_base64: str) -> str:
        """
        Save screenshot to disk.

        Args:
            request_dir: Directory to save screenshot in
            screenshot_base64: Base64-encoded screenshot

        Returns:
            Path to saved screenshot
        """
        # Remove data:image/png;base64, prefix if present
        screenshot_data = screenshot_base64
        if ',' in screenshot_data:
            screenshot_data = screenshot_data.split(',', 1)[1]

        screenshot_path = os.path.join(request_dir, "screenshot.png")
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
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a transformation request with all its data.

        Args:
            prompt: User's natural language prompt
            html: Page HTML
            screenshot: Base64-encoded screenshot
            transformations: Generated transformations
            url: Page URL (optional)

        Returns:
            Dictionary with save information
        """
        domain = urlparse(url).hostname if url else "unknown"
        request_dir, request_num = self._get_next_request_dir(domain)
        timestamp = datetime.now().isoformat()

        # Save screenshot
        screenshot_path = self._save_screenshot(request_dir, screenshot)

        # Extract selectors
        selectors = [t["selector"] for t in transformations]

        # Save complete request data
        request_data_path = os.path.join(request_dir, "request_data.json")
        with open(request_data_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "request_number": request_num,
                "url": url,
                "prompt": prompt,
                "html_length": len(html),
                "screenshot_length": len(screenshot),
                "transformations": transformations,
                "selectors": selectors,
                "transformation_count": len(transformations)
            }, f, indent=2)
        print(f"[RequestSaver] Saved request data to: {request_data_path}")

        # Save HTML separately (can be large)
        html_path = os.path.join(request_dir, "page.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[RequestSaver] Saved HTML to: {html_path}")

        return {
            "request_dir": request_dir,
            "request_num": request_num,
            "screenshot_path": screenshot_path,
            "request_data_path": request_data_path,
            "html_path": html_path
        }

# Create default RequestSaver instance
request_saver = RequestSaver()

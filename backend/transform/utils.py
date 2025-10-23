"""Utility functions for transformation processing"""

import re


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.

    Removes:
    - <script> tags and contents
    - on* event attributes (onclick, onload, etc.)
    - javascript: protocol in href/src
    - data: URLs (potential XSS vector)

    This is a basic sanitizer - for production, consider using a library like bleach.
    """
    if not html:
        return html

    # Remove <script> tags and contents
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)

    # Remove on* event attributes
    html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', html, flags=re.IGNORECASE)

    # Remove javascript: protocol
    html = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'src\s*=\s*["\']javascript:[^"\']*["\']', '', html, flags=re.IGNORECASE)

    # Remove data: URLs (can be used for XSS)
    html = re.sub(r'href\s*=\s*["\']data:[^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'src\s*=\s*["\']data:[^"\']*["\']', '', html, flags=re.IGNORECASE)

    return html

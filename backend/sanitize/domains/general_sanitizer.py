"""
General sanitizer for domains without specific sanitization rules.
Uses lxml.html.clean.Cleaner for security-focused HTML sanitization.
"""

from lxml.html.clean import Cleaner
from shared.api import TransformationRequest


# Configure lxml Cleaner for safe HTML
# Removes dangerous elements but preserves structure and attributes for LLM
cleaner = Cleaner(
    # Security: Remove dangerous elements
    scripts=True,              # Remove <script> tags
    javascript=True,           # Remove javascript: URLs
    comments=True,             # Remove HTML comments
    style=False,               # Keep <style> tags (LLM might need them)
    inline_style=False,        # Keep style="" attributes (LLM needs for visibility checks)
    links=False,               # Keep <link> tags
    meta=True,               
    page_structure=False,      # Keep <html>, <head>, <body>
    processing_instructions=True,  # Remove <?xml?> etc
    embedded=False,            # Keep <embed> (just metadata)
    frames=False,              # Keep <frame> (just structure)
    forms=False,               # Keep <form> (LLM might target forms)
    annoying_tags=True,       
    remove_tags=None,          # Don't remove any tags completely
    kill_tags=['script'],      # Kill <script> completely (content + tag)
    remove_unknown_tags=False, # Keep custom tags
    safe_attrs_only=True,     # Keep all attributes (LLM needs aria-*, data-*, etc)
    add_nofollow=False,        # Don't modify links
    host_whitelist=(),
    whitelist_tags=None
)


def sanitize(request: TransformationRequest) -> TransformationRequest:
    """
    General sanitization using lxml.html.clean.Cleaner.

    Removes:
    - <script> tags and javascript: URLs
    - HTML comments
    - Processing instructions

    Preserves:
    - All structural HTML
    - All attributes (aria-*, data-*, class, id, etc.)
    - style="" attributes (for LLM visibility checks)
    - <style> tags (LLM might read CSS)
    - Forms and inputs

    Args:
        request: The transformation request

    Returns:
        Request with sanitized HTML
    """
    try:
        # Clean the HTML
        sanitized_html = cleaner.clean_html(request.html)

        print(f"[GeneralSanitizer] Cleaned HTML: {len(request.html)} → {len(sanitized_html)} bytes")

        return TransformationRequest(
            prompt=request.prompt,
            html=sanitized_html,
            screenshot=request.screenshot,
            url=request.url
        )
    except Exception as e:
        # If cleaning fails, return original request
        print(f"[GeneralSanitizer] Error cleaning HTML: {e}, returning original")
        return request

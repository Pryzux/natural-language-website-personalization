"""
Sanitize incoming extension requests.
Automatically routes to domain-specific sanitizers based on URL.
"""

import importlib
from api.types import TransformationRequest
from .sanitization_types import DOMAIN_SANITIZERS


def sanitize_request(request: TransformationRequest) -> TransformationRequest:
    """
    Sanitize incoming request based on domain.

    Automatically detects domain from request.url and routes to the
    appropriate sanitizer module. Falls back to general_sanitizer if
    no domain-specific sanitizer exists.

    Args:
        request: The transformation request from the extension

    Returns:
        TransformationRequest with sanitized HTML

    Example:
        # For twitter.com URL → uses twitter_sanitizer
        # For facebook.com URL → uses facebook_sanitizer (if exists)
        # For unknown domain → uses general_sanitizer
    """
    url = request.url

    # No URL provided - use general sanitizer
    if not url:
        return _get_sanitizer("general_sanitizer").sanitize(request)

    # Check if URL matches any registered domain
    for domain, sanitizer_module in DOMAIN_SANITIZERS.items():
        if domain in url:
            print(f"[Sanitize] Detected domain: {domain}, using {sanitizer_module}")
            return _get_sanitizer(sanitizer_module).sanitize(request)

    # No specific sanitizer found - use general
    print(f"[Sanitize] No specific sanitizer for URL, using general_sanitizer")
    return _get_sanitizer("general_sanitizer").sanitize(request)


def _get_sanitizer(module_name: str):
    """
    Dynamically import and return a sanitizer module.

    Args:
        module_name: Name of the sanitizer module (without .py)

    Returns:
        The sanitizer module

    Raises:
        ImportError: If sanitizer module doesn't exist
    """
    try:
        return importlib.import_module(f"sanitize.domains.{module_name}")
    except ImportError as e:
        raise ImportError(
            f"Sanitizer module '{module_name}' not found. "
            f"Create sanitize/domains/{module_name}.py with a sanitize() function."
        ) from e

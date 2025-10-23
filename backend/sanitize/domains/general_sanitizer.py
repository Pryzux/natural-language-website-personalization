"""
General sanitizer for domains without specific sanitization rules.
Currently returns the request unchanged.
"""

from api.types import TransformationRequest


def sanitize(request: TransformationRequest) -> TransformationRequest:
    """
    General sanitization - returns request unchanged.

    Args:
        request: The transformation request

    Returns:
        The request unchanged
    """
    return request

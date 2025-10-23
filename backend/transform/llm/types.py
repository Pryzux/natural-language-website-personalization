from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
import re


# Safe jQuery methods (CSP-compatible, no event handlers with inline functions)
SAFE_JQUERY_METHODS = [
    # Traversal / Selection
    "find", "eq", "filter", "not", "parent", "children", "closest", "siblings",
    "next", "prev", "first", "last", "slice", "has", "add",

    # DOM Manipulation
    "append", "prepend", "before", "after", "appendTo", "prependTo", "remove",
    "empty", "detach", "replaceWith", "wrap", "unwrap", "clone",

    # Attributes & Properties
    "attr", "removeAttr", "prop", "removeProp", "val",

    # Classes
    "addClass", "removeClass", "toggleClass", "hasClass",

    # CSS & Style
    "css", "height", "width", "innerHeight", "innerWidth", "outerHeight", "outerWidth",

    # Content
    "text", "html",

    # Visibility
    "show", "hide", "toggle",

    # Data & Utility
    "data", "removeData"
]


class Command(BaseModel):
    """A single jQuery method call in a command chain"""
    method: str = Field(..., description="jQuery method name")
    args: List[Union[str, int, float, bool, Dict[str, Any], None]] = Field(
        default_factory=list,
        description="Arguments to pass to the method"
    )

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Ensure only safe jQuery methods are used"""
        if v not in SAFE_JQUERY_METHODS:
            raise ValueError(f"Method '{v}' is not in the safe subset. Allowed: {SAFE_JQUERY_METHODS}")
        return v

    @field_validator('args')
    @classmethod
    def sanitize_html_args(cls, v: List[Any], info) -> List[Any]:
        """Sanitize HTML content in arguments for methods that insert HTML"""
        method = info.data.get('method')

        # Methods that accept HTML content
        html_methods = ['html', 'append', 'prepend', 'before', 'after',
                       'appendTo', 'prependTo', 'replaceWith', 'wrap']

        if method not in html_methods:
            return v

        # Sanitize string arguments
        sanitized = []
        for arg in v:
            if isinstance(arg, str):
                sanitized.append(sanitize_html(arg))
            else:
                sanitized.append(arg)

        return sanitized


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


class Transformation(BaseModel):
    """A jQuery transformation with selector and command chain"""
    selector: str = Field(..., description="jQuery selector to find target elements")
    commands: List[Command] = Field(..., min_length=1, description="jQuery methods to execute in sequence")

    @field_validator('selector')
    @classmethod
    def validate_selector(cls, v: str) -> str:
        """Basic validation that selector is not empty"""
        if not v or not v.strip():
            raise ValueError("Selector cannot be empty")
        return v.strip()


class TransformationResponse(BaseModel):
    """LLM response containing jQuery transformations"""
    transformations: List[Transformation] = Field(..., min_length=1)

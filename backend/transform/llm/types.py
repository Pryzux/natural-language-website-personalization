from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Command(BaseModel):
    """
    A single jQuery command to execute on the DOM.

    For 'css' method, use cssProps field.
    For 'relocate' method, use target and position fields.
    For other methods, use content field.
    """
    selector: str = Field(
        ...,
        description="CSS selector to target elements"
    )
    method: str = Field(
        ...,
        description="jQuery method name: css, addClass, removeClass, text, html, append, prepend, remove, hide, show, relocate, etc."
    )

    # Separate field for CSS properties - much clearer for the LLM
    cssProps: Optional[Dict[str, str]] = Field(
        default=None,
        description="CSS properties as key-value pairs. Use this for 'css' method only.",
        examples=[
            {"background": "linear-gradient(to bottom, #87CEEB 0%, #F4A460 100%)", "color": "#2C3E50", "padding": "20px"},
            {"color": "#006994", "font-size": "24px", "text-shadow": "2px 2px 4px rgba(255,255,255,0.5)"}
        ]
    )

    # Simple field for other arguments
    content: Optional[str] = Field(
        default=None,
        description="Content for methods like text, html, append, prepend, addClass, removeClass",
        examples=["<h1>Welcome to the Beach</h1>", "beach-theme", "Hello World"]
    )

    # Fields for relocate method
    target: Optional[str] = Field(
        default=None,
        description="Target selector for 'relocate' method. The destination where element will be moved.",
        examples=["body", ".main-content", "#sidebar"]
    )
    position: Optional[str] = Field(
        default=None,
        description="Position relative to target for 'relocate' method: 'append', 'prepend', 'before', 'after'",
        examples=["append", "prepend", "before", "after"]
    )


class Transformation(BaseModel):
    """
    A transformation consisting of one or more chained commands.

    Commands are executed in sequence to achieve a specific goal.

    Example:
        {
            "description": "Hide ads and add custom message",
            "commands": [
                {"selector": ".ad", "method": "remove", "args": []},
                {"selector": "body", "method": "prepend", "args": ["<div>Clean!</div>"]}
            ]
        }
    """
    description: str = Field(
        ...,
        description="Brief human-readable description of what this transformation does"
    )
    commands: List[Command] = Field(
        ...,
        min_length=1,
        description="List of commands to execute in sequence to achieve the transformation"
    )


class TransformationResponse(BaseModel):
    """
    The complete response containing all transformations to apply to the page.

    For complex thematic requests (e.g., "beach theme"), this should contain
    multiple transformations, each handling a different aspect (background, buttons, etc.)
    """
    transformations: List[Transformation] = Field(
        ...,
        min_length=1,
        description="List of transformations to apply to the page"
    )

"""
Action Definitions Module

Defines all available action types that can be applied to DOM elements.
Each action type has a name, description, and example parameters.
"""

from typing import List, Dict, Any
from enum import Enum


class ActionType(str, Enum):
    """Enumeration of valid action types"""
    COLOR = "color"
    TEXT = "text"
    LAYOUT = "layout"
    VISIBILITY = "visibility"
    STYLE = "style"


class ActionDefinition:
    """Definition of a single action type"""

    def __init__(
        self,
        action_type: ActionType,
        description: str,
        param_examples: Dict[str, Any],
        notes: str = ""
    ):
        self.action_type = action_type
        self.description = description
        self.param_examples = param_examples
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "action": self.action_type.value,
            "description": self.description,
            "param_examples": self.param_examples,
            "notes": self.notes
        }


# Define all available actions
ACTION_DEFINITIONS = [
    ActionDefinition(
        action_type=ActionType.COLOR,
        description="Modify color properties (background, text, border)",
        param_examples={
            "background-color": "#E0F7FA",
            "color": "rgb(255, 0, 0)",
            "border-color": "blue"
        },
        notes="Use standard CSS color values (hex, rgb, named colors)"
    ),

    ActionDefinition(
        action_type=ActionType.TEXT,
        description="Modify text content of elements",
        param_examples={
            "replace": "New text content"
        },
        notes="Replaces entire text content of matched elements"
    ),

    ActionDefinition(
        action_type=ActionType.LAYOUT,
        description="Modify layout properties (positioning, sizing, spacing)",
        param_examples={
            "margin": "10px",
            "padding": "20px",
            "width": "100%",
            "height": "200px",
            "display": "flex",
            "flex-direction": "column"
        },
        notes="Use standard CSS layout properties"
    ),

    ActionDefinition(
        action_type=ActionType.VISIBILITY,
        description="Control element visibility",
        param_examples={
            "display": "none",  # Hide element
            "visibility": "hidden",  # Hide but keep space
            "opacity": "0.5"  # Semi-transparent
        },
        notes="Use 'display: none' to completely hide elements"
    ),

    ActionDefinition(
        action_type=ActionType.STYLE,
        description="Apply any other CSS styles not covered by specific actions",
        param_examples={
            "font-size": "18px",
            "font-weight": "bold",
            "border-radius": "10px",
            "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            "transition": "all 0.3s ease"
        },
        notes="Catch-all for any CSS property"
    )
]


def get_action_definitions() -> List[Dict[str, Any]]:
    """
    Get all action definitions as a list of dictionaries.
    Used to inform the LLM about available actions.

    Returns:
        List of action definition dictionaries
    """
    return [action.to_dict() for action in ACTION_DEFINITIONS]


def get_action_types() -> List[str]:
    """
    Get list of all valid action type strings.

    Returns:
        List of action type strings
    """
    return [action_type.value for action_type in ActionType]


def validate_action_type(action: str) -> bool:
    """
    Check if an action type is valid.

    Args:
        action: Action type string to validate

    Returns:
        True if valid, False otherwise
    """
    return action in get_action_types()

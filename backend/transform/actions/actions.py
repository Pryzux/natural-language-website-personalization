"""Actions Module"""

from typing import List, Dict, Any
from .definitions import ACTION_DEFINITIONS
from .types import Action


class Actions:

    def __init__(self, action_definitions: List[Action]):
        """Initialize Actions"""
        self.definitions = action_definitions
        self.types = [defn.action for defn in action_definitions]

    def get_action_definitions(self) -> List[Dict[str, Any]]:
        """Get all action definitions as a list of dictionaries. Used to inform the LLM about available actions."""
        return [action.model_dump() for action in self.definitions]

    def get_action_types(self) -> List[str]:
        """Get list of all valid action type strings."""
        return self.types

    def validate_action_type(self, action: str) -> bool:
        """Validate that a string is a valid action type"""
        return action in self.types


# Create default Actions instance with predefined definitions
actions = Actions(ACTION_DEFINITIONS)

from pydantic import BaseModel, Field
from typing import Dict, Any


class Action(BaseModel):
    """Pydantic model for an action definition"""

    action: str = Field(..., min_length=1, description="Action type identifier")
    description: str = Field(..., min_length=1, description="Description of what the action does")
    param_examples: Dict[str, Any] = Field(..., description="Example parameters for the action")

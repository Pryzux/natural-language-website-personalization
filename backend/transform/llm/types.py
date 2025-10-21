"""
LLM Types

Type definitions for LLM service requests and responses.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class Transformation(BaseModel):
    """Single transformation to apply to the DOM"""
    selector: str
    action: str
    params: Dict[str, Any] = {}


class TransformationResponse(BaseModel):
    """Response containing all transformations"""
    transformations: List[Transformation]

from typing import Optional
from pydantic import BaseModel, Field


class TransformationRequest(BaseModel):
    """Request to generate transformations"""
    prompt: str = Field(..., description="User's natural language request")
    html: str = Field(..., description="Full HTML of the page")
    screenshot: str = Field(..., description="Base64-encoded screenshot")
    url: Optional[str] = Field(None, description="Page URL for context")

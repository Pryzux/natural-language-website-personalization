"""
FastAPI backend for AI Website Customizer Chrome Extension
"""

import os
from typing import Optional
import json
from urllib.parse import urlparse
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from llm_service import llm_service
from actions import get_action_definitions

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Website Customizer API",
    description="Backend service for generating DOM transformations from natural language",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class TransformationRequest(BaseModel):
    """Request to generate transformations"""
    prompt: str = Field(..., description="User's natural language request")
    html: str = Field(..., description="Full HTML of the page")
    screenshot: str = Field(..., description="Base64-encoded screenshot (required)")
    url: Optional[str] = Field(None, description="Page URL for context")



@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AI Website Customizer API",
        "version": "0.1.0"
    }


@app.get("/actions")
async def get_actions():
    """
    Get available action definitions.
    Useful for debugging and understanding what actions are supported.
    """
    return {
        "actions": get_action_definitions()
    }


@app.post("/generate_transformations")
async def generate_transformations(request: TransformationRequest):
    """
    Generate jQuery selector-based transformations from natural language prompt.

    Takes HTML, optional screenshot, and user prompt, then uses LLM to generate
    structured transformations that can be applied by the extension.

    Args:
        request: TransformationRequest containing prompt, html, optional screenshot/url

    Returns:
        JSON with 'transformations' array containing selector/action/params objects

    Example Response:
        {
            "transformations": [
                {
                    "selector": "body",
                    "action": "color",
                    "params": {"background-color": "green"}
                }
            ],
            "summary": "Applied background color change",
            "selectors": ["body"]
        }
    """
    try:
        print(f"[Generate Transformations] Processing request")
        print(f"[Generate Transformations] Prompt: {request.prompt}")
        print(f"[Generate Transformations] URL: {request.url}")
        print(f"[Generate Transformations] HTML length: {len(request.html)} chars")
        print(f"[Generate Transformations] Screenshot length: {len(request.screenshot)} chars")

        # Validate screenshot is provided
        if not request.screenshot:
            raise HTTPException(
                status_code=400,
                detail="Screenshot is required for generating transformations"
            )

        # Setup request logging directory
        domain = urlparse(request.url).hostname if request.url else "unknown"
        base_dir = os.path.join(os.path.dirname(__file__), "requests", domain)
        os.makedirs(base_dir, exist_ok=True)

        # Find next available request number
        request_num = 1
        while os.path.exists(os.path.join(base_dir, f"request_{request_num}")):
            request_num += 1

        # Create request directory
        request_dir = os.path.join(base_dir, f"request_{request_num}")
        os.makedirs(request_dir, exist_ok=True)

        timestamp = datetime.now().isoformat()

        # Call LLM service
        result = llm_service.generate_transformations(
            prompt=request.prompt,
            html=request.html,
            screenshot_base64=request.screenshot,
            url=request.url
        )

        # Extract selectors and create summary
        transformations = result.get("transformations", [])
        selectors = [t["selector"] for t in transformations]

        print(f"[Generate Transformations] Generated {len(transformations)} transformations")

        # Save screenshot (always required)
        import base64
        # Remove data:image/png;base64, prefix if present
        screenshot_data = request.screenshot
        if ',' in screenshot_data:
            screenshot_data = screenshot_data.split(',', 1)[1]

        screenshot_path = os.path.join(request_dir, "screenshot.png")
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot_data))
        print(f"[Generate Transformations] Saved screenshot to: {screenshot_path}")

        # Save complete request data
        request_data_path = os.path.join(request_dir, "request_data.json")
        with open(request_data_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "request_number": request_num,
                "url": request.url,
                "prompt": request.prompt,
                "html_length": len(request.html),
                "screenshot_length": len(request.screenshot),
                "transformations": transformations,
                "selectors": selectors,
                "transformation_count": len(transformations)
            }, f, indent=2)
        print(f"[Generate Transformations] Saved request data to: {request_data_path}")

        # Save HTML separately (can be large)
        html_path = os.path.join(request_dir, "page.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(request.html)
        print(f"[Generate Transformations] Saved HTML to: {html_path}")

        return {
            "transformations": transformations,
            "summary": f"Generated {len(transformations)} transformations for: {request.prompt}",
            "selectors": selectors
        }

    except Exception as e:
        print(f"[Generate Transformations] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate transformations: {str(e)}"
        )


@app.post("/save_page_data")
async def save_page_data(request: dict):
    """
    Save raw DOM data to disk: requests/{domain}/request_{N}/raw_dom.json

    This is for debugging and testing purposes only.
    The main transformation endpoint is /generate_transformations.
    """
    try:
        page_url = request.get("page_url", "")
        dom_data = request.get("dom_data", {})
        screenshot = request.get("screenshot")

        if not page_url or not dom_data:
            raise HTTPException(status_code=400, detail="Missing page_url or dom_data")

        # Parse domain from URL
        domain = urlparse(page_url).hostname or "unknown"

        # Create directory structure: requests/{domain}/
        base_dir = os.path.join(os.path.dirname(__file__), "requests", domain)
        os.makedirs(base_dir, exist_ok=True)

        # Find next available request number
        request_num = 1
        while os.path.exists(os.path.join(base_dir, f"request_{request_num}")):
            request_num += 1

        # Create request directory
        request_dir = os.path.join(base_dir, f"request_{request_num}")
        os.makedirs(request_dir, exist_ok=True)

        timestamp = datetime.now().isoformat()

        # Save screenshot if provided
        if screenshot:
            import base64
            # Remove data:image/png;base64, prefix if present
            screenshot_data = screenshot
            if ',' in screenshot_data:
                screenshot_data = screenshot_data.split(',', 1)[1]

            screenshot_path = os.path.join(request_dir, "screenshot.png")
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
            print(f"[Save Page Data] Saved screenshot to: {screenshot_path}")

        # Save raw DOM data
        raw_dom_path = os.path.join(request_dir, "raw_dom.json")
        with open(raw_dom_path, "w") as f:
            json.dump({
                "page_url": page_url,
                "timestamp": timestamp,
                "screenshot_provided": bool(screenshot),
                "dom_data": dom_data
            }, f, indent=2)

        print(f"[Save Page Data] Saved raw DOM to: {raw_dom_path}")

        return {
            "success": True,
            "path": raw_dom_path
        }

    except Exception as e:
        print(f"[Save Page Data] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

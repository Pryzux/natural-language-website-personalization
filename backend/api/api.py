import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from transform.llm.llm_service import get_llm_service
from requests.save_requests import request_saver
from sanitize import sanitize_request
from .types import TransformationRequest

# Load environment variables
load_dotenv()

# Check if request saving is enabled
SAVE_REQUESTS = os.getenv("SAVE_REQUESTS", "false").lower() == "true"

# Initialize
app = FastAPI(
    title="AI Website Customizer API",
    description="Backend service for generating DOM transformations from natural language",
    version="0.1.0"
)

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.post("/generate_transformations")
async def generate_transformations(request: TransformationRequest):
    """
    Generate CSP-safe DOM transformations from natural language prompt.

    Takes HTML, screenshot, and user prompt, then uses LLM to generate
    structured action chains that can be applied by the extension.

    Returns: JSON with 'transformations' array containing action chains

    Example Response:
        {
            "transformations": [
                {
                    "description": "Apply green background",
                    "actions": [
                        {
                            "method": "css",
                            "selector": "body",
                            "cssProps": {"background-color": "green"}
                        }
                    ]
                }
            ],
            "summary": "Generated 1 transformations for: make background green",
            "selectors": ["body"]
        }
    """
    try:

        # Validate screenshot is provided
        if not request.screenshot:
            raise HTTPException(status_code=400, detail="Screenshot is required for generating transformations")

        # Sanitize request based on domain
        sanitized_request = sanitize_request(request)

        # Call LLM service with sanitized request
        llm_service = get_llm_service()
        result = llm_service.generate_transformations(sanitized_request)

        # Extract transformations and debugging info
        transformations = result.get("transformations", [])
        llm_messages = result.get("llm_messages")
        llm_response = result.get("llm_response")
        print(f"[Generate Transformations] Generated {len(transformations)} transformations")

        # Extract all unique selectors from all actions in all transformations
        selectors = []
        for t in transformations:
            for action in t.get("actions", []):
                selector = action.get("selector")
                if selector and selector not in selectors:
                    selectors.append(selector)

        # Build response for extension
        extension_response = {
            "transformations": transformations,
            "summary": f"Generated {len(transformations)} transformations for: {request.prompt}",
            "selectors": selectors
        }

        # Save request data with all debugging information (if enabled)
        if SAVE_REQUESTS:
            request_saver.save_transformation_request(
                prompt=request.prompt,
                html=request.html,
                screenshot=request.screenshot,
                transformations=transformations,
                url=request.url,
                llm_messages=llm_messages,
                llm_response=llm_response,
                extension_response=extension_response
            )

        return extension_response

    except Exception as e:
        print(f"[Generate Transformations] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate transformations: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

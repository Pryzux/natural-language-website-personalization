import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from transform.llm.llm_service import get_llm_service
from requests.save_requests import request_saver
from sanitize import sanitize_request
from shared.api import TransformationRequest

# Load environment variables
load_dotenv()

# Check if request saving is enabled
SAVE_REQUESTS = os.getenv("SAVE_REQUESTS", "false").lower() == "true"

# Check if sanitization is disabled
DISABLE_SANITIZATION = os.getenv("DISABLE_SANITIZATION", "false").lower() == "true"

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
        print(f"\n{'='*80}")
        print(f"[API] NEW TRANSFORMATION REQUEST")
        print(f"{'='*80}")
        print(f"[API] Prompt: {request.prompt}")
        print(f"[API] URL: {request.url}")
        print(f"[API] Incoming HTML size: {len(request.html):,} chars ({len(request.html.encode('utf-8')):,} bytes)")
        print(f"[API] Screenshot size: {len(request.screenshot):,} chars")

        # Validate screenshot is provided
        if not request.screenshot:
            raise HTTPException(status_code=400, detail="Screenshot is required for generating transformations")

        # Save raw request immediately (if enabled) - useful for debugging crashes
        request_info = None
        if SAVE_REQUESTS:
            request_info = request_saver.save_raw_request(
                prompt=request.prompt,
                html=request.html,
                screenshot=request.screenshot,
                url=request.url
            )

        # Sanitize request based on domain (unless disabled)
        print(f"\n[API] SANITIZATION PHASE:")
        if DISABLE_SANITIZATION:
            print(f"[API] ⚠️  SANITIZATION DISABLED - Sending raw HTML to LLM")
            sanitized_request = request
            was_sanitized = False
        else:
            sanitized_request = sanitize_request(request)
            was_sanitized = sanitized_request.html != request.html

            if was_sanitized:
                reduction_pct = (1 - len(sanitized_request.html)/len(request.html)) * 100
                print(f"[API] Sanitized: {len(request.html):,} → {len(sanitized_request.html):,} chars ({reduction_pct:.1f}% reduction)")
            else:
                print(f"[API] No sanitization applied (HTML unchanged)")

        # Call LLM service with sanitized request
        print(f"\n[API] LLM SERVICE PHASE:")
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

        # Save LLM results (if enabled)
        if SAVE_REQUESTS and request_info:
            request_saver.save_llm_results(
                request_dir=request_info["request_dir"],
                transformations=transformations,
                llm_messages=llm_messages,
                llm_response=llm_response,
                extension_response=extension_response,
                was_sanitized=was_sanitized,
                sanitized_html=sanitized_request.html if was_sanitized else None,
                original_html_length=len(request.html)
            )

        print(f"\n[API] REQUEST COMPLETE")
        print(f"[API] Transformations generated: {len(transformations)}")
        print(f"[API] Unique selectors: {len(selectors)}")
        print(f"{'='*80}\n")

        return extension_response

    except Exception as e:
        print(f"[Generate Transformations] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate transformations: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

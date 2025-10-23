#!/usr/bin/env python3
"""
Print transformations from any saved request in copy-paste ready format.
Usage: python print_requests.py <domain> <request_number>
"""

import json
import sys
from pathlib import Path

def print_request(domain: str, request_num: int):
    """Print transformations from a request in copy-paste format."""

    # Build path to the LLM response
    # Script is in /backend/requests/, so go to parent to find domains
    request_dir = Path(__file__).parent / domain / f"request_{request_num}"
    llm_response_path = request_dir / "output" / "llm_response.json"
    metadata_path = request_dir / "metadata.json"

    if not llm_response_path.exists():
        print(f"❌ Request {request_num} not found at {llm_response_path}")
        list_available(domain)
        return None

    # Load the response
    with open(llm_response_path) as f:
        data = json.load(f)

    # Load metadata if available
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)

    # Extract transformations
    transformations = data.get("response", {}).get("transformations", [])

    if not transformations:
        print(f"⚠️  No transformations found in request {request_num}")
        return None

    # Pretty print the transformations
    output = json.dumps(transformations, indent=2)

    print(f"✅ Request {request_num} - {domain}")
    if metadata.get("prompt"):
        print(f"📝 Prompt: {metadata['prompt']}")
    print(f"🔢 Transformations: {len(transformations)}")
    print("\n" + "="*60)
    print(output)
    print("="*60)
    print("\n📋 Copy the JSON above and paste it into the extension's 'Test Transformations' section")

    return transformations

def list_available(domain: str):
    """List all available requests for a domain."""
    requests_dir = Path(__file__).parent / domain

    if not requests_dir.exists():
        print(f"\n❌ No requests directory found for domain: {domain}")
        return

    # Find all request directories
    request_dirs = sorted([d for d in requests_dir.iterdir() if d.is_dir() and d.name.startswith("request_")])

    if not request_dirs:
        print(f"\n📭 No requests found for domain: {domain}")
        return

    print(f"\n📁 Available requests for {domain}:")
    for req_dir in request_dirs:
        request_num = req_dir.name.replace("request_", "")
        metadata_path = req_dir / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
                prompt = metadata.get("prompt", "No prompt")
                # Truncate long prompts
                if len(prompt) > 60:
                    prompt = prompt[:60] + "..."
                print(f"  {request_num}: {prompt}")
        else:
            print(f"  {request_num}: (no metadata)")

def list_all_domains():
    """List all available domains."""
    requests_dir = Path(__file__).parent

    if not requests_dir.exists():
        print("❌ No requests directory found")
        return

    # Filter out special directories
    domains = sorted([
        d.name for d in requests_dir.iterdir()
        if d.is_dir() and not d.name.startswith('_') and not d.name.startswith('.')
    ])

    if not domains:
        print("📭 No domains found")
        return

    print("\n🌐 Available domains:")
    for domain in domains:
        domain_dir = requests_dir / domain
        request_count = len([d for d in domain_dir.iterdir() if d.is_dir() and d.name.startswith("request_")])
        print(f"  {domain}: {request_count} requests")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python print_requests.py <domain> <request_number>")
        print("   or: python print_requests.py list <domain>")
        print("   or: python print_requests.py domains")
        print("\nExamples:")
        print("  python print_requests.py x.com 26")
        print("  python print_requests.py list x.com")
        print("  python print_requests.py domains")
        list_all_domains()
        sys.exit(1)

    if sys.argv[1] == "domains":
        list_all_domains()
    elif sys.argv[1] == "list":
        if len(sys.argv) < 3:
            print("❌ Error: domain required")
            print("Usage: python print_requests.py list <domain>")
            print("Example: python print_requests.py list x.com")
            sys.exit(1)
        domain = sys.argv[2]
        list_available(domain)
    else:
        if len(sys.argv) < 3:
            print("❌ Error: both domain and request number required")
            print("Usage: python print_requests.py <domain> <request_number>")
            print("Example: python print_requests.py x.com 26")
            sys.exit(1)
        domain = sys.argv[1]
        request_num = int(sys.argv[2])
        print_request(domain, request_num)

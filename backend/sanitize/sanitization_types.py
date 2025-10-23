"""
Sanitization type definitions and domain mappings.
Maps domains to their sanitizer modules.
"""

from typing import Dict

# Map domains to their sanitizer module names
# Key: domain pattern to match in URL
# Value: sanitizer module name (without .py extension)
DOMAIN_SANITIZERS: Dict[str, str] = {
    "twitter.com": "twitter_sanitizer",
    "x.com": "twitter_sanitizer",
    # Add more domain mappings here:
    # "facebook.com": "facebook_sanitizer",
    # "reddit.com": "reddit_sanitizer",
}

"""
Domain-specific sanitizers

Each sanitizer module must implement:
    def sanitize(request: TransformationRequest) -> TransformationRequest

Sanitizers are automatically routed based on sanitization_types.DOMAIN_SANITIZERS mapping.
"""
